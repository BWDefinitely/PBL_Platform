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
class ScenarioDefinition:
    scenario_id: str
    title: str
    task_type: str
    course_context: str
    deliverable_type: str
    deadline_span: str
    difficulty: str
    artifact_types: list[str] = field(default_factory=list)
    project_brief: str = ""
    initial_context: str = ""
    common_operations: list[str] = field(default_factory=list)
    conflict_points: list[str] = field(default_factory=list)
    natural_endings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id must not be empty.")
        if not self.title:
            raise ValueError(f"Scenario '{self.scenario_id}' must define a title.")


@dataclass(frozen=True)
class GroupDefinition:
    group_id: str
    member_role_ids: list[str]
    scenario_id: str | None = None
    task: str | None = None
    repeats: int = 1
    max_round: int | None = None
    speaker_selection_method: str | None = None
    allow_repeat_speaker: bool | None = None
    temperature: float | None = None
    tags: list[str] = field(default_factory=list)
    session_count_range: tuple[int, int] = (1, 1)
    offtopic_tendency: str = "medium"
    attendance_variability: str = "low"
    deadline_pressure_curve: str = "steady"
    turn_taking: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not 4 <= len(self.member_role_ids) <= 5:
            raise ValueError(
                f"Group '{self.group_id}' must contain 4-5 members, got {len(self.member_role_ids)}."
            )
        if self.repeats < 1:
            raise ValueError(f"Group '{self.group_id}' repeats must be >= 1.")
        session_min, session_max = self.session_count_range
        if session_min < 1 or session_max < session_min:
            raise ValueError(
                f"Group '{self.group_id}' has invalid session_count_range: {self.session_count_range}"
            )
        if not self.scenario_id and not self.task:
            raise ValueError(
                f"Group '{self.group_id}' must define either scenario_id or task."
            )


@dataclass(frozen=True)
class GenerationSettings:
    min_effective_messages: int = 8
    min_participating_speakers: int = 3
    repair_max_rounds: int = 2
    enable_closer: bool = True
    enable_event_controller: bool = False
    enable_quality_diagnostics: bool = True
    session_timeout_seconds: int = 120
    incremental_conversation_timeline: bool = True
    min_project_sessions_before_terminal: int = 4
    force_project_closure_on_final_session: bool = True


@dataclass(frozen=True)
class ExperimentDefinition:
    dataset_name: str
    description: str
    output_prefix: str
    manager_system_message: str
    default_groupchat: dict[str, Any]
    groups: list[GroupDefinition]
    source_path: Path
    default_task: str | None = None
    schema_version: str = "project_timeline_v2"
    generation_settings: GenerationSettings = field(default_factory=GenerationSettings)

    def validate(self) -> None:
        seen_group_ids: set[str] = set()
        for group in self.groups:
            if group.group_id in seen_group_ids:
                raise ValueError(f"Duplicate group_id found: {group.group_id}")
            group.validate()
            seen_group_ids.add(group.group_id)
