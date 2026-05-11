# backend/settings.py
"""Application settings for the PBL teaching plan generation system.

Google Style compliant.
Python version: 3.10+
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
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


AI_SETTINGS: Final[AISettings] = AISettings(
    api_key=_get_env("JENIYA_API_KEY","sk-sZrlbu7OV3eVqviPC1tAOoghL5copn29DmCS8CeFPxSf8ZHQ"),
    base_url=_get_env("JENIYA_BASE_URL", "https://jeniya.cn/v1/chat/completions"),
    model=_get_env("JENIYA_MODEL", "gpt-4o"),
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