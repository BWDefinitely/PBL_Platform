from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    ExperimentDefinition,
    GenerationSettings,
    GroupDefinition,
    PersonaRole,
    ScenarioDefinition,
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_personas(persona_path: str | Path) -> dict[str, PersonaRole]:
    path = Path(persona_path)
    payload = _read_json(path)
    roles = payload.get("roles", [])
    if not roles:
        raise ValueError(f"No roles found in {path}.")

    persona_map: dict[str, PersonaRole] = {}
    for role in roles:
        persona = PersonaRole(
            role_id=role["role_id"],
            name=role["name"],
            category=role["category"],
            description=role["description"],
            system_message=role["system_message"],
        )
        if persona.role_id in persona_map:
            raise ValueError(f"Duplicate persona role_id found: {persona.role_id}")
        persona_map[persona.role_id] = persona

    return persona_map


def load_scenarios(config_path: str | Path) -> dict[str, ScenarioDefinition]:
    path = Path(config_path)
    payload = _read_json(path)
    scenarios = payload.get("scenarios", [])
    if not scenarios:
        raise ValueError(f"No scenarios found in {path}.")

    scenario_map: dict[str, ScenarioDefinition] = {}
    for item in scenarios:
        scenario = ScenarioDefinition(
            scenario_id=item["scenario_id"],
            title=item["title"],
            task_type=item["task_type"],
            course_context=item["course_context"],
            deliverable_type=item["deliverable_type"],
            deadline_span=item["deadline_span"],
            difficulty=item["difficulty"],
            artifact_types=item.get("artifact_types", []),
            project_brief=item.get("project_brief", ""),
            initial_context=item.get("initial_context", ""),
            common_operations=item.get("common_operations", []),
            conflict_points=item.get("conflict_points", []),
            natural_endings=item.get("natural_endings", []),
        )
        scenario.validate()
        if scenario.scenario_id in scenario_map:
            raise ValueError(f"Duplicate scenario_id found: {scenario.scenario_id}")
        scenario_map[scenario.scenario_id] = scenario

    return scenario_map


def load_experiment_config(config_path: str | Path) -> ExperimentDefinition:
    path = Path(config_path)
    payload = _resolve_experiment_payload(_read_json(path), source=path)
    group_defaults_override = payload.pop("group_defaults_override", None)

    raw_groups = [
        _merge_group_definition_fields(group, group_defaults_override)
        for group in payload.get("groups", [])
    ]

    groups = [
        GroupDefinition(
            group_id=group["group_id"],
            member_role_ids=group["member_role_ids"],
            scenario_id=group.get("scenario_id"),
            task=group.get("task"),
            repeats=group.get("repeats", 1),
            max_round=group.get("max_round"),
            speaker_selection_method=group.get("speaker_selection_method"),
            allow_repeat_speaker=group.get("allow_repeat_speaker"),
            temperature=group.get("temperature"),
            tags=group.get("tags", []),
            session_count_range=_normalize_session_count_range(
                group.get("session_count_range"),
                has_scenario=bool(group.get("scenario_id")),
            ),
            offtopic_tendency=group.get("offtopic_tendency", "medium"),
            attendance_variability=group.get("attendance_variability", "low"),
            deadline_pressure_curve=group.get("deadline_pressure_curve", "steady"),
            turn_taking=group.get("turn_taking", {}),
        )
        for group in raw_groups
    ]

    experiment = ExperimentDefinition(
        dataset_name=payload["dataset_name"],
        description=payload.get("description", ""),
        output_prefix=payload.get("output_prefix", "persona_project_timeline_dataset"),
        manager_system_message=payload.get(
            "manager_system_message",
            "You are the conversation manager for a natural student team discussion.",
        ),
        default_groupchat=payload.get("default_groupchat", {}),
        groups=groups,
        source_path=path,
        default_task=payload.get("default_task"),
        schema_version=payload.get("schema_version", "project_timeline_v2"),
        generation_settings=_load_generation_settings(payload.get("generation_settings", {})),
    )
    experiment.validate()
    return experiment


def _resolve_experiment_payload(payload: Any, source: Path) -> dict:
    if not isinstance(payload, dict):
        raise ValueError(f"{source} must contain a JSON object.")

    extends = payload.get("extends")
    if not extends:
        return payload

    base_path = Path(extends)
    if not base_path.is_absolute():
        base_path = (source.parent / base_path).resolve()
    base_payload = _resolve_experiment_payload(_read_json(base_path), source=base_path)

    merged = dict(base_payload)
    for key, value in payload.items():
        if key == "extends":
            continue
        if key == "default_groupchat" and isinstance(value, dict):
            merged[key] = {**base_payload.get(key, {}), **value}
        elif key == "generation_settings" and isinstance(value, dict):
            merged[key] = {**base_payload.get(key, {}), **value}
        elif key == "group_defaults_override" and isinstance(value, dict):
            merged[key] = value
        else:
            merged[key] = value
    return merged


def _merge_group_definition_fields(
    group: dict,
    group_defaults_override: dict | None,
) -> dict:
    if not group_defaults_override:
        return group

    merged = dict(group)
    for key, value in group_defaults_override.items():
        if key == "turn_taking" and isinstance(value, dict):
            merged[key] = {**group.get("turn_taking", {}), **value}
        elif key == "tags" and isinstance(value, list):
            existing_tags = list(group.get("tags", []))
            merged[key] = sorted({*existing_tags, *value})
        else:
            merged[key] = value
    return merged


def _normalize_session_count_range(
    raw_value: list[int] | tuple[int, int] | int | None,
    has_scenario: bool,
) -> tuple[int, int]:
    if raw_value is None:
        return (3, 5) if has_scenario else (1, 1)

    if isinstance(raw_value, int):
        return (raw_value, raw_value)

    if isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
        session_min = int(raw_value[0])
        session_max = int(raw_value[1])
        return (session_min, session_max)

    raise ValueError(f"Invalid session_count_range: {raw_value}")


def _load_generation_settings(raw_value: dict | None) -> GenerationSettings:
    raw = raw_value or {}
    return GenerationSettings(
        min_effective_messages=int(raw.get("min_effective_messages", 8)),
        min_participating_speakers=int(raw.get("min_participating_speakers", 3)),
        repair_max_rounds=int(raw.get("repair_max_rounds", 2)),
        enable_closer=bool(raw.get("enable_closer", True)),
        enable_event_controller=bool(raw.get("enable_event_controller", False)),
        enable_quality_diagnostics=bool(raw.get("enable_quality_diagnostics", True)),
        session_timeout_seconds=int(raw.get("session_timeout_seconds", 120)),
        incremental_conversation_timeline=bool(raw.get("incremental_conversation_timeline", True)),
        min_project_sessions_before_terminal=int(raw.get("min_project_sessions_before_terminal", 4)),
        force_project_closure_on_final_session=bool(raw.get("force_project_closure_on_final_session", True)),
    )
