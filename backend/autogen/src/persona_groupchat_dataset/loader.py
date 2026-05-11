from __future__ import annotations

import json
from pathlib import Path

from .models import ExperimentDefinition, GroupDefinition, PersonaRole


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


def load_experiment_config(config_path: str | Path) -> ExperimentDefinition:
    path = Path(config_path)
    payload = _read_json(path)

    groups = [
        GroupDefinition(
            group_id=group["group_id"],
            member_role_ids=group["member_role_ids"],
            task=group.get("task"),
            repeats=group.get("repeats", 1),
            max_round=group.get("max_round"),
            speaker_selection_method=group.get("speaker_selection_method"),
            allow_repeat_speaker=group.get("allow_repeat_speaker"),
            temperature=group.get("temperature"),
            tags=group.get("tags", []),
        )
        for group in payload.get("groups", [])
    ]

    experiment = ExperimentDefinition(
        dataset_name=payload["dataset_name"],
        description=payload.get("description", ""),
        default_task=payload["default_task"],
        output_prefix=payload.get("output_prefix", "persona_groupchat_dataset"),
        manager_system_message=payload.get(
            "manager_system_message",
            "You are the conversation manager for a task-focused group chat.",
        ),
        default_groupchat=payload.get("default_groupchat", {}),
        groups=groups,
        source_path=path,
    )
    experiment.validate()
    return experiment
