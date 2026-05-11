from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .loader import load_experiment_config, load_personas, load_scenarios
from .runner import (
    append_behavior_events,
    append_behavior_timeline,
    append_conversation_timeline,
    append_project_checkpoint,
    append_project_progress_behavior_timeline,
    append_project_progress_timeline,
    append_project_progress_snapshot,
    create_dataset_skeleton,
    create_run_artifacts,
    iter_projects,
    resolve_model_config_bundle,
    select_groups,
    write_quality_reports,
    write_dataset_state,
    write_run_metadata,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate project-timeline student dialogue datasets from persona.json."
    )
    parser.add_argument(
        "--persona-file",
        default="persona.json",
        help="Path to the persona definition JSON file.",
    )
    parser.add_argument(
        "--scenario-file",
        default="configs/scenarios_timeline.json",
        help="Path to the timeline scenario JSON file.",
    )
    parser.add_argument(
        "--experiment-file",
        default="configs/experiment_groups_timeline.json",
        help="Path to the timeline experiment group configuration JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for generated dataset JSON files.",
    )
    parser.add_argument(
        "--config-list-file",
        help="AutoGen config_list JSON file containing model credentials.",
    )
    parser.add_argument("--model", help="Model name used when not providing --config-list-file.")
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the API key when using --model.",
    )
    parser.add_argument(
        "--base-url",
        help="Optional OpenAI-compatible base_url when using --model.",
    )
    parser.add_argument(
        "--cache-seed",
        type=int,
        default=42,
        help="Base cache seed used by AutoGen for reproducibility.",
    )
    parser.add_argument(
        "--only-groups",
        help="Comma-separated group IDs to run. By default all groups run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate persona, scenario, and experiment config without calling the model.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run only the short timeline_smoke_test group.",
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        help="Stop after generating this many project instances.",
    )
    parser.add_argument(
        "--estimate-cost",
        action="store_true",
        help="Print a rough run-size estimate without calling the model.",
    )
    return parser


def main() -> int:
    configure_console_encoding()
    args = build_parser().parse_args()

    persona_path = resolve_project_path(args.persona_file)
    scenario_path = resolve_project_path(args.scenario_file)
    experiment_path = resolve_project_path(args.experiment_file)
    output_dir = resolve_output_dir(args.output_dir)

    personas = load_personas(persona_path)
    scenarios = load_scenarios(scenario_path)
    experiment = load_experiment_config(experiment_path)
    only_groups = parse_only_groups(args.only_groups)
    if args.smoke_test:
        only_groups = {"timeline_smoke_test"}

    validate_references(personas, scenarios, experiment, only_groups)

    if args.dry_run or args.estimate_cost:
        print_dry_run_summary(personas, scenarios, experiment, only_groups)
        if args.estimate_cost:
            print_run_size_estimate(experiment, only_groups, args.max_projects)
        return 0

    config_bundle = resolve_model_config_bundle(
        config_list_file=str(resolve_project_path(args.config_list_file)) if args.config_list_file else None,
        model=args.model,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
    )
    artifacts = create_run_artifacts(output_dir, experiment.output_prefix)
    setup_logging(artifacts.log_path)
    write_run_metadata(artifacts, experiment, config_bundle, only_groups)

    dataset = create_dataset_skeleton(
        experiment=experiment,
        config_bundle=config_bundle,
        only_groups=only_groups,
        persona_source=persona_path,
        scenario_source=scenario_path,
        artifacts=artifacts,
    )
    write_dataset_state(dataset, artifacts.state_path)
    partial_projects: dict[str, dict[str, object]] = {}

    def persist_project_progress(project_snapshot: dict[str, object]) -> None:
        partial_projects[str(project_snapshot["project_id"])] = project_snapshot
        dataset["projects"] = [partial_projects[key] for key in sorted(partial_projects)]
        append_project_progress_snapshot(artifacts, project_snapshot)
        if experiment.generation_settings.incremental_conversation_timeline:
            append_project_progress_timeline(artifacts, project_snapshot)
            append_project_progress_behavior_timeline(artifacts, project_snapshot)
            latest_session = project_snapshot.get("sessions", [])[-1]
            append_behavior_events(
                artifacts,
                latest_session.get("events", []) + latest_session.get("between_session_events_after", []),
            )
        write_dataset_state(dataset, artifacts.state_path)
        if experiment.generation_settings.enable_quality_diagnostics:
            write_quality_reports(artifacts, dataset)

    try:
        completed_project_count = 0
        for project_record in iter_projects(
            personas=personas,
            scenarios=scenarios,
            experiment=experiment,
            dialogue_config_list=config_bundle.dialogue,
            controller_config_list=config_bundle.controller,
            cache_seed=args.cache_seed,
            only_groups=only_groups,
            progress_callback=persist_project_progress,
        ):
            partial_projects[project_record["project_id"]] = project_record
            dataset["projects"] = [partial_projects[key] for key in sorted(partial_projects)]
            append_project_checkpoint(artifacts, project_record)
            if not experiment.generation_settings.incremental_conversation_timeline:
                append_conversation_timeline(artifacts, project_record)
                append_behavior_timeline(artifacts, project_record)
                append_behavior_events(artifacts, project_record.get("events", []))
            write_dataset_state(dataset, artifacts.state_path)
            if experiment.generation_settings.enable_quality_diagnostics:
                write_quality_reports(artifacts, dataset)
            logging.getLogger(__name__).info(
                "Checkpoint saved for %s at %s",
                project_record["project_id"],
                artifacts.state_path,
            )
            completed_project_count += 1
            if args.max_projects and completed_project_count >= args.max_projects:
                break
    except KeyboardInterrupt:
        dataset["status"] = "interrupted"
        dataset["ended_at"] = current_timestamp()
        write_dataset_state(dataset, artifacts.state_path)
        if experiment.generation_settings.enable_quality_diagnostics:
            write_quality_reports(artifacts, dataset)
        print(f"Run interrupted. Partial results saved to: {artifacts.state_path.resolve()}")
        print(f"Session checkpoints: {artifacts.project_checkpoint_path.resolve()}")
        print(f"Conversation timeline: {artifacts.conversation_timeline_path.resolve()}")
        print(f"Behavior timeline: {artifacts.behavior_timeline_path.resolve()}")
        print(f"Behavior event stream: {artifacts.behavior_events_path.resolve()}")
        return 130
    except Exception as exc:
        dataset["status"] = "failed"
        dataset["ended_at"] = current_timestamp()
        dataset["error"] = f"{type(exc).__name__}: {exc}"
        write_dataset_state(dataset, artifacts.state_path)
        if experiment.generation_settings.enable_quality_diagnostics:
            write_quality_reports(artifacts, dataset)
        logging.getLogger(__name__).exception("Run failed. Partial results saved.")
        raise

    dataset["status"] = "completed"
    dataset["ended_at"] = current_timestamp()
    output_path = write_dataset_state(dataset, artifacts.final_dataset_path)
    write_dataset_state(dataset, artifacts.state_path)
    if experiment.generation_settings.enable_quality_diagnostics:
        write_quality_reports(artifacts, dataset)
    print(f"Dataset written to: {output_path.resolve()}")
    print(f"Run log written to: {artifacts.log_path.resolve()}")
    print(f"Completed projects: {artifacts.project_jsonl_path.resolve()}")
    print(f"Session checkpoints: {artifacts.project_checkpoint_path.resolve()}")
    print(f"Conversation timeline written to: {artifacts.conversation_timeline_path.resolve()}")
    print(f"Behavior timeline written to: {artifacts.behavior_timeline_path.resolve()}")
    print(f"Behavior event stream written to: {artifacts.behavior_events_path.resolve()}")
    if experiment.generation_settings.enable_quality_diagnostics:
        print(f"Quality report written to: {artifacts.quality_report_md_path.resolve()}")
    return 0


def parse_only_groups(raw_value: str | None) -> set[str] | None:
    if not raw_value:
        return None
    return {item.strip() for item in raw_value.split(",") if item.strip()}


def resolve_project_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def resolve_output_dir(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def setup_logging(log_path: Path) -> None:
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def current_timestamp() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def validate_references(personas, scenarios, experiment, only_groups: set[str] | None) -> None:
    if only_groups:
        known_group_ids = {group.group_id for group in experiment.groups}
        unknown_group_ids = sorted(only_groups - known_group_ids)
        if unknown_group_ids:
            raise ValueError(f"Unknown group IDs in --only-groups: {unknown_group_ids}")

    for group in experiment.groups:
        if only_groups and group.group_id not in only_groups:
            continue
        missing_role_ids = [role_id for role_id in group.member_role_ids if role_id not in personas]
        if missing_role_ids:
            raise ValueError(
                f"Group '{group.group_id}' references undefined role IDs: {missing_role_ids}"
            )
        if group.scenario_id and group.scenario_id not in scenarios:
            raise ValueError(
                f"Group '{group.group_id}' references undefined scenario_id: {group.scenario_id}"
            )


def print_dry_run_summary(personas, scenarios, experiment, only_groups: set[str] | None) -> None:
    selected_groups = select_groups(experiment, only_groups)
    print(f"Personas loaded: {len(personas)}")
    print(f"Scenarios loaded: {len(scenarios)}")
    print(f"Experiment: {experiment.dataset_name}")
    print(f"Selected groups: {len(selected_groups)}")
    for group in selected_groups:
        member_names = [personas[role_id].name for role_id in group.member_role_ids]
        print(
            f"- {group.group_id}: {len(member_names)} members, repeats={group.repeats}, "
            f"sessions={group.session_count_range}, scenario={group.scenario_id or 'legacy_task'}, "
            f"members={member_names}"
        )


def print_run_size_estimate(experiment, only_groups: set[str] | None, max_projects: int | None) -> None:
    selected_groups = select_groups(experiment, only_groups)
    project_count = sum(group.repeats for group in selected_groups)
    if max_projects is not None:
        project_count = min(project_count, max_projects)

    min_sessions = 0
    max_sessions = 0
    counted_projects = 0
    for group in selected_groups:
        for _ in range(group.repeats):
            if max_projects is not None and counted_projects >= max_projects:
                break
            min_sessions += group.session_count_range[0]
            max_sessions += group.session_count_range[1]
            counted_projects += 1

    print("Run-size estimate:")
    print(f"- projects: {project_count}")
    print(f"- sessions: {min_sessions}-{max_sessions}")
    speaker_policies = sorted(
        {
            group.speaker_selection_method
            or experiment.default_groupchat.get("speaker_selection_method", "auto")
            for group in selected_groups
        }
    )
    if speaker_policies == ["urgency_queue"]:
        print(
            f"- rough model calls: at least {min_sessions * 3}; urgency_queue avoids the extra LLM speaker-selection call per turn"
        )
    else:
        print(f"- rough model calls: at least {min_sessions * 3}, often higher because AutoGen selects speakers per turn")
    print(f"- speaker policies: {speaker_policies}")
    print("- note: this is not a billing estimate; it only estimates run size.")
