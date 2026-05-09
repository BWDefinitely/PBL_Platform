# backend/model.py
"""Document upload and extraction logic."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Final

import fitz
from docx import Document


_SUPPORTED_EXTENSIONS: Final[set[str]] = {".pdf", ".docx"}


def is_supported_file(file_name: str) -> bool:
    """Return whether the uploaded file is supported."""
    suffix = Path(file_name).suffix.lower()
    return suffix in _SUPPORTED_EXTENSIONS


def extract_text_from_pdf(data: bytes) -> str:
    """Extract text from PDF bytes."""
    document = fitz.open(stream=data, filetype="pdf")
    chunks: list[str] = []
    for page in document:
        chunks.append(page.get_text("text"))
    return "\n".join(chunks).strip()


def extract_text_from_docx(data: bytes) -> str:
    """Extract text from DOCX bytes."""
    stream = io.BytesIO(data)
    document = Document(stream)
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n".join(paragraphs).strip()


def extract_text_from_upload(file_name: str, data: bytes) -> str:
    """Extract text from uploaded document bytes.

    原理：按文件扩展名走不同解析器，将 PDF / DOCX 统一转为纯文本上下文。
    """
    if not is_supported_file(file_name):
        raise ValueError("仅支持 .pdf 或 .docx 文件。")

    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(data)
    if suffix == ".docx":
        return extract_text_from_docx(data)

    raise ValueError("不支持的文件类型。")
