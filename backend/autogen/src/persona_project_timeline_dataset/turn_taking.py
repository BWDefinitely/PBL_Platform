from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_URGENCY_SETTINGS: dict[str, Any] = {
    "interrupt_threshold": 0.78,
    "silence_threshold": 0.34,
    "underparticipation_boost": 0.18,
    "direct_mention_boost": 0.55,
    "last_speaker_penalty": 0.35,
    "max_consecutive_turns": 1,
    "min_turns_before_silence": 7,
    "trace_limit": 80,
}

ROLE_BASE_URGENCY = {
    "initiator_proposer": 0.62,
    "evaluator_critic": 0.55,
    "implementer_worker": 0.52,
    "information_seeker": 0.54,
    "gatekeeper_expediter": 0.58,
    "harmonizer": 0.46,
    "encourager": 0.42,
    "free_rider": 0.2,
    "lone_wolf": 0.42,
    "dominator": 0.7,
    "blocker": 0.5,
}

PRESENCE_MULTIPLIER = {
    "active": 1.0,
    "late": 0.78,
    "passive": 0.58,
}

CONFLICT_MARKERS = [
    "不行",
    "不对",
    "问题",
    "反对",
    "吵",
    "算了",
    "别",
    "卡住",
    "不合理",
    "拖",
    "但是",
    "可是",
]
TASK_MARKERS = ["负责", "分工", "截止", "ddl", "deadline", "提交", "先做", "推进", "进度"]
QUESTION_MARKERS = ["?", "？", "怎么", "是否", "为什么", "谁来", "有没有"]
CLOSING_MARKERS = ["先到这", "今天先", "下次", "散会", "先这样", "回头", "各自去做"]


@dataclass
class UrgencySelectionState:
    policy: str = "urgency_queue"
    trace: list[dict[str, Any]] | None = None
    interruption_like_turns: list[int] | None = None
    silence_stop_used: bool = False
    stop_reason: str | None = None

    def __post_init__(self) -> None:
        if self.trace is None:
            self.trace = []
        if self.interruption_like_turns is None:
            self.interruption_like_turns = []

    def asdict(self) -> dict[str, Any]:
        return {
            "speaker_selection_policy": self.policy,
            "interruption_like_turns": self.interruption_like_turns or [],
            "silence_stop_used": self.silence_stop_used,
            "stop_reason": self.stop_reason,
            "speaker_selection_trace": self.trace or [],
        }


def merge_urgency_settings(*sources: dict[str, Any] | None) -> dict[str, Any]:
    settings = dict(DEFAULT_URGENCY_SETTINGS)
    for source in sources:
        if source:
            settings.update(source)
    return settings


def build_urgency_speaker_selector(
    team_profiles: list[dict[str, Any]],
    presence_map: dict[str, str],
    project_state: dict[str, Any],
    settings: dict[str, Any] | None,
    rng: random.Random,
) -> tuple[Callable[[Any, Any], Any | None], UrgencySelectionState]:
    resolved = merge_urgency_settings(settings)
    state = UrgencySelectionState()

    profile_by_name = {profile["agent_name"]: profile for profile in team_profiles}
    live_names = {
        profile["agent_name"]
        for profile in team_profiles
        if presence_map.get(profile["agent_name"]) in PRESENCE_MULTIPLIER
    }

    def select_speaker(last_speaker: Any, groupchat: Any) -> Any | None:
        agents = [agent for agent in groupchat.agents if getattr(agent, "name", None) in live_names]
        if not agents:
            state.silence_stop_used = True
            state.stop_reason = "no_live_agents"
            return None

        messages = [
            message
            for message in getattr(groupchat, "messages", [])
            if message.get("name") in live_names and message.get("content")
        ]
        turn_index = len(messages) + 1
        last_name = getattr(last_speaker, "name", None)
        last_content = str(messages[-1].get("content", "")) if messages else ""
        speaker_counts = count_speaker_messages(messages)
        consecutive_count = count_trailing_speaker(messages, last_name)
        scored = [
            score_candidate(
                agent=agent,
                profile=profile_by_name[getattr(agent, "name")],
                messages=messages,
                speaker_counts=speaker_counts,
                last_name=last_name,
                last_content=last_content,
                consecutive_count=consecutive_count,
                presence_map=presence_map,
                project_state=project_state,
                settings=resolved,
                rng=rng,
            )
            for agent in agents
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        best = scored[0]
        best_agent = best["agent"]

        enough_messages = len(messages) >= int(resolved["min_turns_before_silence"])
        best_score = float(best["score"])
        if enough_messages and best_score < float(resolved["silence_threshold"]):
            state.silence_stop_used = True
            state.stop_reason = "low_urgency"
            append_trace(state, resolved, turn_index, best, scored, selected=None, event="silence_stop")
            return None

        if enough_messages and has_natural_closing_signal(last_content):
            state.silence_stop_used = True
            state.stop_reason = "natural_closing_signal"
            append_trace(state, resolved, turn_index, best, scored, selected=None, event="natural_stop")
            return None

        selected_name = getattr(best_agent, "name")
        is_interruption_like = (
            bool(messages)
            and selected_name != last_name
            and best_score >= float(resolved["interrupt_threshold"])
            and has_interruptible_context(last_content)
        )
        if is_interruption_like:
            state.interruption_like_turns.append(turn_index)

        append_trace(
            state,
            resolved,
            turn_index,
            best,
            scored,
            selected=selected_name,
            event="interruption_like" if is_interruption_like else "selected",
        )
        return best_agent

    return select_speaker, state


def score_candidate(
    agent: Any,
    profile: dict[str, Any],
    messages: list[dict[str, Any]],
    speaker_counts: dict[str, int],
    last_name: str | None,
    last_content: str,
    consecutive_count: int,
    presence_map: dict[str, str],
    project_state: dict[str, Any],
    settings: dict[str, Any],
    rng: random.Random,
) -> dict[str, Any]:
    name = getattr(agent, "name")
    persona = profile["persona"]
    role_id = persona.role_id
    score = ROLE_BASE_URGENCY.get(role_id, 0.45)
    reasons = [f"role_base:{role_id}"]

    presence_mode = presence_map.get(name, "active")
    score *= PRESENCE_MULTIPLIER.get(presence_mode, 0.75)
    reasons.append(f"presence:{presence_mode}")

    average_count = sum(speaker_counts.values()) / max(len(speaker_counts), 1)
    own_count = speaker_counts.get(name, 0)
    if own_count < average_count:
        delta = (average_count - own_count) * float(settings["underparticipation_boost"])
        score += delta
        reasons.append("underparticipation")

    if directly_mentions(last_content, name):
        score += float(settings["direct_mention_boost"])
        reasons.append("direct_mention")

    if name == last_name:
        score -= float(settings["last_speaker_penalty"])
        reasons.append("last_speaker_penalty")
        if consecutive_count >= int(settings["max_consecutive_turns"]):
            score -= 0.45
            reasons.append("max_consecutive_turns")

    deadline_pressure = project_state.get("deadline_pressure", "low")
    score += deadline_pressure_boost(role_id, deadline_pressure, last_content, reasons)
    score += context_role_boost(role_id, last_content, reasons)

    if role_id == "free_rider" and not directly_mentions(last_content, name):
        score -= 0.16
        reasons.append("free_rider_without_prompt")

    if role_id == "dominator" and has_interruptible_context(last_content):
        score += 0.12
        reasons.append("dominator_interrupt_bias")

    if not messages:
        if role_id in {"initiator_proposer", "gatekeeper_expediter", "information_seeker"}:
            score += 0.22
            reasons.append("opening_speaker_bias")
        if role_id in {"free_rider", "blocker"}:
            score -= 0.1
            reasons.append("low_opening_bias")

    # Tiny deterministic jitter avoids repetitive ties without making behavior random.
    score += rng.uniform(0.0, 0.035)

    return {
        "agent": agent,
        "speaker": name,
        "role_id": role_id,
        "score": round(max(score, 0.0), 4),
        "reasons": reasons,
    }


def deadline_pressure_boost(
    role_id: str,
    deadline_pressure: str,
    last_content: str,
    reasons: list[str],
) -> float:
    if deadline_pressure == "high":
        if role_id in {"gatekeeper_expediter", "implementer_worker"}:
            reasons.append("high_deadline_task_push")
            return 0.18
        if role_id in {"dominator", "blocker"} and has_conflict_signal(last_content):
            reasons.append("high_deadline_conflict")
            return 0.1
    if deadline_pressure == "medium" and role_id == "gatekeeper_expediter":
        reasons.append("medium_deadline_gatekeeping")
        return 0.08
    return 0.0


def context_role_boost(role_id: str, last_content: str, reasons: list[str]) -> float:
    boost = 0.0
    if has_conflict_signal(last_content):
        if role_id == "harmonizer":
            boost += 0.34
            reasons.append("conflict_harmonize")
        if role_id in {"evaluator_critic", "blocker", "dominator"}:
            boost += 0.14
            reasons.append("conflict_response")
    if has_task_signal(last_content):
        if role_id in {"implementer_worker", "gatekeeper_expediter"}:
            boost += 0.16
            reasons.append("task_execution_signal")
        if role_id == "free_rider":
            boost += 0.1
            reasons.append("task_avoidance_signal")
    if has_question_signal(last_content):
        if role_id in {"information_seeker", "evaluator_critic"}:
            boost += 0.14
            reasons.append("question_response")
        if role_id == "encourager":
            boost += 0.06
            reasons.append("question_support")
    return boost


def count_speaker_messages(messages: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for message in messages:
        name = message.get("name")
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts


def count_trailing_speaker(messages: list[dict[str, Any]], speaker: str | None) -> int:
    if not speaker:
        return 0
    count = 0
    for message in reversed(messages):
        if message.get("name") != speaker:
            break
        count += 1
    return count


def directly_mentions(content: str, name: str) -> bool:
    if not content:
        return False
    return bool(re.search(rf"(^|[\s，。！？、:：@]){re.escape(name)}($|[\s，。！？、:：])", content))


def has_conflict_signal(content: str) -> bool:
    return contains_any(content, CONFLICT_MARKERS)


def has_task_signal(content: str) -> bool:
    return contains_any(content, TASK_MARKERS)


def has_question_signal(content: str) -> bool:
    return contains_any(content, QUESTION_MARKERS)


def has_natural_closing_signal(content: str) -> bool:
    return contains_any(content, CLOSING_MARKERS)


def has_interruptible_context(content: str) -> bool:
    return has_conflict_signal(content) or has_task_signal(content) or has_question_signal(content)


def contains_any(content: str, markers: list[str]) -> bool:
    lowered = content.lower()
    return any(marker.lower() in lowered for marker in markers)


def append_trace(
    state: UrgencySelectionState,
    settings: dict[str, Any],
    turn_index: int,
    best: dict[str, Any],
    scored: list[dict[str, Any]],
    selected: str | None,
    event: str,
) -> None:
    if state.trace is None:
        state.trace = []
    trace = state.trace
    trace.append(
        {
            "turn": turn_index,
            "event": event,
            "selected": selected,
            "best_score": best["score"],
            "best_reasons": best["reasons"],
            "top_candidates": [
                {
                    "speaker": item["speaker"],
                    "role_id": item["role_id"],
                    "score": item["score"],
                }
                for item in scored[:3]
            ],
        }
    )
    limit = int(settings.get("trace_limit", 80))
    if len(trace) > limit:
        del trace[:-limit]
