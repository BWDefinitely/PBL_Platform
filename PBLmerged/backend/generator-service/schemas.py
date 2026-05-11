# backend/schemas.py
"""Typed data schemas for the PBL teaching plan system."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass(slots=True)
class PageContent:
    """Single page content."""

    index: int
    title: str
    body: str

    def to_dict(self) -> Dict[str, object]:
        """Serialize page content to dict."""
        return asdict(self)


@dataclass(slots=True)
class GenerationResult:
    """Full generation result."""

    pages: List[PageContent]

    def to_dict(self) -> Dict[str, object]:
        """Serialize generation result to dict."""
        return {"pages": [page.to_dict() for page in self.pages]}


@dataclass(slots=True)
class GeneratePayload:
    """Generate request payload."""

    description: str
    total_pages: int
    reference_mode: bool = False
    reference_text: str = ""


@dataclass(slots=True)
class RegeneratePayload:
    """Regenerate request payload."""

    description: str
    page_index: int
    total_pages: int
    reference_mode: bool = False
    reference_text: str = ""