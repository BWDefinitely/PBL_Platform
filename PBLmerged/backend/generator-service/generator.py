# backend/generator.py
"""Core PBL generation logic."""

from __future__ import annotations

import json
import logging
import time
from typing import List

import requests

from schemas import PageContent
from settings import AI_SETTINGS, PROMPT_SETTINGS


_LOGGER = logging.getLogger(__name__)


class AIRequestError(RuntimeError):
    """Raised when AI API request fails."""


def _validate_ai_settings() -> None:
    """Validate required AI settings."""
    if not AI_SETTINGS.api_key:
        raise AIRequestError(
            "未检测到 JENIYA_API_KEY，请先配置环境变量后再运行。"
        )
    if not AI_SETTINGS.model:
        raise AIRequestError(
            "未检测到 JENIYA_MODEL，请配置可用模型名称后再运行。"
        )


def _extract_error_body(response: requests.Response) -> str:
    """Return readable response body for debugging."""
    try:
        payload = response.json()
        return json.dumps(payload, ensure_ascii=False, indent=2)
    except ValueError:
        return response.text[:1200].strip()


def _parse_chat_content(response: requests.Response) -> str:
    """Parse OpenAI-compatible chat completion content."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise AIRequestError(
            "AI 接口返回的不是有效 JSON。"
            f"\nHTTP {response.status_code}"
            f"\nBody: {response.text[:1200].strip()}"
        ) from exc

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIRequestError(
            "AI 接口返回结构异常：缺少 choices。"
            f"\nPayload: {json.dumps(payload, ensure_ascii=False, indent=2)[:1200]}"
        )

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise AIRequestError("AI 接口返回结构异常：choices[0] 不是对象。")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise AIRequestError("AI 接口返回结构异常：缺少 message。")

    content = message.get("content")
    if not isinstance(content, str):
        raise AIRequestError("AI 接口返回结构异常：message.content 不是字符串。")

    return content.strip()


def _call_ai(prompt: str) -> str:
    """Call AI API and return generated text.

    原理：使用 OpenAI 兼容的 Chat Completions 协议，附带重试和结构校验，
    把网络错误、鉴权错误和模型响应异常转成可诊断的业务异常。
    """
    _validate_ai_settings()

    payload = {
        "model": AI_SETTINGS.model,
        "messages": [
            {
                "role": "system",
                "content": PROMPT_SETTINGS.system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": AI_SETTINGS.temperature,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {AI_SETTINGS.api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(AI_SETTINGS.max_retries + 1):
        try:
            response = requests.post(
                AI_SETTINGS.chat_completions_url,
                headers=headers,
                json=payload,
                timeout=AI_SETTINGS.timeout_seconds,
            )
            if not response.ok:
                body = _extract_error_body(response)
                raise AIRequestError(
                    "AI 接口请求失败。"
                    f"\nHTTP {response.status_code}"
                    f"\nResponse: {body}"
                )
            return _parse_chat_content(response)
        except (requests.RequestException, AIRequestError) as exc:
            last_error = exc
            _LOGGER.warning("AI request failed on attempt %s: %s", attempt + 1, exc)
            if attempt < AI_SETTINGS.max_retries:
                time.sleep(1.0 * (attempt + 1))

    raise AIRequestError(f"AI 请求最终失败：{last_error}") from last_error


def _build_reference_block(reference_mode: bool, reference_text: str) -> str:
    """Build reference section for prompt."""
    if not reference_mode or not reference_text.strip():
        return ""

    clipped = reference_text.strip()
    if len(clipped) > 12000:
        clipped = clipped[:12000]

    return (
        "\n【参考文档内容】\n"
        "请学习以下上传文档的结构、呈现方式和信息组织逻辑，"
        "在保证新内容原创且符合用户需求的前提下，生成类似风格的输出。\n"
        f"{clipped}\n"
    )


def _build_page_prompt(
    description: str,
    total_pages: int,
    page_index: int,
    reference_mode: bool,
    reference_text: str,
) -> str:
    """Build a single-page generation prompt."""
    outline_text = "、".join(PROMPT_SETTINGS.page_outline)
    page_number = page_index + 1
    reference_block = _build_reference_block(reference_mode, reference_text)
    return (
        f"请为一个 PBL 教学教案生成第 {page_number}/{total_pages} 页内容。\n\n"
        f"【用户需求】\n{description.strip()}\n"
        f"{reference_block}\n"
        "【输出要求】\n"
        f"1. 只输出当前页内容；\n"
        f"2. 本页需要完整、可单独阅读；\n"
        f"3. 优先包含：{outline_text}；\n"
        "4. 用清晰的小标题组织内容；\n"
        "5. 不要输出 JSON，不要解释你的做法。\n"
    )


def generate_pages(
    description: str,
    total_pages: int,
    reference_mode: bool = False,
    reference_text: str = "",
) -> List[PageContent]:
    """Generate all pages.

    Args:
        description: User's course description.
        total_pages: Number of pages to generate.
        reference_mode: Whether uploaded document context is enabled.
        reference_text: Extracted reference text.

    Returns:
        List of page contents.
    """
    cleaned_description = description.strip()
    if not cleaned_description:
        raise ValueError("description 不能为空。")
    if total_pages <= 0:
        raise ValueError("total_pages 必须大于 0。")

    pages: list[PageContent] = []
    for page_index in range(total_pages):
        prompt = _build_page_prompt(
            description=cleaned_description,
            total_pages=total_pages,
            page_index=page_index,
            reference_mode=reference_mode,
            reference_text=reference_text,
        )
        content = _call_ai(prompt)
        pages.append(
            PageContent(
                index=page_index,
                title=f"PBL Page {page_index + 1}",
                body=content,
            )
        )
    return pages


def regenerate_page(
    description: str,
    total_pages: int,
    page_index: int,
    reference_mode: bool = False,
    reference_text: str = "",
) -> PageContent:
    """Regenerate a single page."""
    if page_index < 0 or page_index >= total_pages:
        raise ValueError("page_index 超出范围。")

    prompt = _build_page_prompt(
        description=description,
        total_pages=total_pages,
        page_index=page_index,
        reference_mode=reference_mode,
        reference_text=reference_text,
    )
    content = _call_ai(prompt)
    return PageContent(
        index=page_index,
        title=f"PBL Page {page_index + 1}",
        body=content,
    )
