from __future__ import annotations

import json
import logging
import os
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .models import ExperimentDefinition, GroupDefinition, PersonaRole

LOGGER = logging.getLogger(__name__)
TERMINATION_TOKEN = "[GROUP_COMPLETE]"
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


@dataclass(frozen=True)
class RunArtifacts:
    run_dir: Path
    dialogue_jsonl_path: Path
    state_path: Path
    final_dataset_path: Path
    metadata_path: Path
    log_path: Path


def resolve_model_config_list(
    config_list_file: str | None,
    model: str | None,
    api_key_env: str,
    base_url: str | None,
) -> list[dict[str, Any]]:
    if config_list_file:
        config_path = Path(config_list_file)
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            payload = (
                payload.get("dialogue")
                or payload.get("dialogue_config_list")
                or payload.get("default")
                or payload.get("config_list")
            )
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


def create_run_artifacts(output_dir: str | Path, output_prefix: str) -> RunArtifacts:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = target_dir / f"{output_prefix}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunArtifacts(
        run_dir=run_dir,
        dialogue_jsonl_path=run_dir / "dialogues.jsonl",
        state_path=run_dir / "state.json",
        final_dataset_path=run_dir / "final_dataset.json",
        metadata_path=run_dir / "metadata.json",
        log_path=run_dir / "run.log",
    )


def create_dataset_skeleton(
    experiment: ExperimentDefinition,
    config_list: list[dict[str, Any]],
    only_groups: set[str] | None,
    persona_source: str | Path,
    artifacts: RunArtifacts,
) -> dict[str, Any]:
    selected_group_ids = [group.group_id for group in select_groups(experiment, only_groups)]
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "dataset_name": experiment.dataset_name,
        "description": experiment.description,
        "generated_at": now,
        "updated_at": now,
        "status": "running",
        "persona_source": str(persona_source),
        "experiment_source": str(experiment.source_path),
        "model_config_summary": summarize_model_config(config_list),
        "selected_group_ids": selected_group_ids,
        "termination_token": TERMINATION_TOKEN,
        "run_directory": str(artifacts.run_dir),
        "dialogues": [],
    }


def write_run_metadata(
    artifacts: RunArtifacts,
    experiment: ExperimentDefinition,
    config_list: list[dict[str, Any]],
    only_groups: set[str] | None,
) -> None:
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_name": experiment.dataset_name,
        "experiment_source": str(experiment.source_path),
        "selected_group_ids": [group.group_id for group in select_groups(experiment, only_groups)],
        "model_config_summary": summarize_model_config(config_list),
        "artifacts": {
            "dialogues_jsonl": str(artifacts.dialogue_jsonl_path),
            "state_json": str(artifacts.state_path),
            "final_dataset_json": str(artifacts.final_dataset_path),
            "log_file": str(artifacts.log_path),
        },
    }
    artifacts.metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_dialogue_checkpoint(artifacts: RunArtifacts, dialogue: dict[str, Any]) -> None:
    with artifacts.dialogue_jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dialogue, ensure_ascii=False))
        handle.write("\n")


def write_dataset_state(dataset: dict[str, Any], path: str | Path) -> Path:
    dataset["updated_at"] = datetime.now().isoformat(timespec="seconds")
    target_path = Path(path)
    target_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_path


def iter_dialogues(
    personas: dict[str, PersonaRole],
    experiment: ExperimentDefinition,
    config_list: list[dict[str, Any]],
    cache_seed: int,
    only_groups: set[str] | None = None,
) -> Iterator[dict[str, Any]]:
    selected_groups = select_groups(experiment, only_groups)
    if not selected_groups:
        raise ValueError("No groups selected to run.")

    for group in selected_groups:
        members = [personas[role_id] for role_id in group.member_role_ids]
        for run_index in range(1, group.repeats + 1):
            yield run_single_dialogue(
                members=members,
                group=group,
                experiment=experiment,
                config_list=config_list,
                cache_seed=cache_seed + run_index - 1,
                run_index=run_index,
            )


def run_single_dialogue(
    members: list[PersonaRole],
    group: GroupDefinition,
    experiment: ExperimentDefinition,
    config_list: list[dict[str, Any]],
    cache_seed: int,
    run_index: int,
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
        group.temperature if group.temperature is not None else group_defaults.get("temperature", 0.7)
    )
    task = compose_task_prompt(group.task or experiment.default_task, max_round)

    llm_config = {
        "config_list": deepcopy(config_list),
        "cache_seed": cache_seed,
        "temperature": temperature,
        "timeout": 120,
    }

    agent_profiles = build_agent_profiles(members)
    agents = [_build_assistant_agent(autogen, profile, llm_config) for profile in agent_profiles]

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
        system_message=compose_manager_system_message(experiment.manager_system_message, max_round),
    )

    task_host = autogen.UserProxyAgent(
        name="TaskHost",
        human_input_mode="NEVER",
        code_execution_config=False,
        llm_config=False,
    )

    LOGGER.info(
        "Starting dialogue %s run=%s members=%s",
        group.group_id,
        run_index,
        [profile["agent_name"] for profile in agent_profiles],
    )
    try:
        task_host.initiate_chat(manager, message=task, clear_history=True)
    except TypeError:
        task_host.initiate_chat(manager, message=task)

    name_to_profile = {profile["agent_name"]: profile for profile in agent_profiles}
    messages = [
        serialize_message(idx, message, name_to_profile)
        for idx, message in enumerate(groupchat.messages, start=1)
    ]
    termination_reason = detect_termination_reason(messages, max_round)

    LOGGER.info(
        "Finished dialogue %s run=%s messages=%s termination=%s",
        group.group_id,
        run_index,
        len(messages),
        termination_reason,
    )

    return {
        "dialogue_id": f"{group.group_id}__run_{run_index:02d}",
        "group_id": group.group_id,
        "run_index": run_index,
        "task": task,
        "group_tags": group.tags or group_defaults.get("tags", []),
        "member_count": len(members),
        "members": [
            {
                **asdict(profile["persona"]),
                "agent_name": profile["agent_name"],
                "display_name": profile["display_name"],
            }
            for profile in agent_profiles
        ],
        "speaker_selection_method": speaker_selection_method,
        "allow_repeat_speaker": allow_repeat_speaker,
        "max_round": max_round,
        "messages": messages,
        "message_count": len(messages),
        "termination_reason": termination_reason,
        "termination_token": TERMINATION_TOKEN,
        "completed_naturally": termination_reason == "group_complete_token",
    }


def serialize_message(
    turn_index: int,
    message: dict[str, Any],
    name_to_profile: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    speaker = message.get("name") or message.get("role") or "unknown"
    content = message.get("content", "")
    if isinstance(content, list):
        content = json.dumps(content, ensure_ascii=False)
    elif content is None:
        content = ""

    profile = name_to_profile.get(speaker)
    return {
        "turn": turn_index,
        "speaker": speaker,
        "display_name": profile["display_name"] if profile else speaker,
        "role_id": profile["persona"].role_id if profile else None,
        "persona_name": profile["persona"].name if profile else None,
        "content": str(content),
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


def compose_task_prompt(task: str, max_round: int) -> str:
    return (
        f"{task}\n\n"
        "额外要求：\n"
        "1. 每位成员每次发言尽量控制在 1-3 句，避免重复之前已经说过的话。\n"
        "2. 如果团队已经基本达成一致，请尽快进入总结，而不是继续寒暄或重复表态。\n"
        f"3. 最迟请在 {max_round} 轮内收束讨论。\n"
        f"4. 当方案已经成型时，由任意一位成员给出简短总结，并在最后单独输出 {TERMINATION_TOKEN} 作为结束标记。"
    )


def compose_manager_system_message(system_message: str, max_round: int) -> str:
    return (
        f"{system_message}\n"
        "你必须主动抑制空转、重复、客套和废话。\n"
        "当讨论已经覆盖目标用户、核心功能、最小可行版本和分工建议后，优先选择一位最适合总结的成员发言。\n"
        f"如果群聊接近第 {max_round} 轮仍未收束，请引导成员直接总结，并用 {TERMINATION_TOKEN} 结束。"
    )


def compose_persona_system_message(persona: PersonaRole, agent_name: str) -> str:
    return (
        f"{persona.system_message}\n"
        f"你在本轮群聊中的公开名字是 {agent_name}。\n"
        "请保持角色特征，但发言务必简洁、具体，避免重复别人已经说过的内容。\n"
        f"当团队已经形成可执行结论时，请支持收束；如果你负责总结，请在最后单独输出 {TERMINATION_TOKEN}。"
    )


def detect_termination_reason(messages: list[dict[str, Any]], max_round: int) -> str:
    if any(message_has_termination_token(message["content"]) for message in messages):
        return "group_complete_token"
    if len(messages) >= max_round + 1:
        return "max_round_reached"
    return "stopped_without_token"


def select_groups(
    experiment: ExperimentDefinition,
    only_groups: set[str] | None = None,
) -> list[GroupDefinition]:
    return [group for group in experiment.groups if not only_groups or group.group_id in only_groups]


def _build_assistant_agent(autogen: Any, profile: dict[str, Any], llm_config: dict[str, Any]) -> Any:
    persona: PersonaRole = profile["persona"]
    agent_kwargs = {
        "name": profile["agent_name"],
        "system_message": compose_persona_system_message(persona, profile["agent_name"]),
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
    return message_has_termination_token(str(content))


def message_has_termination_token(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return False
    if stripped == TERMINATION_TOKEN:
        return True
    last_line = stripped.splitlines()[-1].strip()
    return last_line == TERMINATION_TOKEN
