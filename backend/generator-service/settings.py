# backend/settings.py
"""Application settings for the PBL teaching plan generation system.

Google Style compliant.
Python version: 3.10+
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
from typing import Final, List


@dataclass(frozen=True, slots=True)
class AISettings:
    """AI API related settings."""

    api_key: str
    base_url: str
    model: str
    timeout_seconds: int = 120
    temperature: float = 0.7
    max_retries: int = 2

    @property
    def chat_completions_url(self) -> str:
        """Return normalized chat completions endpoint."""
        base = self.base_url.rstrip("/")
        if base.endswith("/v1/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"


@dataclass(frozen=True, slots=True)
class UISettings:
    """Local web UI settings."""

    host: str = "127.0.0.1"
    port: int = 8765
    auto_open_browser: bool = True
    upload_max_size_mb: int = 20


@dataclass(frozen=True, slots=True)
class PromptSettings:
    """Prompt related settings."""

    system_prompt: str
    page_outline: List[str] = field(default_factory=list)


def _get_env(name: str, default: str = "") -> str:
    """Return stripped environment variable."""
    return os.getenv(name, default).strip()


# Unified LLM config shared with autogen. Single source of truth for
# model/api_key/base_url across the whole backend. Env vars still win when
# present, so deployments can override without editing the file.
_LLM_CONFIG_PATH = Path(__file__).resolve().parent.parent / "llm_config.json"


def _load_unified_llm() -> dict[str, str]:
    try:
        payload = json.loads(_LLM_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    entry = payload.get("platform")
    if not entry and isinstance(payload.get("dialogue"), list) and payload["dialogue"]:
        entry = payload["dialogue"][0]
    if not isinstance(entry, dict):
        return {}
    base = str(entry.get("base_url", "")).rstrip("/")
    # generator-service historically points at the chat/completions URL;
    # normalise here so the rest of the code keeps working unchanged.
    if base and not base.endswith("/chat/completions"):
        if base.endswith("/v1"):
            base = f"{base}/chat/completions"
        else:
            base = f"{base}/v1/chat/completions"
    return {
        "api_key": entry.get("api_key", ""),
        "base_url": base,
        "model": entry.get("model", ""),
    }


_UNIFIED = _load_unified_llm()


AI_SETTINGS: Final[AISettings] = AISettings(
    api_key=_get_env("JENIYA_API_KEY", _UNIFIED.get("api_key", "")),
    base_url=_get_env("JENIYA_BASE_URL", _UNIFIED.get("base_url", "")),
    model=_get_env("JENIYA_MODEL", _UNIFIED.get("model", "gpt-4o")),
)

UI_SETTINGS: Final[UISettings] = UISettings(
    host=_get_env("PBL_HOST", "127.0.0.1"),
    port=int(_get_env("PBL_PORT", "8765")),
    auto_open_browser=_get_env("PBL_AUTO_OPEN_BROWSER", "1") == "1",
    upload_max_size_mb=int(_get_env("PBL_UPLOAD_MAX_MB", "20")),
)

PROMPT_SETTINGS: Final[PromptSettings] = PromptSettings(
    system_prompt=(
        "你是一名资深的跨学科 PBL 教学设计专家。"
        "请输出结构化、真实可执行、面向课堂实施的中文教案内容。"
        "输出必须适合直接展示给教师、学生或课程负责人。"
    ),
    page_outline=[
        "页面标题",
        "本页目标",
        "学习活动设计",
        "教师引导建议",
        "学生产出物",
        "评价与反思要点",
    ],
)

LOG_LEVEL: Final[int] = logging.INFO