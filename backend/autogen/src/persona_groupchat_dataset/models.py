from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PersonaRole:
    role_id: str
    name: str
    category: str
    description: str
    system_message: str


@dataclass(frozen=True)
class GroupDefinition:
    group_id: str
    member_role_ids: list[str]
    task: str | None = None
    repeats: int = 1
    max_round: int | None = None
    speaker_selection_method: str | None = None
    allow_repeat_speaker: bool | None = None
    temperature: float | None = None
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 4 <= len(self.member_role_ids) <= 5:
            raise ValueError(
                f"Group '{self.group_id}' must contain 4-5 members, got {len(self.member_role_ids)}."
            )
        if self.repeats < 1:
            raise ValueError(f"Group '{self.group_id}' repeats must be >= 1.")


@dataclass(frozen=True)
class ExperimentDefinition:
    dataset_name: str
    description: str
    default_task: str
    output_prefix: str
    manager_system_message: str
    default_groupchat: dict[str, Any]
    groups: list[GroupDefinition]
    source_path: Path

    def validate(self) -> None:
        seen_group_ids: set[str] = set()
        for group in self.groups:
            if group.group_id in seen_group_ids:
                raise ValueError(f"Duplicate group_id found: {group.group_id}")
            group.validate()
            seen_group_ids.add(group.group_id)
