from __future__ import annotations

import json
import logging
import os
import random
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator

from .models import ExperimentDefinition, GroupDefinition, PersonaRole, ScenarioDefinition
from .turn_taking import build_urgency_speaker_selector, merge_urgency_settings

LOGGER = logging.getLogger(__name__)
INTERNAL_SESSION_END_TOKEN = "[[SESSION_END]]"
ROLE_NICKNAME_MAP = {
    "initiator_proposer": "Ivy",
    "evaluator_critic": "Leo",
    "implementer_worker": "Max",
    "information_seeker": "Nina",
    "gatekeeper_expediter": "Owen",
    "harmonizer": "Mia",
    "encourager": "Sunny",
    "free_rider": "Ethan",
    "lone_wolf": "Victor",
    "dominator": "Derek",
    "blocker": "Bruno",
}
PRESENCE_LIVE_MODES = {"active", "passive", "late"}
PROJECT_END_SIGNALS = {"continue", "completed", "stalled", "abandoned", "forced_submission"}
SESSION_OUTCOMES = {
    "progress_made_and_pause",
    "temporary_stalemate",
    "conflict_breakup",
    "task_completed_for_now",
}
EVENT_PATTERNS: dict[str, list[str]] = {
    "upload_document": [
        "上传",
        "发到群里",
        "共享文档",
        "传到网盘",
        "放到共享盘",
        "发群里",
        "链接发",
        "上传作业",
        "上传会议记录",
    ],
    "share_result": [
        "结果发",
        "把结果发",
        "数据出来了",
        "结果出来了",
        "分享结果",
        "发你们看",
        "同步结果",
        "同步一下结果",
    ],
    "submit_deliverable": [
        "提交",
        "交上去",
        "交作业",
        "提交作业",
        "提交最终版",
        "定稿",
        "已经交了",
        "提交完成",
    ],
    "present_defense": [
        "答辩",
        "展示",
        "路演",
        "presentation",
        "present",
        "汇报一下",
        "进行汇报",
        "开始汇报",
        "上台汇报",
    ],
}
FRONTEND_VISIBLE_EVENT_TYPES = {
    "upload_document",
    "share_result",
    "submit_deliverable",
    "present_defense",
}


@dataclass(frozen=True)
class RunArtifacts:
    run_dir: Path
    project_jsonl_path: Path
    project_checkpoint_path: Path
    conversation_timeline_path: Path
    behavior_timeline_path: Path
    behavior_events_path: Path
    quality_report_json_path: Path
    quality_report_md_path: Path
    state_path: Path
    final_dataset_path: Path
    metadata_path: Path
    log_path: Path


@dataclass(frozen=True)
class ModelConfigBundle:
    dialogue: list[dict[str, Any]]
    controller: list[dict[str, Any]]


def resolve_model_config_list(
    config_list_file: str | None,
    model: str | None,
    api_key_env: str,
    base_url: str | None,
) -> list[dict[str, Any]]:
    if config_list_file:
        config_path = Path(config_list_file)
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list) or not payload:
            raise ValueError(f"{config_path} must contain a non-empty JSON list.")
        return payload

    if not model:
        raise ValueError(
            "Provide either --config-list-file or --model together with an API key environment variable."
        )

    api_key = os.getenv(api_key_env)
    if not api_key:
        raise ValueError(f"Environment variable '{api_key_env}' is not set.")

    config: dict[str, Any] = {
        "model": model,
        "api_key": api_key,
    }
    if base_url:
        config["base_url"] = base_url
    return [config]


def resolve_model_config_bundle(
    config_list_file: str | None,
    model: str | None,
    api_key_env: str,
    base_url: str | None,
) -> ModelConfigBundle:
    if config_list_file:
        config_path = Path(config_list_file)
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
        return parse_model_config_bundle(payload, source=config_path)

    config_list = resolve_model_config_list(
        config_list_file=None,
        model=model,
        api_key_env=api_key_env,
        base_url=base_url,
    )
    return ModelConfigBundle(dialogue=config_list, controller=deepcopy(config_list))


def parse_model_config_bundle(payload: Any, source: str | Path) -> ModelConfigBundle:
    if isinstance(payload, list):
        validate_model_config_list(payload, source=source)
        return ModelConfigBundle(dialogue=payload, controller=deepcopy(payload))

    if not isinstance(payload, dict):
        raise ValueError(f"{source} must contain either a JSON list or a JSON object.")

    dialogue_config = (
        payload.get("dialogue")
        or payload.get("dialogue_config_list")
        or payload.get("default")
        or payload.get("config_list")
    )
    controller_config = (
        payload.get("controller")
        or payload.get("controller_config_list")
        or dialogue_config
    )
    validate_model_config_list(dialogue_config, source=f"{source}:dialogue")
    validate_model_config_list(controller_config, source=f"{source}:controller")
    return ModelConfigBundle(dialogue=dialogue_config, controller=controller_config)


def validate_model_config_list(config_list: Any, source: str | Path) -> None:
    if not isinstance(config_list, list) or not config_list:
        raise ValueError(f"{source} must contain a non-empty JSON list.")
    if not all(isinstance(item, dict) for item in config_list):
        raise ValueError(f"{source} must contain only JSON objects.")


def summarize_model_config(config_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for item in config_list:
        summary.append(
            {
                "model": item.get("model"),
                "base_url": item.get("base_url"),
                "api_type": item.get("api_type"),
                "api_version": item.get("api_version"),
            }
        )
    return summary


def summarize_model_config_bundle(config_bundle: ModelConfigBundle) -> dict[str, list[dict[str, Any]]]:
    return {
        "dialogue": summarize_model_config(config_bundle.dialogue),
        "controller": summarize_model_config(config_bundle.controller),
    }


def create_run_artifacts(output_dir: str | Path, output_prefix: str) -> RunArtifacts:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = target_dir / f"{output_prefix}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_dir=run_dir,
        project_jsonl_path=run_dir / "projects.jsonl",
        project_checkpoint_path=run_dir / "project_checkpoints.jsonl",
        conversation_timeline_path=run_dir / "conversation_timeline.txt",
        behavior_timeline_path=run_dir / "behavior_timeline.txt",
        behavior_events_path=run_dir / "behavior_events.jsonl",
        quality_report_json_path=run_dir / "quality_report.json",
        quality_report_md_path=run_dir / "quality_report.md",
        state_path=run_dir / "state.json",
        final_dataset_path=run_dir / "final_dataset.json",
        metadata_path=run_dir / "metadata.json",
        log_path=run_dir / "run.log",
    )


def create_dataset_skeleton(
    experiment: ExperimentDefinition,
    config_bundle: ModelConfigBundle,
    only_groups: set[str] | None,
    persona_source: str | Path,
    scenario_source: str | Path,
    artifacts: RunArtifacts,
) -> dict[str, Any]:
    selected_group_ids = [group.group_id for group in select_groups(experiment, only_groups)]
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "schema_version": experiment.schema_version,
        "dataset_name": experiment.dataset_name,
        "description": experiment.description,
        "generated_at": now,
        "updated_at": now,
        "status": "running",
        "persona_source": str(persona_source),
        "scenario_source": str(scenario_source),
        "experiment_source": str(experiment.source_path),
        "model_config_summary": summarize_model_config_bundle(config_bundle),
        "generation_settings": asdict(experiment.generation_settings),
        "selected_group_ids": selected_group_ids,
        "run_directory": str(artifacts.run_dir),
        "projects": [],
    }


def write_run_metadata(
    artifacts: RunArtifacts,
    experiment: ExperimentDefinition,
    config_bundle: ModelConfigBundle,
    only_groups: set[str] | None,
) -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_name": experiment.dataset_name,
        "schema_version": experiment.schema_version,
        "experiment_source": str(experiment.source_path),
        "selected_group_ids": [group.group_id for group in select_groups(experiment, only_groups)],
        "model_config_summary": summarize_model_config_bundle(config_bundle),
        "generation_settings": asdict(experiment.generation_settings),
        "artifacts": {
            "projects_jsonl": str(artifacts.project_jsonl_path),
            "project_checkpoints_jsonl": str(artifacts.project_checkpoint_path),
            "conversation_timeline_txt": str(artifacts.conversation_timeline_path),
            "behavior_timeline_txt": str(artifacts.behavior_timeline_path),
            "behavior_events_jsonl": str(artifacts.behavior_events_path),
            "quality_report_json": str(artifacts.quality_report_json_path),
            "quality_report_md": str(artifacts.quality_report_md_path),
            "state_json": str(artifacts.state_path),
            "final_dataset_json": str(artifacts.final_dataset_path),
            "log_file": str(artifacts.log_path),
        },
    }
    artifacts.metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_project_checkpoint(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    with artifacts.project_jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(project_record, ensure_ascii=False))
        handle.write("\n")


def append_conversation_timeline(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    with artifacts.conversation_timeline_path.open("a", encoding="utf-8") as handle:
        handle.write(format_project_conversation_timeline(project_record))
        handle.write("\n\n")


def append_project_progress_timeline(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    sessions = project_record.get("sessions", [])
    if not sessions:
        return

    latest_session = sessions[-1]
    with artifacts.conversation_timeline_path.open("a", encoding="utf-8") as handle:
        if len(sessions) == 1:
            handle.write(format_project_conversation_header(project_record))
            handle.write("\n")
        handle.write("\n".join(format_session_conversation(latest_session)).rstrip())
        handle.write("\n\n")


def append_behavior_timeline(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    with artifacts.behavior_timeline_path.open("a", encoding="utf-8") as handle:
        handle.write(format_project_behavior_timeline(project_record))
        handle.write("\n\n")


def append_behavior_events(artifacts: RunArtifacts, events: list[dict[str, Any]]) -> None:
    if not events:
        return
    with artifacts.behavior_events_path.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False))
            handle.write("\n")


def append_project_progress_behavior_timeline(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    sessions = project_record.get("sessions", [])
    if not sessions:
        return

    latest_session = sessions[-1]
    with artifacts.behavior_timeline_path.open("a", encoding="utf-8") as handle:
        if len(sessions) == 1:
            handle.write(format_project_behavior_header(project_record))
            handle.write("\n")
        handle.write("\n".join(format_session_behavior_timeline(latest_session)).rstrip())
        handle.write("\n\n")


def append_project_progress_snapshot(artifacts: RunArtifacts, project_record: dict[str, Any]) -> None:
    with artifacts.project_checkpoint_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(project_record, ensure_ascii=False))
        handle.write("\n")


def write_dataset_state(dataset: dict[str, Any], path: str | Path) -> Path:
    dataset["updated_at"] = datetime.now().isoformat(timespec="seconds")
    target_path = Path(path)
    target_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_path


def format_project_conversation_timeline(project_record: dict[str, Any]) -> str:
    lines = [format_project_conversation_header(project_record), ""]

    for session in project_record["sessions"]:
        lines.extend(format_session_conversation(session))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_project_conversation_header(project_record: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"项目：{project_record['project_id']}",
            f"场景：{project_record['scenario']['title']}",
        ]
    )


def format_session_conversation(session: dict[str, Any]) -> list[str]:
    lines = [
        f"===== 第 {session['meeting_index']} 次对话 =====",
        "",
    ]

    events_by_turn = group_events_by_turn(session.get("events", []))
    for message in session["messages"]:
        lines.append(f"{message['speaker']}：{message['content']}")
        for event in events_by_turn.get(message["turn"], []):
            lines.append(format_event_line(event))

    return lines


def group_events_by_turn(events: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault(event["timestamp_index"], []).append(event)
    return grouped


def format_event_line(event: dict[str, Any]) -> str:
    return (
        f"【操作】{event['actor']} | {event['event_type']} | "
        f"{event['status']} | {event['artifact_summary']}"
    )


def format_timestamp_for_display(raw_value: str | None) -> str:
    if not raw_value:
        return "unknown"
    try:
        return datetime.fromisoformat(raw_value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw_value


def format_date_for_display(raw_value: str | None) -> str:
    if not raw_value:
        return "unknown"
    try:
        return datetime.fromisoformat(raw_value).strftime("%Y-%m-%d")
    except ValueError:
        return raw_value


def format_project_conversation_header(project_record: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Project: {project_record['project_id']}",
            f"Scenario: {project_record['scenario']['title']}",
            f"Project anchor time: {format_timestamp_for_display(project_record.get('project_anchor_time'))}",
        ]
    )


def format_session_conversation(session: dict[str, Any]) -> list[str]:
    lines = [
        f"===== Session {session['meeting_index']} =====",
        f"Date: {format_date_for_display(session.get('session_start_time'))}",
        f"Start: {format_timestamp_for_display(session.get('session_start_time'))}",
        "",
    ]
    for message in session["messages"]:
        lines.append(
            f"[{format_timestamp_for_display(message.get('message_timestamp'))}] "
            f"{message['speaker']}: {message['content']}"
        )
    return lines


def format_project_behavior_header(project_record: dict[str, Any]) -> str:
    return f"Project: {project_record['project_id']}"


def format_project_behavior_timeline(project_record: dict[str, Any]) -> str:
    lines = [format_project_behavior_header(project_record), ""]
    for session in project_record["sessions"]:
        lines.extend(format_session_behavior_timeline(session))
        lines.append("")
    return "\n".join(lines).rstrip()


def format_session_behavior_timeline(session: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for event in session.get("events", []):
        lines.append(format_behavior_event_line(event))
    for event in session.get("between_session_events_after", []):
        lines.append(format_behavior_event_line(event))
    return lines


def format_behavior_event_line(event: dict[str, Any]) -> str:
    return (
        f"[{format_timestamp_for_display(event.get('timestamp'))}] "
        f"{event.get('actor')} | {event.get('artifact_summary')}"
    )


def write_quality_reports(artifacts: RunArtifacts, dataset: dict[str, Any]) -> None:
    diagnostics = build_dataset_quality_diagnostics(dataset)
    artifacts.quality_report_json_path.write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    artifacts.quality_report_md_path.write_text(
        format_quality_report_markdown(diagnostics),
        encoding="utf-8",
    )


def iter_projects(
    personas: dict[str, PersonaRole],
    scenarios: dict[str, ScenarioDefinition],
    experiment: ExperimentDefinition,
    dialogue_config_list: list[dict[str, Any]],
    controller_config_list: list[dict[str, Any]],
    cache_seed: int,
    only_groups: set[str] | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> Iterator[dict[str, Any]]:
    selected_groups = select_groups(experiment, only_groups)
    if not selected_groups:
        raise ValueError("No groups selected to run.")

    for group_index, group in enumerate(selected_groups, start=1):
        members = [personas[role_id] for role_id in group.member_role_ids]
        scenario = resolve_group_scenario(group, scenarios, experiment)
        for run_index in range(1, group.repeats + 1):
            yield run_project_timeline(
                members=members,
                group=group,
                scenario=scenario,
                experiment=experiment,
                dialogue_config_list=dialogue_config_list,
                controller_config_list=controller_config_list,
                cache_seed=cache_seed + (group_index * 100) + run_index - 1,
                run_index=run_index,
                progress_callback=progress_callback,
            )


def run_project_timeline(
    members: list[PersonaRole],
    group: GroupDefinition,
    scenario: ScenarioDefinition,
    experiment: ExperimentDefinition,
    dialogue_config_list: list[dict[str, Any]],
    controller_config_list: list[dict[str, Any]],
    cache_seed: int,
    run_index: int,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    rng = random.Random(cache_seed)
    team_profiles = build_agent_profiles(members)
    planned_sessions = rng.randint(group.session_count_range[0], group.session_count_range[1])
    project_id = f"{group.group_id}__project_{run_index:02d}"
    project_anchor_time = build_project_anchor_time(planned_sessions=planned_sessions, rng=rng)
    project_time_cursor = project_anchor_time
    project_state = build_initial_project_state(scenario)
    project_state_history = [
        {
            "meeting_index": 0,
            "session_id": None,
            "carryover_summary": "项目刚启动，团队还没有进行正式会议。",
            **deepcopy(project_state),
        }
    ]
    project_events: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []
    project_outcome = "ongoing"

    LOGGER.info(
        "Starting project %s scenario=%s planned_sessions=%s",
        project_id,
        scenario.scenario_id,
        planned_sessions,
    )

    for meeting_index in range(1, planned_sessions + 1):
        presence_map = assign_presence_modes(
            team_profiles=team_profiles,
            variability=group.attendance_variability,
            rng=rng,
        )
        deadline_pressure = compute_deadline_pressure(
            meeting_index=meeting_index,
            total_sessions=planned_sessions,
            curve=group.deadline_pressure_curve,
        )
        project_state["deadline_pressure"] = deadline_pressure

        session_record = run_single_session(
            project_id=project_id,
            meeting_index=meeting_index,
            total_sessions=planned_sessions,
            team_profiles=team_profiles,
            presence_map=presence_map,
            scenario=scenario,
            project_state=deepcopy(project_state),
            recent_events=project_events[-6:],
            project_event_count=len(project_events),
            group=group,
            experiment=experiment,
            dialogue_config_list=dialogue_config_list,
            controller_config_list=controller_config_list,
            cache_seed=cache_seed + meeting_index - 1,
        )
        apply_session_timeline(
            session_record=session_record,
            session_start_time=project_time_cursor if meeting_index == 1 else build_next_session_start_time(project_time_cursor, rng),
            rng=rng,
        )
        between_session_events = synthesize_between_session_events(
            project_id=project_id,
            session_record=session_record,
            team_profiles=team_profiles,
            project_event_offset=len(project_events) + len(session_record["events"]),
            rng=rng,
            allow_inference=(meeting_index < planned_sessions),
        )
        session_record["between_session_events_after"] = between_session_events
        sessions.append(session_record)
        project_events.extend(session_record["events"])
        project_events.extend(between_session_events)
        project_time_cursor = get_latest_event_time(session_record, between_session_events)
        project_state = deepcopy(session_record["state_after_session"])
        project_state_history.append(
            {
                "meeting_index": meeting_index,
                "session_id": session_record["session_id"],
                "carryover_summary": session_record["carryover_summary"],
                **deepcopy(project_state),
            }
        )

        project_end_signal = session_record["project_end_signal"]
        if (
            meeting_index < experiment.generation_settings.min_project_sessions_before_terminal
            and project_end_signal in {"completed", "stalled", "abandoned", "forced_submission"}
        ):
            LOGGER.info(
                "Ignoring early terminal signal for %s at session %s: %s",
                project_id,
                meeting_index,
                project_end_signal,
            )
            project_end_signal = "continue"
            session_record["project_end_signal"] = "continue"
        if project_end_signal != "continue" and between_session_events:
            project_events = project_events[: -len(between_session_events)]
            between_session_events = []
            session_record["between_session_events_after"] = []
            project_time_cursor = get_latest_event_time(session_record, between_session_events)
        if progress_callback is not None:
            progress_callback(
                build_project_record(
                    project_id=project_id,
                    project_anchor_time=project_anchor_time,
                    group=group,
                    experiment=experiment,
                    scenario=scenario,
                    team_profiles=team_profiles,
                    planned_sessions=planned_sessions,
                    sessions=sessions,
                    project_state_history=project_state_history,
                    project_events=project_events,
                    project_outcome="ongoing",
                    status="in_progress",
                    run_index=run_index,
                )
            )
        if project_end_signal in {"completed", "stalled", "abandoned", "forced_submission"}:
            project_outcome = project_end_signal
            break

    if project_outcome == "ongoing" or project_outcome == "stalled":
        project_outcome = finalize_project_outcome(project_state, sessions)

    LOGGER.info(
        "Finished project %s sessions=%s outcome=%s",
        project_id,
        len(sessions),
        project_outcome,
    )

    return build_project_record(
        project_id=project_id,
        project_anchor_time=project_anchor_time,
        group=group,
        experiment=experiment,
        scenario=scenario,
        team_profiles=team_profiles,
        planned_sessions=planned_sessions,
        sessions=sessions,
        project_state_history=project_state_history,
        project_events=project_events,
        project_outcome=project_outcome,
        status="completed",
        run_index=run_index,
    )


def build_project_record(
    project_id: str,
    project_anchor_time: datetime,
    group: GroupDefinition,
    experiment: ExperimentDefinition,
    scenario: ScenarioDefinition,
    team_profiles: list[dict[str, Any]],
    planned_sessions: int,
    sessions: list[dict[str, Any]],
    project_state_history: list[dict[str, Any]],
    project_events: list[dict[str, Any]],
    project_outcome: str,
    status: str,
    run_index: int,
) -> dict[str, Any]:
    artifacts = build_artifacts_from_events(project_events)
    quality_diagnostics = build_project_quality_diagnostics(
        project_id=project_id,
        sessions=sessions,
        project_events=project_events,
        project_state_history=project_state_history,
        project_outcome=project_outcome,
        team_profiles=team_profiles,
    )
    return {
        "project_id": project_id,
        "project_anchor_time": project_anchor_time.isoformat(timespec="seconds"),
        "group_id": group.group_id,
        "status": status,
        "run_index": run_index,
        "group_tags": group.tags or experiment.default_groupchat.get("tags", []),
        "scenario": asdict(scenario),
        "team_members": [
            {
                **asdict(profile["persona"]),
                "agent_name": profile["agent_name"],
                "display_name": profile["display_name"],
            }
            for profile in team_profiles
        ],
        "planned_session_count": planned_sessions,
        "generated_session_count": len(sessions),
        "project_outcome": project_outcome,
        "project_state_history": project_state_history,
        "events": project_events,
        "behavior_events": project_events,
        "artifacts": artifacts,
        "sessions": sessions,
        "quality_diagnostics": quality_diagnostics,
    }


def run_single_session(
    project_id: str,
    meeting_index: int,
    total_sessions: int,
    team_profiles: list[dict[str, Any]],
    presence_map: dict[str, str],
    scenario: ScenarioDefinition,
    project_state: dict[str, Any],
    recent_events: list[dict[str, Any]],
    project_event_count: int,
    group: GroupDefinition,
    experiment: ExperimentDefinition,
    dialogue_config_list: list[dict[str, Any]],
    controller_config_list: list[dict[str, Any]],
    cache_seed: int,
) -> dict[str, Any]:
    try:
        import autogen
    except ImportError as exc:
        raise RuntimeError(
            "AutoGen is not installed in the active environment. Install requirements.txt first."
        ) from exc

    group_defaults = experiment.default_groupchat
    max_round = group.max_round or group_defaults.get("max_round", 12)
    speaker_selection_method = group.speaker_selection_method or group_defaults.get(
        "speaker_selection_method", "auto"
    )
    allow_repeat_speaker = (
        group.allow_repeat_speaker
        if group.allow_repeat_speaker is not None
        else group_defaults.get("allow_repeat_speaker", False)
    )
    temperature = (
        group.temperature if group.temperature is not None else group_defaults.get("temperature", 0.8)
    )
    generation_settings = experiment.generation_settings
    session_id = f"{project_id}__session_{meeting_index:02d}"
    llm_config = {
        "config_list": deepcopy(dialogue_config_list),
        "cache_seed": None,
        "temperature": temperature,
        "timeout": generation_settings.session_timeout_seconds,
    }
    controller_llm_config = {
        "config_list": deepcopy(controller_config_list),
        "cache_seed": None,
        "temperature": 0.2,
        "timeout": generation_settings.session_timeout_seconds,
    }

    session_prompt = compose_session_prompt(
        scenario=scenario,
        project_state=project_state,
        recent_events=recent_events,
        team_profiles=team_profiles,
        presence_map=presence_map,
        meeting_index=meeting_index,
        total_sessions=total_sessions,
        offtopic_tendency=group.offtopic_tendency,
    )

    live_profiles = [
        profile for profile in team_profiles if presence_map[profile["agent_name"]] in PRESENCE_LIVE_MODES
    ]
    agents = [
        _build_assistant_agent(
            autogen=autogen,
            profile=profile,
            llm_config=llm_config,
            presence_mode=presence_map[profile["agent_name"]],
            offtopic_tendency=group.offtopic_tendency,
            project_state=project_state,
        )
        for profile in live_profiles
    ]
    speaker_selection_policy = str(speaker_selection_method)
    urgency_selection_state = None
    if speaker_selection_method == "urgency_queue":
        urgency_settings = merge_urgency_settings(
            group_defaults.get("turn_taking"),
            group.turn_taking,
        )
        speaker_selection_method, urgency_selection_state = build_urgency_speaker_selector(
            team_profiles=live_profiles,
            presence_map=presence_map,
            project_state=project_state,
            settings=urgency_settings,
            rng=random.Random(cache_seed + meeting_index),
        )

    groupchat = autogen.GroupChat(
        agents=agents,
        messages=[],
        max_round=max_round,
        speaker_selection_method=speaker_selection_method,
        allow_repeat_speaker=allow_repeat_speaker,
    )

    manager = _build_groupchat_manager(
        autogen=autogen,
        groupchat=groupchat,
        llm_config=llm_config,
        system_message=compose_manager_system_message(
            system_message=experiment.manager_system_message,
            max_round=max_round,
            offtopic_tendency=group.offtopic_tendency,
        ),
    )

    task_host = autogen.UserProxyAgent(
        name="TaskHost",
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=False,
    )

    LOGGER.info(
        "Starting session %s live_members=%s presence=%s speaker_policy=%s",
        session_id,
        [profile["agent_name"] for profile in live_profiles],
        presence_map,
        speaker_selection_policy,
    )
    try:
        task_host.initiate_chat(manager, message=session_prompt, clear_history=True)
    except TypeError:
        task_host.initiate_chat(manager, message=session_prompt)

    name_to_profile = {profile["agent_name"]: profile for profile in team_profiles}
    raw_messages = serialize_groupchat_messages(
        groupchat_messages=groupchat.messages,
        name_to_profile=name_to_profile,
        presence_map=presence_map,
    )
    live_speaker_names = {profile["agent_name"] for profile in live_profiles}
    repair_round = 0
    while (
        needs_discussion_repair(
            messages=raw_messages,
            live_speaker_names=live_speaker_names,
            min_effective_messages=generation_settings.min_effective_messages,
            min_participating_speakers=generation_settings.min_participating_speakers,
        )
        and repair_round < generation_settings.repair_max_rounds
    ):
        follow_up_prompt = compose_discussion_repair_prompt(
            scenario=scenario,
            project_state=project_state,
            live_profiles=live_profiles,
            current_messages=raw_messages,
        )
        try:
            task_host.initiate_chat(manager, message=follow_up_prompt, clear_history=False)
        except TypeError:
            task_host.initiate_chat(manager, message=follow_up_prompt)
        raw_messages = serialize_groupchat_messages(
            groupchat_messages=groupchat.messages,
            name_to_profile=name_to_profile,
            presence_map=presence_map,
        )
        repair_round += 1

    async_profiles = [
        profile for profile in team_profiles if presence_map[profile["agent_name"]] == "async_followup"
    ]
    if async_profiles:
        for profile in async_profiles[:1]:
            raw_messages.append(
                {
                    "turn": len(raw_messages) + 1,
                    "speaker": profile["agent_name"],
                    "display_name": profile["display_name"],
                    "role_id": profile["persona"].role_id,
                    "persona_name": profile["persona"].name,
                    "content": compose_async_followup_message(
                        persona=profile["persona"],
                        project_state=project_state,
                    ),
                    "event_refs": [],
                    "mentioned_artifacts": [],
                    "speaker_presence_mode": "async_followup",
                }
            )

    controller_payload = analyze_session_with_controller(
        autogen=autogen,
        llm_config=controller_llm_config,
        scenario=scenario,
        project_state=project_state,
        recent_events=recent_events,
        session_id=session_id,
        meeting_index=meeting_index,
        total_sessions=total_sessions,
        messages=raw_messages,
        team_profiles=team_profiles,
        presence_map=presence_map,
        force_project_closure=(
            generation_settings.force_project_closure_on_final_session
            and meeting_index >= total_sessions
        ),
    )

    messages = deepcopy(raw_messages)
    if generation_settings.enable_closer and controller_payload["should_add_closing_utterance"]:
        closer_profile = resolve_closer_profile(
            team_profiles=team_profiles,
            presence_map=presence_map,
            closer_role_id=controller_payload["closer_role_id"],
        )
        if closer_profile is not None:
            closing_message = generate_closing_message(
                autogen=autogen,
                llm_config=controller_llm_config,
                profile=closer_profile,
                scenario=scenario,
                session_outcome=controller_payload["session_outcome"],
                carryover_summary=controller_payload["carryover_summary"],
                project_end_signal=controller_payload["project_end_signal"],
            )
            messages.append(
                {
                    "turn": len(messages) + 1,
                    "speaker": closer_profile["agent_name"],
                    "display_name": closer_profile["display_name"],
                    "role_id": closer_profile["persona"].role_id,
                    "persona_name": closer_profile["persona"].name,
                    "content": closing_message,
                    "event_refs": [],
                    "mentioned_artifacts": [],
                    "speaker_presence_mode": presence_map[closer_profile["agent_name"]],
                }
            )

    events = detect_events(
        project_id=project_id,
        meeting_index=meeting_index,
        session_id=session_id,
        messages=messages,
        project_event_offset=project_event_count,
    )
    attach_event_references(messages, events)

    participant_statuses = [
        {
            "agent_name": profile["agent_name"],
            "role_id": profile["persona"].role_id,
            "display_name": profile["display_name"],
            "presence_mode": presence_map[profile["agent_name"]],
        }
        for profile in team_profiles
    ]

    LOGGER.info(
        "Finished session %s messages=%s outcome=%s end_signal=%s",
        session_id,
        len(messages),
        controller_payload["session_outcome"],
        controller_payload["project_end_signal"],
    )

    return {
        "project_id": project_id,
        "session_id": session_id,
        "meeting_index": meeting_index,
        "session_prompt": session_prompt,
        "participants_present": [
            profile["agent_name"]
            for profile in team_profiles
            if presence_map[profile["agent_name"]] != "absent"
        ],
        "participant_statuses": participant_statuses,
        "carryover_summary": controller_payload["carryover_summary"],
        "messages": messages,
        "message_count": len(messages),
        "session_outcome": controller_payload["session_outcome"],
        "project_end_signal": controller_payload["project_end_signal"],
        "state_delta": controller_payload["state_delta"],
        "state_after_session": controller_payload["state_after_session"],
        "events": events,
        "between_session_events_after": [],
        "session_start_time": None,
        "session_end_time": None,
        **(
            urgency_selection_state.asdict()
            if urgency_selection_state is not None
            else {
                "speaker_selection_policy": speaker_selection_policy,
                "interruption_like_turns": [],
                "silence_stop_used": False,
                "stop_reason": None,
                "speaker_selection_trace": [],
            }
        ),
    }


def resolve_group_scenario(
    group: GroupDefinition,
    scenarios: dict[str, ScenarioDefinition],
    experiment: ExperimentDefinition,
) -> ScenarioDefinition:
    if group.scenario_id:
        if group.scenario_id not in scenarios:
            raise ValueError(f"Group '{group.group_id}' references unknown scenario_id '{group.scenario_id}'.")
        return scenarios[group.scenario_id]

    task_text = group.task or experiment.default_task or "学生围绕课程项目展开讨论。"
    return ScenarioDefinition(
        scenario_id=f"legacy_{group.group_id}",
        title="Legacy Scenario",
        task_type="legacy_task",
        course_context="未提供课程上下文",
        deliverable_type="discussion",
        deadline_span="unknown",
        difficulty="medium",
        artifact_types=["notes"],
        project_brief=task_text,
        initial_context=task_text,
    )


def build_initial_project_state(scenario: ScenarioDefinition) -> dict[str, Any]:
    return {
        "current_goal": f"围绕“{scenario.title}”推进项目，并逐步形成可交付成果。",
        "known_decisions": [],
        "open_issues": [f"还没有确定 {scenario.deliverable_type} 的完整方案。"],
        "assigned_work": [],
        "progress_level": "not_started",
        "deadline_pressure": "low",
        "team_mood": "neutral",
    }


def build_agent_profiles(members: list[PersonaRole]) -> list[dict[str, Any]]:
    used_names: set[str] = set()
    profiles: list[dict[str, Any]] = []
    for persona in members:
        base_name = ROLE_NICKNAME_MAP.get(persona.role_id, persona.name.replace("_", " "))
        agent_name = make_unique_name(base_name, used_names)
        used_names.add(agent_name)
        profiles.append(
            {
                "persona": persona,
                "agent_name": agent_name,
                "display_name": f"{agent_name} ({persona.description})",
            }
        )
    return profiles


def make_unique_name(base_name: str, used_names: set[str]) -> str:
    if base_name not in used_names:
        return base_name
    suffix = 2
    while f"{base_name}{suffix}" in used_names:
        suffix += 1
    return f"{base_name}{suffix}"


def assign_presence_modes(
    team_profiles: list[dict[str, Any]],
    variability: str,
    rng: random.Random,
) -> dict[str, str]:
    mode_weights = {
        "low": {"active": 0.7, "passive": 0.15, "late": 0.1, "async_followup": 0.03, "absent": 0.02},
        "medium": {"active": 0.5, "passive": 0.2, "late": 0.15, "async_followup": 0.1, "absent": 0.05},
        "high": {"active": 0.38, "passive": 0.22, "late": 0.18, "async_followup": 0.12, "absent": 0.1},
    }
    weights = mode_weights.get(variability, mode_weights["medium"])
    modes = list(weights.keys())
    probabilities = list(weights.values())

    presence_map: dict[str, str] = {}
    for profile in team_profiles:
        presence_map[profile["agent_name"]] = rng.choices(modes, weights=probabilities, k=1)[0]

    live_members = [name for name, mode in presence_map.items() if mode in PRESENCE_LIVE_MODES]
    if len(live_members) < 2:
        absent_candidates = [name for name, mode in presence_map.items() if mode not in PRESENCE_LIVE_MODES]
        rng.shuffle(absent_candidates)
        for candidate in absent_candidates:
            presence_map[candidate] = "passive"
            live_members.append(candidate)
            if len(live_members) >= 2:
                break

    return presence_map


def compute_deadline_pressure(meeting_index: int, total_sessions: int, curve: str) -> str:
    ratio = meeting_index / max(total_sessions, 1)
    if curve == "late_crunch":
        if ratio < 0.7:
            return "low"
        if ratio < 0.9:
            return "medium"
        return "high"
    if curve == "ramp_up":
        if ratio < 0.34:
            return "low"
        if ratio < 0.75:
            return "medium"
        return "high"
    if curve == "front_loaded":
        if ratio < 0.34:
            return "high"
        if ratio < 0.67:
            return "medium"
        return "low"
    if ratio < 0.5:
        return "low"
    if ratio < 0.85:
        return "medium"
    return "high"


def compose_session_prompt(
    scenario: ScenarioDefinition,
    project_state: dict[str, Any],
    recent_events: list[dict[str, Any]],
    team_profiles: list[dict[str, Any]],
    presence_map: dict[str, str],
    meeting_index: int,
    total_sessions: int,
    offtopic_tendency: str,
) -> str:
    recent_event_lines = "\n".join(
        f"- {event['actor']} | {event['artifact_summary']}"
        for event in recent_events[-4:]
    )
    recent_event_block = recent_event_lines or "- 目前还没有记录到额外操作事件。"
    known_decisions = "\n".join(f"- {item}" for item in project_state["known_decisions"]) or "- 暂无明确结论。"
    open_issues = "\n".join(f"- {item}" for item in project_state["open_issues"]) or "- 暂无明确遗留问题。"
    assigned_work = "\n".join(f"- {item}" for item in project_state["assigned_work"]) or "- 暂无稳定分工。"
    common_operations = "\n".join(f"- {item}" for item in scenario.common_operations) or "- 查资料、整理大纲、编辑材料、同步结果。"
    conflict_points = "\n".join(f"- {item}" for item in scenario.conflict_points) or "- 分工、范围、时间压力或技术可行性可能产生分歧。"
    natural_endings = "\n".join(f"- {item}" for item in scenario.natural_endings) or "- 推进后暂停、暂时僵持、冲突散会或阶段性完成。"
    attendance_lines = "\n".join(
        f"- {profile['agent_name']}：{describe_presence_mode(presence_map[profile['agent_name']])}"
        for profile in team_profiles
    )
    offtopic_note = {
        "low": "可以有极少量生活化表达，但仍要以任务推进为主。",
        "medium": "允许自然的闲聊、抱怨和情绪表达，但不要长时间脱离项目。",
        "high": "允许明显更生活化的学生交流、吐槽和短暂跑题，只要整体仍围绕同一项目时间线演化。",
    }.get(offtopic_tendency, "允许适量自然闲聊，但不要一直跑题。")

    return (
        f"你们是一组大学生，正在连续推进同一个课程项目。这是第 {meeting_index}/{total_sessions} 次讨论。\n\n"
        f"项目标题：{scenario.title}\n"
        f"任务类型：{scenario.task_type}\n"
        f"课程场景：{scenario.course_context}\n"
        f"交付物：{scenario.deliverable_type}\n"
        f"项目难度：{scenario.difficulty}\n"
        f"时间跨度：{scenario.deadline_span}\n"
        f"项目背景：{scenario.project_brief or scenario.initial_context}\n\n"
        "当前项目状态：\n"
        f"- 当前目标：{project_state['current_goal']}\n"
        f"- 进度水平：{project_state['progress_level']}\n"
        f"- 截止压力：{project_state['deadline_pressure']}\n"
        f"- 团队氛围：{project_state['team_mood']}\n\n"
        "已知结论：\n"
        f"{known_decisions}\n\n"
        "待解决问题：\n"
        f"{open_issues}\n\n"
        "已有分工：\n"
        f"{assigned_work}\n\n"
        "最近发生的事件：\n"
        f"{recent_event_block}\n\n"
        "这个场景中常见的学生操作：\n"
        f"{common_operations}\n\n"
        "可能出现的真实分歧：\n"
        f"{conflict_points}\n\n"
        "可能自然结束的方式：\n"
        f"{natural_endings}\n\n"
        "本次成员状态：\n"
        f"{attendance_lines}\n\n"
        "要求：\n"
        "1. 你们不是在开正式评审会，而是在自然讨论项目进展。\n"
        "2. 不要机械地覆盖固定议程，应该根据当前进展、遗留问题和成员状态自然展开。\n"
        "3. 允许有人吐槽、闲聊、抱怨、插科打诨或临时跑题，但整体仍要围绕这个项目。\n"
        f"4. {offtopic_note}\n"
        "5. 这次讨论的结局不预设成功或失败，可以推进一些进展、谈崩、搁置、或者先散会等下一次再说。\n"
        "6. 不要在刚开场时就立刻散会，至少要出现几轮有效交流，或者明确暴露出真实分歧后，才适合结束。\n"
        "7. 如果讨论已经到一个自然停点，请用像真实学生一样的方式收尾，例如“今天先到这”“这个点先放一下”“那我晚点把文档传上来”。\n"
        f"8. 如果你们决定自然结束本次讨论，请由任意一位成员在最后一条消息末尾单独补上一行 {INTERNAL_SESSION_END_TOKEN}。这只是内部结束信号，不要解释它。"
    )


def describe_presence_mode(presence_mode: str) -> str:
    descriptions = {
        "active": "正常参与，会实时发言。",
        "passive": "在线但存在感较低，发言会偏少、偏短。",
        "late": "会迟到，进入状态较慢。",
        "async_followup": "这次没能实时参加，可能会在会后补一句。",
        "absent": "本次基本缺席。",
    }
    return descriptions.get(presence_mode, "状态未知。")


def compose_manager_system_message(
    system_message: str,
    max_round: int,
    offtopic_tendency: str,
) -> str:
    offtopic_note = {
        "low": "只允许极少量偏离任务的话题。",
        "medium": "允许少量生活化闲聊，但不要让对话长时间失控。",
        "high": "允许明显更生活化的闲聊和情绪表达，但要避免彻底空转。",
    }.get(offtopic_tendency, "允许适量生活化表达。")
    return (
        f"{system_message}\n"
        "你是学生项目讨论的流程协调者，不是会议秘书，也不是强制总结器。\n"
        f"{offtopic_note}\n"
        "你的职责是：抑制明显的重复和空转；在成员长时间各说各话时适度拉回项目；在快到自然停点时优先让最合适的人收尾。\n"
        f"如果对话接近第 {max_round} 轮仍没有明显收束，请引导成员自然结束本次讨论，而不是强行完成全部任务。"
    )


def compose_persona_system_message(
    persona: PersonaRole,
    agent_name: str,
    presence_mode: str,
    offtopic_tendency: str,
    project_state: dict[str, Any],
) -> str:
    presence_note = {
        "active": "你这次正常参会，可以自然推进、闲聊、吐槽或回应别人。",
        "passive": "你这次在线但比较潜水，除非被点到或你特别想说，否则发言偏少、偏短。",
        "late": "你这次迟到了，对前文并不完全了解，参与时先用简短语句确认上下文。",
    }.get(presence_mode, "你这次正常参与。")
    offtopic_note = {
        "low": "尽量少跑题。",
        "medium": "允许少量生活化表达和短暂跑题。",
        "high": "允许明显更生活化的表达、情绪和短暂跑题，只要整体还围绕同一项目。",
    }.get(offtopic_tendency, "允许适量生活化表达。")
    return (
        f"{persona.system_message}\n"
        f"你在本轮群聊中的公开名字是 {agent_name}。\n"
        f"{presence_note}\n"
        f"{offtopic_note}\n"
        f"当前项目进度大致为：{project_state['progress_level']}；团队气氛为：{project_state['team_mood']}；截止压力为：{project_state['deadline_pressure']}。\n"
        "请像真实学生一样交流，不要把每句话都说成汇报摘要，也不要机械复述任务要求。\n"
        "每条消息只代表你自己，不要代替别人补台词，也不要写成“Leo: ... Max: ...”这种一条消息里出现多个人发言的格式。\n"
        "只有在至少两名成员已经围绕当前点位有来回交流后，才适合考虑自然收尾。\n"
        f"如果你觉得本次讨论已经到自然停点，可以用真实口语方式收尾，并在最后一行单独补上 {INTERNAL_SESSION_END_TOKEN} 作为内部结束信号。"
    )


def serialize_message(
    turn_index: int,
    message: dict[str, Any],
    name_to_profile: dict[str, dict[str, Any]],
    presence_map: dict[str, str],
    known_speaker_names: set[str],
) -> dict[str, Any]:
    speaker = message.get("name") or message.get("role") or "unknown"
    content = message.get("content", "")
    if isinstance(content, list):
        content = json.dumps(content, ensure_ascii=False)
    elif content is None:
        content = ""

    cleaned_content = normalize_speaker_message_content(
        content=str(content),
        speaker=speaker,
        known_speaker_names=known_speaker_names,
    )
    profile = name_to_profile.get(speaker)
    return {
        "turn": turn_index,
        "speaker": speaker,
        "display_name": profile["display_name"] if profile else speaker,
        "role_id": profile["persona"].role_id if profile else None,
        "persona_name": profile["persona"].name if profile else None,
        "content": cleaned_content,
        "event_refs": [],
        "mentioned_artifacts": [],
        "speaker_presence_mode": presence_map.get(speaker, "system"),
    }


def serialize_groupchat_messages(
    groupchat_messages: list[dict[str, Any]],
    name_to_profile: dict[str, dict[str, Any]],
    presence_map: dict[str, str],
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    known_speaker_names = set(name_to_profile)
    for message in groupchat_messages:
        if is_task_host_message(message):
            continue
        messages.append(
            serialize_message(
                turn_index=len(messages) + 1,
                message=message,
                name_to_profile=name_to_profile,
                presence_map=presence_map,
                known_speaker_names=known_speaker_names,
            )
        )
    return messages


def is_task_host_message(message: dict[str, Any]) -> bool:
    return (message.get("name") or message.get("role")) == "TaskHost"


def needs_discussion_repair(
    messages: list[dict[str, Any]],
    live_speaker_names: set[str],
    min_effective_messages: int = 8,
    min_participating_speakers: int = 3,
) -> bool:
    participant_messages = [
        message for message in messages if message["speaker"] in live_speaker_names and message["content"]
    ]
    unique_speakers = {message["speaker"] for message in participant_messages}
    required_unique_speakers = max(2, min(min_participating_speakers, len(live_speaker_names)))
    minimum_message_count = max(required_unique_speakers + 1, min_effective_messages)
    return len(participant_messages) < minimum_message_count or len(unique_speakers) < required_unique_speakers


def compose_discussion_repair_prompt(
    scenario: ScenarioDefinition,
    project_state: dict[str, Any],
    live_profiles: list[dict[str, Any]],
    current_messages: list[dict[str, Any]],
) -> str:
    spoken_speakers = {message["speaker"] for message in current_messages}
    missing_speakers = [
        profile["agent_name"] for profile in live_profiles if profile["agent_name"] not in spoken_speakers
    ]
    missing_text = "、".join(missing_speakers) if missing_speakers else "还没充分展开的成员"
    return (
        f"先别急着散会。围绕“{scenario.title}”至少再推进一步。\n"
        f"请至少明确以下三类内容中的一类：一个更具体的想法、一个明确分工、或者一个真实分歧点。\n"
        f"当前项目状态仍然是：{project_state['current_goal']}\n"
        f"优先让这些还没充分发言的人接一句：{missing_text}。\n"
        "每条消息只代表一个人，不要替别人写台词，也不要写成“Leo: ... Max: ...”这种格式。\n"
        "讨论可以自然、有口语感，但不要只说一句“今天先到这”。"
    )


def strip_internal_end_token(content: str) -> str:
    stripped = content.strip()
    if not stripped:
        return ""
    stripped = stripped.replace(INTERNAL_SESSION_END_TOKEN, "").strip()
    return stripped


def message_has_internal_end_token(content: str) -> bool:
    return INTERNAL_SESSION_END_TOKEN in content


def normalize_speaker_message_content(
    content: str,
    speaker: str,
    known_speaker_names: set[str],
) -> str:
    normalized = strip_internal_end_token(content)
    if not normalized:
        return ""

    normalized = re.sub(rf"^\s*{re.escape(speaker)}\s*[:：]\s*", "", normalized).strip()
    nested_label_match = find_other_speaker_label(normalized, speaker, known_speaker_names)
    if nested_label_match is not None:
        normalized = normalized[: nested_label_match.start()].strip()
    return normalized


def find_other_speaker_label(
    content: str,
    speaker: str,
    known_speaker_names: set[str],
) -> re.Match[str] | None:
    if not content or not known_speaker_names:
        return None

    label_pattern = "|".join(
        re.escape(name) for name in sorted(known_speaker_names, key=len, reverse=True)
    )
    if not label_pattern:
        return None

    pattern = re.compile(rf"(^|\n|\s)({label_pattern})\s*[:：]")
    for match in pattern.finditer(content):
        matched_speaker = match.group(2)
        if matched_speaker != speaker:
            return match
    return None


def build_project_anchor_time(planned_sessions: int, rng: random.Random) -> datetime:
    now = datetime.now().replace(second=0, microsecond=0)
    backfill_days = max(0, planned_sessions - 1) + rng.randint(0, 2)
    anchor = now - timedelta(days=backfill_days)
    return anchor.replace(
        hour=rng.choice([13, 14, 18, 19, 20]),
        minute=rng.choice([0, 10, 15, 20, 30, 45]),
    )


def build_next_session_start_time(previous_time: datetime, rng: random.Random) -> datetime:
    next_time = previous_time + timedelta(days=rng.choice([1, 1, 2, 2, 3]))
    next_time = next_time.replace(
        hour=rng.choice([13, 14, 18, 19, 20]),
        minute=rng.choice([0, 10, 15, 20, 30, 45]),
        second=0,
        microsecond=0,
    )
    if next_time <= previous_time:
        next_time = next_time + timedelta(days=1)
    return next_time


def apply_session_timeline(
    session_record: dict[str, Any],
    session_start_time: datetime,
    rng: random.Random,
) -> None:
    messages = session_record.get("messages", [])
    current_time = session_start_time
    turn_timestamps: dict[int, str] = {}

    # Use minute-level simulated pacing so transcripts look like meeting notes
    # without pretending to reconstruct precise wall-clock timings.
    for index, message in enumerate(messages):
        if index > 0:
            current_time += timedelta(
                minutes=infer_message_gap_minutes(
                    previous_message=messages[index - 1],
                    current_message=message,
                    rng=rng,
                )
            )
        message_timestamp = current_time.isoformat(timespec="seconds")
        message["message_timestamp"] = message_timestamp
        turn_timestamps[message["turn"]] = message_timestamp

    session_record["session_start_time"] = session_start_time.isoformat(timespec="seconds")
    session_record["session_end_time"] = current_time.isoformat(timespec="seconds")

    for event in session_record.get("events", []):
        event["timestamp"] = turn_timestamps.get(
            event.get("timestamp_index"),
            session_record["session_start_time"],
        )


def infer_message_gap_minutes(
    previous_message: dict[str, Any],
    current_message: dict[str, Any],
    rng: random.Random,
) -> int:
    if current_message.get("speaker_presence_mode") == "async_followup":
        return rng.choice([45, 60, 90, 120])

    base_gap = rng.choice([1, 2, 2, 3, 4])
    if current_message.get("speaker_presence_mode") == "late":
        base_gap += 1
    if current_message.get("speaker_presence_mode") == "passive":
        base_gap += 1
    if previous_message.get("speaker") == current_message.get("speaker"):
        base_gap = max(1, base_gap - 1)
    return base_gap


def get_latest_event_time(session_record: dict[str, Any], between_session_events: list[dict[str, Any]]) -> datetime:
    if between_session_events:
        return datetime.fromisoformat(between_session_events[-1]["timestamp"])
    if session_record.get("session_end_time"):
        return datetime.fromisoformat(session_record["session_end_time"])
    if session_record.get("session_start_time"):
        return datetime.fromisoformat(session_record["session_start_time"])
    return datetime.now().replace(second=0, microsecond=0)


def synthesize_between_session_events(
    project_id: str,
    session_record: dict[str, Any],
    team_profiles: list[dict[str, Any]],
    project_event_offset: int,
    rng: random.Random,
    allow_inference: bool,
) -> list[dict[str, Any]]:
    if not allow_inference:
        return []

    assigned_work = session_record.get("state_after_session", {}).get("assigned_work", [])
    if not assigned_work:
        return []

    session_end_time_raw = session_record.get("session_end_time")
    if not session_end_time_raw:
        return []
    cursor = datetime.fromisoformat(session_end_time_raw)

    events: list[dict[str, Any]] = []
    candidate_items = [item for item in assigned_work if infer_followup_event_type(item)]
    if not candidate_items:
        return events

    # Keep only a small amount of randomness so follow-up behavior stays stable
    # while still feeling less scripted across runs.
    selected_items = [rng.choice(candidate_items[: min(2, len(candidate_items))])]
    for work_item in selected_items:
        event_type = infer_followup_event_type(work_item)
        if event_type is None:
            continue
        actor = find_actor_in_text(work_item, team_profiles)
        if actor is None:
            actor = infer_actor_from_event_type(event_type, team_profiles, rng)
        if actor is None:
            continue
        source_basis = "between_sessions" if find_actor_in_text(work_item, team_profiles) else "persona_inferred"

        cursor += timedelta(hours=rng.choice([6, 12, 18]), minutes=rng.choice([0, 10, 20, 30, 45]))
        event_number = project_event_offset + len(events) + 1
        artifact_summary = summarize_between_session_event(event_type, work_item)
        status = "completed"
        event = {
            "event_id": f"{session_record['session_id']}__event_{event_number:03d}",
            "project_id": project_id,
            "session_id": session_record["session_id"],
            "meeting_index": session_record["meeting_index"],
            "actor": actor,
            "event_type": event_type,
            "event_phase": "between_sessions_after",
            "timestamp_index": None,
            "timestamp": cursor.isoformat(timespec="seconds"),
            "artifact_id": f"{session_record['session_id']}__artifact_{event_number:03d}",
            "artifact_name": f"{event_type}_{session_record['session_id']}_{event_number:03d}",
            "artifact_type": infer_artifact_type(event_type),
            "artifact_version": infer_artifact_version(status),
            "artifact_status": status,
            "artifact_owner": actor,
            "source_basis": source_basis,
            "visibility": infer_event_visibility(event_type, source_basis),
            "source_reference": work_item,
            "artifact_history": [
                {
                    "event_id": f"{session_record['session_id']}__event_{event_number:03d}",
                    "status": status,
                    "summary": artifact_summary,
                }
            ],
            "artifact_summary": artifact_summary,
            "status": status,
        }
        events.append(event)

    return events


def infer_followup_event_type(work_item: str) -> str | None:
    lowered = work_item.lower()
    if any(token in work_item for token in ["提交", "交作业", "交上去", "最终版", "定稿"]):
        return "submit_deliverable"
    if any(token in work_item for token in ["结果", "数据", "实验结果", "测试结果"]):
        return "share_result"
    if any(token in lowered for token in ["presentation", "present"]) or any(
        token in work_item for token in ["答辩", "展示", "路演", "口头汇报", "上台汇报"]
    ):
        return "present_defense"
    if any(token in lowered for token in ["upload", "share"]) or any(
        token in work_item
        for token in [
            "上传",
            "发群里",
            "共享",
            "网盘",
            "会议记录",
            "纪要",
            "记录",
            "汇总",
            "分类",
            "清单",
            "点子",
            "功能点",
            "PPT",
            "ppt",
            "slides",
            "幻灯",
            "文档",
            "报告",
            "初稿",
            "方案",
            "材料",
        ]
    ):
        return "upload_document"
    return None


def find_actor_in_text(work_item: str, team_profiles: list[dict[str, Any]]) -> str | None:
    for profile in team_profiles:
        if profile["agent_name"] in work_item or profile["display_name"] in work_item:
            return profile["agent_name"]
    return None


def infer_actor_from_event_type(
    event_type: str,
    team_profiles: list[dict[str, Any]],
    rng: random.Random,
) -> str | None:
    priority_by_event_type = {
        "upload_document": ["gatekeeper_expediter", "implementer_worker"],
        "share_result": ["implementer_worker", "information_seeker"],
        "submit_deliverable": ["gatekeeper_expediter", "implementer_worker"],
        "present_defense": ["initiator_proposer", "gatekeeper_expediter"],
    }
    preferred_roles = priority_by_event_type.get(event_type, [])
    for role_id in preferred_roles:
        for profile in team_profiles:
            if profile["persona"].role_id == role_id:
                return profile["agent_name"]
    if not team_profiles:
        return None
    return rng.choice(team_profiles)["agent_name"]


def infer_event_visibility(event_type: str, source_basis: str) -> str:
    if source_basis == "explicit_in_dialogue":
        return "public"
    if event_type in {"upload_document", "share_result", "submit_deliverable", "present_defense"}:
        return "public"
    if source_basis == "between_sessions":
        return "implied_next_session"
    return "private"


def summarize_between_session_event(event_type: str, work_item: str) -> str:
    return build_artifact_summary(event_type, work_item)


def detect_events(
    project_id: str,
    meeting_index: int,
    session_id: str,
    messages: list[dict[str, Any]],
    project_event_offset: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_counter = project_event_offset

    for message in messages:
        content = message["content"]
        if not content:
            continue
        for event_type, patterns in EVENT_PATTERNS.items():
            if any(pattern in content for pattern in patterns):
                if event_type not in FRONTEND_VISIBLE_EVENT_TYPES:
                    break
                status = infer_event_status(event_type, content)
                if status != "completed":
                    break
                event_counter += 1
                artifact_name = f"{event_type}_{session_id}_{event_counter:03d}"
                artifact_id = f"{session_id}__artifact_{event_counter:03d}"
                artifact_summary = build_artifact_summary(event_type, content)
                event = {
                    "event_id": f"{session_id}__event_{event_counter:03d}",
                    "project_id": project_id,
                    "session_id": session_id,
                    "meeting_index": meeting_index,
                    "actor": message["speaker"],
                    "event_type": event_type,
                    "event_phase": "in_session",
                    "timestamp_index": message["turn"],
                    "timestamp": None,
                    "artifact_id": artifact_id,
                    "artifact_name": artifact_name,
                    "artifact_type": infer_artifact_type(event_type),
                    "artifact_version": infer_artifact_version(status),
                    "artifact_status": status,
                    "artifact_owner": message["speaker"],
                    "source_basis": "explicit_in_dialogue",
                    "visibility": "public",
                    "source_reference": f"turn:{message['turn']}",
                    "artifact_history": [
                        {
                            "event_id": f"{session_id}__event_{event_counter:03d}",
                            "status": status,
                            "summary": artifact_summary,
                        }
                    ],
                    "artifact_summary": artifact_summary,
                    "status": status,
                }
                events.append(event)
                break

    return events


def infer_event_status(event_type: str, content: str) -> str:
    completed_tokens_by_type = {
        "upload_document": [
            "上传了",
            "已经上传",
            "上传完成",
            "上传到群里了",
            "上传到共享盘了",
            "发到群里了",
            "发群里了",
            "传群里了",
            "发你们了",
            "共享了",
            "传到网盘了",
            "放到共享盘了",
            "链接发了",
        ],
        "share_result": [
            "结果发了",
            "把结果发了",
            "分享了结果",
            "同步了结果",
            "结果出来了",
            "数据出来了",
            "发你们看了",
        ],
        "submit_deliverable": [
            "提交了",
            "已经提交",
            "提交完成",
            "交上去了",
            "交作业了",
            "已经交了",
            "定稿了",
        ],
        "present_defense": [
            "答辩了",
            "完成答辩",
            "进行了答辩",
            "汇报了",
            "进行了汇报",
            "开始汇报",
            "我来汇报",
            "我先汇报",
            "做了展示",
            "进行了展示",
            "开始展示",
            "我来展示",
            "路演了",
        ],
    }
    planned_tokens = ["待会", "等会", "准备", "打算", "计划", "之后", "晚点", "先做", "先去"]
    if any(token in content for token in completed_tokens_by_type.get(event_type, [])):
        return "completed"
    if any(token in content for token in planned_tokens):
        return "planned"
    return "mentioned"


def build_artifact_summary(event_type: str, content: str) -> str:
    if event_type == "upload_document":
        return f"上传了{infer_visible_artifact_subject(content, default='文件')}"
    if event_type == "share_result":
        return f"同步了{infer_visible_artifact_subject(content, default='结果')}"
    if event_type == "submit_deliverable":
        return f"提交了{infer_visible_artifact_subject(content, default='作业成果')}"
    if event_type == "present_defense":
        return f"进行了{infer_presentation_subject(content)}"
    return "完成了一项平台可见操作"


def infer_visible_artifact_subject(content: str, default: str) -> str:
    subject_patterns = [
        ("会议记录", ["会议记录", "纪要", "meeting notes", "meeting note"]),
        ("点子汇总", ["汇总", "分类汇总", "功能点", "点子", "清单"]),
        ("作业", ["作业", "assignment"]),
        ("PPT", ["PPT", "ppt", "slides", "幻灯片", "汇报材料", "演示材料"]),
        ("报告", ["报告", "实验报告", "文档", "初稿", "正文"]),
        ("材料", ["材料", "PDF", "pdf"]),
        ("结果", ["结果", "数据", "实验结果", "测试结果"]),
        ("链接", ["链接", "网盘"]),
    ]
    lowered = content.lower()
    for subject, patterns in subject_patterns:
        if any(pattern in content or pattern in lowered for pattern in patterns):
            return subject
    return default


def infer_presentation_subject(content: str) -> str:
    if "答辩" in content:
        return "答辩"
    if "路演" in content:
        return "路演"
    if "展示" in content or "演示" in content:
        return "展示"
    return "汇报"


def infer_artifact_type(event_type: str) -> str:
    mapping = {
        "upload_document": "shared_document",
        "share_result": "result_summary",
        "submit_deliverable": "submission_record",
        "present_defense": "presentation_record",
    }
    return mapping.get(event_type, "project_artifact")


def infer_artifact_version(status: str) -> int:
    return 1 if status in {"planned", "mentioned"} else 2


def attach_event_references(messages: list[dict[str, Any]], events: list[dict[str, Any]]) -> None:
    events_by_turn: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        events_by_turn.setdefault(event["timestamp_index"], []).append(event)

    for message in messages:
        turn_events = events_by_turn.get(message["turn"], [])
        if not turn_events:
            continue
        message["event_refs"] = [event["event_id"] for event in turn_events]
        message["mentioned_artifacts"] = [event["artifact_name"] for event in turn_events]


def analyze_session_with_controller(
    autogen: Any,
    llm_config: dict[str, Any],
    scenario: ScenarioDefinition,
    project_state: dict[str, Any],
    recent_events: list[dict[str, Any]],
    session_id: str,
    meeting_index: int,
    total_sessions: int,
    messages: list[dict[str, Any]],
    team_profiles: list[dict[str, Any]],
    presence_map: dict[str, str],
    force_project_closure: bool = False,
) -> dict[str, Any]:
    transcript_lines = []
    for message in messages:
        transcript_lines.append(
            f"{message['turn']}. {message['speaker']}[{message['speaker_presence_mode']}]: {message['content']}"
        )
    transcript = "\n".join(transcript_lines)
    known_role_ids = [profile["persona"].role_id for profile in team_profiles]
    recent_event_lines = "\n".join(
        f"- {event['actor']} | {event['artifact_summary']}"
        for event in recent_events[-4:]
    ) or "- 无"

    system_message = (
        "你是内部会话控制器，只服务于生成更自然的学生项目讨论数据。"
        "你需要阅读当前会议文本，并输出一个 JSON 对象，不要输出任何额外解释。"
    )
    user_message = (
        f"请分析下面这场学生项目会议，并返回 JSON。\n\n"
        f"scenario_title: {scenario.title}\n"
        f"meeting_index: {meeting_index}\n"
        f"total_sessions: {total_sessions}\n"
        f"known_role_ids: {known_role_ids}\n"
        f"current_state: {json.dumps(project_state, ensure_ascii=False)}\n"
        f"recent_events: {recent_event_lines}\n"
        f"presence_map: {json.dumps(presence_map, ensure_ascii=False)}\n"
        f"force_project_closure: {force_project_closure}\n"
        f"transcript:\n{transcript}\n\n"
        "JSON schema:\n"
        "{\n"
        '  "session_outcome": "progress_made_and_pause | temporary_stalemate | conflict_breakup | task_completed_for_now",\n'
        '  "should_add_closing_utterance": true,\n'
        '  "closer_role_id": "one role_id from known_role_ids or null",\n'
        '  "carryover_summary": "brief Chinese summary for next meeting context",\n'
        '  "state_delta": {\n'
        '    "decisions_added": ["..."],\n'
        '    "open_issues_changed": ["..."],\n'
        '    "work_updates": ["..."],\n'
        '    "mood_change": "..." \n'
        "  },\n"
        '  "state_after_session": {\n'
        '    "current_goal": "...",\n'
        '    "known_decisions": ["..."],\n'
        '    "open_issues": ["..."],\n'
        '    "assigned_work": ["..."],\n'
        '    "progress_level": "not_started | early_progress | mid_progress | near_completion | completed",\n'
        '    "deadline_pressure": "low | medium | high",\n'
        '    "team_mood": "positive | neutral | tense | frustrated"\n'
        "  },\n"
        '  "project_end_signal": "continue | completed | stalled | abandoned | forced_submission"\n'
        "}\n\n"
        "规则：\n"
        "1. 如果会议文本已经有自然结束感，可以把 should_add_closing_utterance 设为 false。\n"
        "2. 如果最后停得太硬、太突然，或者只有讨论没有收尾，就设为 true，并选择最适合收尾的角色。\n"
        "3. project_end_signal 只有在项目明显完成、明显烂尾、明显拖死或只能被迫交付时才设为终局；否则用 continue。\n"
        "4. 如果 force_project_closure=true，这代表这是项目时间线的最后一次会议，必须从 completed、stalled、abandoned、forced_submission 中选择一个项目级结局，不要继续返回 continue；同时 carryover_summary 要写成最终结局摘要，而不是下一次会议待办。\n"
        "5. 只输出 JSON。"
    )

    reply_text = generate_model_reply(
        autogen=autogen,
        llm_config=llm_config,
        system_message=system_message,
        user_message=user_message,
        agent_name="SessionController",
    )
    payload = parse_json_object(reply_text)
    if payload is None:
        LOGGER.warning("Controller JSON parse failed for %s. Falling back to heuristic analysis.", session_id)
        return fallback_controller_payload(
            messages=messages,
            project_state=project_state,
            meeting_index=meeting_index,
            total_sessions=total_sessions,
        )

    session_outcome = payload.get("session_outcome")
    if session_outcome not in SESSION_OUTCOMES:
        payload["session_outcome"] = "progress_made_and_pause"

    project_end_signal = payload.get("project_end_signal")
    if project_end_signal not in PROJECT_END_SIGNALS:
        payload["project_end_signal"] = "continue"
    if force_project_closure and payload["project_end_signal"] == "continue":
        payload["project_end_signal"] = infer_terminal_project_end_signal(
            messages=messages,
            project_state=payload.get("state_after_session") or project_state,
            session_outcome=payload["session_outcome"],
        )
        payload["should_add_closing_utterance"] = True

    payload["should_add_closing_utterance"] = bool(payload.get("should_add_closing_utterance"))
    payload["closer_role_id"] = payload.get("closer_role_id")
    payload["carryover_summary"] = payload.get("carryover_summary") or "团队有一定进展，但仍有遗留问题待下一次讨论。"
    payload["state_delta"] = payload.get("state_delta") or {
        "decisions_added": [],
        "open_issues_changed": [],
        "work_updates": [],
        "mood_change": "no_clear_change",
    }
    payload["state_after_session"] = refine_state_after_session(
        state=normalize_state_after_session(
            previous_state=project_state,
            raw_state=payload.get("state_after_session", {}),
        ),
        session_outcome=payload["session_outcome"],
    )
    return payload


def fallback_controller_payload(
    messages: list[dict[str, Any]],
    project_state: dict[str, Any],
    meeting_index: int,
    total_sessions: int,
) -> dict[str, Any]:
    full_text = " ".join(message["content"] for message in messages if message["content"])
    has_conflict = any(token in full_text for token in ["别废话", "听我的", "不行", "不可能", "没法做", "吵", "烦"])
    has_progress = any(token in full_text for token in ["我负责", "先做", "上传", "查资料", "我们先", "那我来"])
    has_completion = any(token in full_text for token in ["就这样吧", "先到这", "差不多了", "可以提交", "定了"])
    session_outcome = "temporary_stalemate"
    if has_conflict:
        session_outcome = "conflict_breakup"
    elif has_completion:
        session_outcome = "task_completed_for_now"
    elif has_progress:
        session_outcome = "progress_made_and_pause"

    progress_level = project_state["progress_level"]
    if session_outcome == "progress_made_and_pause" and progress_level == "not_started":
        progress_level = "early_progress"
    elif session_outcome == "task_completed_for_now":
        progress_level = "completed"

    project_end_signal = "continue"
    if session_outcome == "task_completed_for_now":
        project_end_signal = "completed"
    elif meeting_index >= total_sessions:
        project_end_signal = "abandoned" if has_conflict else "stalled"

    return {
        "session_outcome": session_outcome,
        "should_add_closing_utterance": not has_completion,
        "closer_role_id": None,
        "carryover_summary": "上次讨论形成了一些口头共识，但仍有部分问题没有完全收束。",
        "state_delta": {
            "decisions_added": [],
            "open_issues_changed": [],
            "work_updates": [],
            "mood_change": "tense" if has_conflict else "neutral",
        },
        "state_after_session": refine_state_after_session(
            state={
                **deepcopy(project_state),
                "progress_level": progress_level,
                "team_mood": "tense" if has_conflict else project_state["team_mood"],
            },
            session_outcome=session_outcome,
        ),
        "project_end_signal": project_end_signal,
    }


def infer_terminal_project_end_signal(
    messages: list[dict[str, Any]],
    project_state: dict[str, Any],
    session_outcome: str,
) -> str:
    full_text = " ".join(str(message.get("content", "")) for message in messages)
    progress_level = project_state.get("progress_level", "not_started")
    team_mood = project_state.get("team_mood", "neutral")
    decisions = project_state.get("known_decisions", [])
    assigned_work = project_state.get("assigned_work", [])
    has_submission_signal = any(
        token in full_text for token in ["提交", "交上去", "交作业", "最终版", "定稿", "先交", "可以交"]
    )
    has_abandon_signal = any(
        token in full_text for token in ["不做了", "算了", "放弃", "没人管", "做不完", "别搞了"]
    )
    has_conflict_signal = session_outcome in {"temporary_stalemate", "conflict_breakup"} or any(
        token in full_text for token in ["吵", "不行", "别废话", "没法", "谈不拢", "卡住"]
    )

    if progress_level == "completed" or (
        has_submission_signal and (len(decisions) >= 2 or len(assigned_work) >= 2)
    ):
        return "completed"
    if has_abandon_signal or (
        has_conflict_signal
        and team_mood in {"tense", "frustrated"}
        and len(decisions) < 2
    ):
        return "abandoned"
    if len(decisions) >= 2 or len(assigned_work) >= 2 or progress_level in {"mid_progress", "near_completion"}:
        return "forced_submission"
    return "stalled"


def normalize_state_after_session(
    previous_state: dict[str, Any],
    raw_state: dict[str, Any],
) -> dict[str, Any]:
    normalized = deepcopy(previous_state)
    normalized["current_goal"] = raw_state.get("current_goal") or previous_state["current_goal"]
    normalized["known_decisions"] = normalize_string_list(
        raw_state.get("known_decisions"), previous_state["known_decisions"]
    )
    normalized["open_issues"] = normalize_string_list(
        raw_state.get("open_issues"), previous_state["open_issues"]
    )
    normalized["assigned_work"] = normalize_string_list(
        raw_state.get("assigned_work"), previous_state["assigned_work"]
    )
    normalized["progress_level"] = raw_state.get("progress_level") or previous_state["progress_level"]
    normalized["deadline_pressure"] = raw_state.get("deadline_pressure") or previous_state["deadline_pressure"]
    normalized["team_mood"] = raw_state.get("team_mood") or previous_state["team_mood"]
    return normalized


def refine_state_after_session(
    state: dict[str, Any],
    session_outcome: str,
) -> dict[str, Any]:
    refined = deepcopy(state)
    decision_count = len(refined.get("known_decisions", []))
    assigned_count = len(refined.get("assigned_work", []))
    combined_progress_signals = decision_count + assigned_count

    if session_outcome == "task_completed_for_now":
        refined["progress_level"] = "completed"
    elif refined["progress_level"] == "not_started" and combined_progress_signals > 0:
        refined["progress_level"] = "early_progress"
    elif refined["progress_level"] == "early_progress" and combined_progress_signals >= 3:
        refined["progress_level"] = "mid_progress"

    if session_outcome == "conflict_breakup" and refined["team_mood"] == "neutral":
        refined["team_mood"] = "tense"
    elif session_outcome == "progress_made_and_pause" and refined["team_mood"] == "frustrated":
        refined["team_mood"] = "neutral"

    return refined


def normalize_string_list(raw_value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(raw_value, list):
        return deepcopy(fallback)
    values = [str(item).strip() for item in raw_value if str(item).strip()]
    return values or deepcopy(fallback)


def resolve_closer_profile(
    team_profiles: list[dict[str, Any]],
    presence_map: dict[str, str],
    closer_role_id: str | None,
) -> dict[str, Any] | None:
    if closer_role_id:
        for profile in team_profiles:
            if (
                profile["persona"].role_id == closer_role_id
                and presence_map[profile["agent_name"]] != "absent"
            ):
                return profile
    for profile in team_profiles:
        if presence_map[profile["agent_name"]] in PRESENCE_LIVE_MODES:
            return profile
    return None


def generate_closing_message(
    autogen: Any,
    llm_config: dict[str, Any],
    profile: dict[str, Any],
    scenario: ScenarioDefinition,
    session_outcome: str,
    carryover_summary: str,
    project_end_signal: str = "continue",
) -> str:
    system_message = compose_persona_system_message(
        persona=profile["persona"],
        agent_name=profile["agent_name"],
        presence_mode="active",
        offtopic_tendency="medium",
        project_state={"progress_level": "mid_progress", "team_mood": "neutral", "deadline_pressure": "medium"},
    )
    if project_end_signal == "continue":
        closure_instruction = "这不是项目最终结局，只需要自然结束本次会议，并留下下一次继续推进的口径。"
    else:
        closure_instruction = (
            f"这是项目时间线的最后一次会议，项目级结局是 {project_end_signal}。"
            "你的收尾必须明确表达这个结局，例如完成提交、被迫先交、谈崩放弃、或暂时无结果收场；不要再说“下次继续”。"
        )
    user_message = (
        f"你需要作为 {profile['agent_name']} 用一条简短、自然、口语化的中文消息结束这次学生项目讨论。\n"
        f"项目：{scenario.title}\n"
        f"本次结果：{session_outcome}\n"
        f"项目级结局信号：{project_end_signal}\n"
        f"摘要：{carryover_summary}\n"
        f"{closure_instruction}\n"
        "要求：\n"
        "1. 只写一条群聊消息，不要解释。\n"
        "2. 不要输出任何标记、标题、项目符号或 JSON。\n"
        "3. 像真实学生一样说话，例如“那就先按这个版本交了”“算了，今晚先交能交的”“这个项目我们就到这里吧”。"
    )
    reply_text = generate_model_reply(
        autogen=autogen,
        llm_config=llm_config,
        system_message=system_message,
        user_message=user_message,
        agent_name="ClosingMessageAgent",
    ).strip()
    return strip_internal_end_token(reply_text) or "那今天先到这吧，剩下的我们晚点再接着推进。"


def compose_async_followup_message(persona: PersonaRole, project_state: dict[str, Any]) -> str:
    if persona.role_id == "implementer_worker":
        return "我刚补看了聊天记录，今晚先把能动手的那部分推进一下，明天再同步进度。"
    if persona.role_id == "evaluator_critic":
        return "我晚点把今天定下来的思路再过一遍，如果有明显漏洞我再在群里提。"
    if persona.role_id == "free_rider":
        return "我刚看到消息，辛苦大家了，后面有需要我再跟。"
    if persona.role_id == "dominator":
        return "我看完记录了，后面别再改来改去，先按今天这个方向往下做。"
    if project_state["deadline_pressure"] == "high":
        return "我刚补看了记录，先别再拖了，今晚能补的我尽量补上。"
    return "我刚补看了聊天记录，先按你们刚才定的方向走，后面有更新我再接。"


def build_artifacts_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    artifacts_by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        artifact_id = event.get("artifact_id") or event.get("artifact_name")
        if not artifact_id:
            continue
        if artifact_id not in artifacts_by_id:
            artifacts_by_id[artifact_id] = {
                "artifact_id": artifact_id,
                "artifact_name": event.get("artifact_name"),
                "artifact_type": event.get("artifact_type", "project_artifact"),
                "artifact_version": event.get("artifact_version", 1),
                "artifact_status": event.get("artifact_status") or event.get("status", "mentioned"),
                "artifact_owner": event.get("artifact_owner") or event.get("actor"),
                "artifact_summary": event.get("artifact_summary", ""),
                "artifact_history": [],
            }
        artifact = artifacts_by_id[artifact_id]
        artifact["artifact_version"] = max(
            int(artifact.get("artifact_version", 1)),
            int(event.get("artifact_version", 1)),
        )
        artifact["artifact_status"] = event.get("artifact_status") or event.get("status", artifact["artifact_status"])
        artifact["artifact_history"].append(
            {
                "event_id": event.get("event_id"),
                "session_id": event.get("session_id"),
                "actor": event.get("actor"),
                "event_type": event.get("event_type"),
                "status": event.get("status"),
                "summary": event.get("artifact_summary"),
            }
        )
    return list(artifacts_by_id.values())


def build_project_quality_diagnostics(
    project_id: str,
    sessions: list[dict[str, Any]],
    project_events: list[dict[str, Any]],
    project_state_history: list[dict[str, Any]],
    project_outcome: str,
    team_profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    team_names = [profile["agent_name"] for profile in team_profiles]
    session_diagnostics = [
        build_session_quality_diagnostics(session=session, team_names=team_names)
        for session in sessions
    ]
    outcome_counts: dict[str, int] = {}
    for session in sessions:
        outcome = session.get("session_outcome", "unknown")
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

    final_state = project_state_history[-1] if project_state_history else {}
    decisions = final_state.get("known_decisions", [])
    assigned_work = final_state.get("assigned_work", [])
    outcome_contradiction = (
        project_outcome == "stalled"
        and (len(decisions) >= 4 or len(assigned_work) >= 3)
        and final_state.get("deadline_pressure") == "high"
    )
    warnings = []
    if outcome_contradiction:
        warnings.append("项目被判定为 stalled，但已有较多决策/分工且 deadline 压力较高，可能应考虑 forced_submission 或 completed。")
    if sessions and len(outcome_counts) == 1:
        warnings.append("所有 session_outcome 完全相同，结局类型多样性不足。")
    if sessions and len(project_events) < max(1, len(sessions) // 2):
        warnings.append("事件数量偏低，可能漏掉了学生操作。")
    warnings.extend(
        f"第 {item['meeting_index']} 次对话：{warning}"
        for item in session_diagnostics
        for warning in item["warnings"]
    )

    return {
        "project_id": project_id,
        "project_outcome": project_outcome,
        "session_count": len(sessions),
        "event_count": len(project_events),
        "artifact_count": len(build_artifacts_from_events(project_events)),
        "session_outcome_counts": outcome_counts,
        "final_decision_count": len(decisions),
        "final_assigned_work_count": len(assigned_work),
        "outcome_contradiction": outcome_contradiction,
        "warnings": warnings,
        "sessions": session_diagnostics,
    }


def build_session_quality_diagnostics(session: dict[str, Any], team_names: list[str]) -> dict[str, Any]:
    messages = session.get("messages", [])
    counts: dict[str, int] = {}
    pseudo_multi_speaker_messages = []
    previous_normalized = None
    repeated_turns = 0
    for message in messages:
        speaker = message.get("speaker", "unknown")
        counts[speaker] = counts.get(speaker, 0) + 1
        content = str(message.get("content", ""))
        if contains_other_speaker_label(content, speaker, team_names):
            pseudo_multi_speaker_messages.append(message.get("turn"))
        normalized = normalize_message_for_quality(content)
        if normalized and previous_normalized == normalized:
            repeated_turns += 1
        previous_normalized = normalized

    total = sum(counts.values())
    dominant_count = max(counts.values()) if counts else 0
    dominance_ratio = round(dominant_count / total, 3) if total else 0.0
    warnings = []
    if dominance_ratio >= 0.55 and total >= 6:
        warnings.append("单个成员发言占比过高。")
    if len(counts) < 3:
        warnings.append("有效参与成员少于 3 人。")
    if pseudo_multi_speaker_messages:
        warnings.append("疑似出现一名 agent 替多人说话的伪对话格式。")
    if repeated_turns:
        warnings.append("存在相邻重复或近似重复发言。")
    if total < 8:
        warnings.append("消息数偏少，讨论可能过浅。")

    speaker_selection_policy = session.get("speaker_selection_policy", "unknown")
    interruption_like_turns = session.get("interruption_like_turns", [])
    silence_stop_used = bool(session.get("silence_stop_used", False))
    if speaker_selection_policy == "urgency_queue":
        if silence_stop_used and total < 6:
            warnings.append("urgency_queue 过早使用低紧迫度停止，可能导致讨论不足。")
        if not interruption_like_turns and total >= 8:
            warnings.append("urgency_queue 未检测到抢话/插话式 turn，高冲突组可能未充分体现。")

    return {
        "session_id": session.get("session_id"),
        "meeting_index": session.get("meeting_index"),
        "message_count": total,
        "speaker_message_counts": counts,
        "dominance_ratio": dominance_ratio,
        "event_count": len(session.get("events", [])),
        "session_outcome": session.get("session_outcome"),
        "pseudo_multi_speaker_turns": pseudo_multi_speaker_messages,
        "repeated_turn_count": repeated_turns,
        "speaker_selection_policy": speaker_selection_policy,
        "interruption_like_turns": interruption_like_turns,
        "silence_stop_used": silence_stop_used,
        "speaker_selection_trace_count": len(session.get("speaker_selection_trace", [])),
        "warnings": warnings,
    }


def contains_other_speaker_label(content: str, speaker: str, team_names: list[str]) -> bool:
    for name in team_names:
        if name == speaker:
            continue
        if re.search(rf"(^|\n|\s){re.escape(name)}\s*[:：]", content):
            return True
    return False


def normalize_message_for_quality(content: str) -> str:
    normalized = re.sub(r"\s+", "", content)
    normalized = re.sub(r"[，。！？,.!?：:；;、]", "", normalized)
    return normalized[:80]


def build_dataset_quality_diagnostics(dataset: dict[str, Any]) -> dict[str, Any]:
    projects = dataset.get("projects", [])
    project_diagnostics = [
        project.get("quality_diagnostics") or build_project_quality_diagnostics(
            project_id=project.get("project_id", "unknown"),
            sessions=project.get("sessions", []),
            project_events=project.get("events", []),
            project_state_history=project.get("project_state_history", []),
            project_outcome=project.get("project_outcome", "unknown"),
            team_profiles=[
                {"agent_name": member.get("agent_name", member.get("name", "unknown"))}
                for member in project.get("team_members", [])
            ],
        )
        for project in projects
    ]
    warnings = [
        warning
        for project in project_diagnostics
        for warning in project.get("warnings", [])
    ]
    return {
        "dataset_name": dataset.get("dataset_name"),
        "status": dataset.get("status"),
        "project_count": len(projects),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_session_count": sum(project.get("session_count", 0) for project in project_diagnostics),
        "total_event_count": sum(project.get("event_count", 0) for project in project_diagnostics),
        "warning_count": len(warnings),
        "warnings": warnings,
        "projects": project_diagnostics,
    }


def format_quality_report_markdown(diagnostics: dict[str, Any]) -> str:
    lines = [
        "# 生成质量诊断报告",
        "",
        "本报告只用于调试对话生成质量，不是学生表现评估标签。",
        "",
        f"- 数据集：{diagnostics.get('dataset_name')}",
        f"- 运行状态：{diagnostics.get('status')}",
        f"- 项目数：{diagnostics.get('project_count')}",
        f"- session 数：{diagnostics.get('total_session_count')}",
        f"- 事件数：{diagnostics.get('total_event_count')}",
        f"- 警告数：{diagnostics.get('warning_count')}",
        "",
        "## 主要警告",
        "",
    ]
    warnings = diagnostics.get("warnings", [])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings[:30])
    else:
        lines.append("- 暂无明显质量警告。")

    lines.extend(["", "## 项目明细", ""])
    for project in diagnostics.get("projects", []):
        lines.extend(
            [
                f"### {project.get('project_id')}",
                "",
                f"- 项目结局：{project.get('project_outcome')}",
                f"- session 数：{project.get('session_count')}",
                f"- 事件数：{project.get('event_count')}",
                f"- artifact 数：{project.get('artifact_count')}",
                f"- session_outcome 分布：{project.get('session_outcome_counts')}",
                "",
            ]
        )
        for session in project.get("sessions", []):
            lines.append(
                f"- 第 {session.get('meeting_index')} 次：messages={session.get('message_count')}, "
                f"speakers={session.get('speaker_message_counts')}, "
                f"dominance={session.get('dominance_ratio')}, events={session.get('event_count')}, "
                f"policy={session.get('speaker_selection_policy')}, "
                f"interruptions={session.get('interruption_like_turns')}, "
                f"silence_stop={session.get('silence_stop_used')}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def finalize_project_outcome(project_state: dict[str, Any], sessions: list[dict[str, Any]]) -> str:
    if not sessions:
        return "abandoned"
    progress_level = project_state.get("progress_level", "not_started")
    team_mood = project_state.get("team_mood", "neutral")
    decisions = project_state.get("known_decisions", [])
    assigned_work = project_state.get("assigned_work", [])
    deadline_pressure = project_state.get("deadline_pressure")
    recent_text = " ".join(
        message.get("content", "")
        for session in sessions[-2:]
        for message in session.get("messages", [])
    )
    has_submission_signal = any(
        token in recent_text for token in ["提交", "交上去", "可以交", "最终版", "定稿", "先交"]
    )
    has_abandon_signal = any(
        token in recent_text for token in ["不做了", "算了", "放弃", "没人管", "做不完", "别搞了"]
    )
    if progress_level == "completed":
        return "completed"
    if has_submission_signal and len(decisions) >= 2:
        return "completed"
    if has_abandon_signal or (
        team_mood in {"tense", "frustrated"} and progress_level in {"not_started", "early_progress"} and len(decisions) < 2
    ):
        return "abandoned"
    if deadline_pressure == "high" and (
        progress_level == "near_completion"
        or len(decisions) >= 4
        or len(assigned_work) >= 3
    ):
        return "forced_submission"
    return "stalled"


def generate_model_reply(
    autogen: Any,
    llm_config: dict[str, Any],
    system_message: str,
    user_message: str,
    agent_name: str,
) -> str:
    agent = autogen.AssistantAgent(
        name=agent_name,
        system_message=system_message,
        llm_config=deepcopy(llm_config),
        code_execution_config=False,
        human_input_mode="NEVER",
    )
    reply = agent.generate_reply(messages=[{"role": "user", "content": user_message}], sender=None)
    if isinstance(reply, dict):
        content = reply.get("content", "")
    else:
        content = reply or ""
    return str(content)


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    if not raw_text:
        return None
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def select_groups(
    experiment: ExperimentDefinition,
    only_groups: set[str] | None = None,
) -> list[GroupDefinition]:
    if only_groups:
        return [group for group in experiment.groups if group.group_id in only_groups]
    return [group for group in experiment.groups if "smoke_test" not in group.tags]


def compose_turn_taking_instruction(role_id: str) -> str:
    role_note = {
        "dominator": "你更容易抢话或打断别人，但仍然只能代表自己发言。",
        "blocker": "当团队推进太快或你觉得方案不可靠时，你会更容易插话反对。",
        "gatekeeper_expediter": "当话题跑偏、deadline 逼近或分工不清时，你会主动插话拉回进度。",
        "harmonizer": "当出现冲突、否定或情绪紧张时，你会主动介入缓和。",
        "free_rider": "除非被点名或需要敷衍回应，否则你通常少说、短说。",
        "lone_wolf": "你可能突然插入自己的方案，但不应该代替别人说话。",
    }.get(role_id, "你可以在有真实理由时自然插话、回应或保持沉默。")
    return (
        "自发发言规则：你不需要每一轮都长篇发言；如果别人刚说完但你强烈不同意、被点名、发现风险、"
        "或想抢回节奏，可以用很短的一句话插入。"
        f"{role_note}"
        "不要写成会议纪要，不要在一条消息里模拟多名成员发言。"
    )


def _build_assistant_agent(
    autogen: Any,
    profile: dict[str, Any],
    llm_config: dict[str, Any],
    presence_mode: str,
    offtopic_tendency: str,
    project_state: dict[str, Any],
) -> Any:
    persona: PersonaRole = profile["persona"]
    agent_kwargs = {
        "name": profile["agent_name"],
        "system_message": (
            compose_persona_system_message(
                persona=persona,
                agent_name=profile["agent_name"],
                presence_mode=presence_mode,
                offtopic_tendency=offtopic_tendency,
                project_state=project_state,
            )
            + "\n"
            + compose_turn_taking_instruction(persona.role_id)
        ),
        "llm_config": deepcopy(llm_config),
        "is_termination_msg": _is_termination_message,
    }
    try:
        return autogen.AssistantAgent(description=persona.description, **agent_kwargs)
    except TypeError:
        return autogen.AssistantAgent(**agent_kwargs)


def _build_groupchat_manager(
    autogen: Any,
    groupchat: Any,
    llm_config: dict[str, Any],
    system_message: str,
) -> Any:
    manager_kwargs = {
        "groupchat": groupchat,
        "llm_config": deepcopy(llm_config),
        "is_termination_msg": _is_termination_message,
    }
    try:
        return autogen.GroupChatManager(system_message=system_message, **manager_kwargs)
    except TypeError:
        return autogen.GroupChatManager(**manager_kwargs)


def _is_termination_message(message: dict[str, Any]) -> bool:
    content = message.get("content", "")
    if isinstance(content, list):
        content = json.dumps(content, ensure_ascii=False)
    return message_has_internal_end_token(str(content))
