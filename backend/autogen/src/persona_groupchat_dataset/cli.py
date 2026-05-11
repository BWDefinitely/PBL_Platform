from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .loader import load_experiment_config, load_personas
from .runner import (
    append_dialogue_checkpoint,
    create_dataset_skeleton,
    create_run_artifacts,
    iter_dialogues,
    resolve_model_config_list,
    write_dataset_state,
    write_run_metadata,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate AutoGen group-chat datasets from persona.json."
    )
    parser.add_argument(
        "--persona-file",
        default="persona.json",
        help="Path to the persona definition JSON file.",
    )
    parser.add_argument(
        "--experiment-file",
        default="configs/experiment_groups.json",
        help="Path to the experiment group configuration JSON file.",
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
        help="Validate persona and experiment config without calling the model.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    persona_path = resolve_project_path(args.persona_file)
    experiment_path = resolve_project_path(args.experiment_file)
    output_dir = resolve_output_dir(args.output_dir)

    personas = load_personas(persona_path)
    experiment = load_experiment_config(experiment_path)
    only_groups = parse_only_groups(args.only_groups)

    validate_persona_references(personas, experiment, only_groups)

    if args.dry_run:
        print_dry_run_summary(personas, experiment, only_groups)
        return 0

    config_list = resolve_model_config_list(
        config_list_file=str(resolve_project_path(args.config_list_file)) if args.config_list_file else None,
        model=args.model,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
    )
    artifacts = create_run_artifacts(output_dir, experiment.output_prefix)
    setup_logging(artifacts.log_path)
    write_run_metadata(artifacts, experiment, config_list, only_groups)

    dataset = create_dataset_skeleton(
        experiment=experiment,
        config_list=config_list,
        only_groups=only_groups,
        persona_source=persona_path,
        artifacts=artifacts,
    )
    write_dataset_state(dataset, artifacts.state_path)

    try:
        for dialogue in iter_dialogues(
            personas=personas,
            experiment=experiment,
            config_list=config_list,
            cache_seed=args.cache_seed,
            only_groups=only_groups,
        ):
            dataset["dialogues"].append(dialogue)
            append_dialogue_checkpoint(artifacts, dialogue)
            write_dataset_state(dataset, artifacts.state_path)
            logging.getLogger(__name__).info(
                "Checkpoint saved for %s at %s",
                dialogue["dialogue_id"],
                artifacts.state_path,
            )
    except KeyboardInterrupt:
        dataset["status"] = "interrupted"
        dataset["ended_at"] = current_timestamp()
        write_dataset_state(dataset, artifacts.state_path)
        print(f"Run interrupted. Partial results saved to: {artifacts.state_path.resolve()}")
        print(f"Per-dialogue checkpoints: {artifacts.dialogue_jsonl_path.resolve()}")
        return 130
    except Exception as exc:
        dataset["status"] = "failed"
        dataset["ended_at"] = current_timestamp()
        dataset["error"] = f"{type(exc).__name__}: {exc}"
        write_dataset_state(dataset, artifacts.state_path)
        logging.getLogger(__name__).exception("Run failed. Partial results saved.")
        raise

    dataset["status"] = "completed"
    dataset["ended_at"] = current_timestamp()
    output_path = write_dataset_state(dataset, artifacts.final_dataset_path)
    write_dataset_state(dataset, artifacts.state_path)
    print(f"Dataset written to: {output_path.resolve()}")
    print(f"Run log written to: {artifacts.log_path.resolve()}")
    print(f"Per-dialogue checkpoints: {artifacts.dialogue_jsonl_path.resolve()}")
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


def validate_persona_references(personas, experiment, only_groups: set[str] | None) -> None:
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


def print_dry_run_summary(personas, experiment, only_groups: set[str] | None) -> None:
    selected_groups = [
        group for group in experiment.groups if not only_groups or group.group_id in only_groups
    ]
    print(f"Personas loaded: {len(personas)}")
    print(f"Experiment: {experiment.dataset_name}")
    print(f"Selected groups: {len(selected_groups)}")
    for group in selected_groups:
        member_names = [personas[role_id].name for role_id in group.member_role_ids]
        task_preview = (group.task or experiment.default_task)[:60].replace("\n", " ")
        print(
            f"- {group.group_id}: {len(member_names)} members, repeats={group.repeats}, "
            f"members={member_names}, task='{task_preview}...'"
        )
