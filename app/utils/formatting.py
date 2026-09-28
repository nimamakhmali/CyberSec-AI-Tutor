"""
Text formatting and display utilities.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def format_source_reference(metadata: dict[str, Any], index: int) -> str:
    """
    Format a document metadata dict into a readable source reference.

    Args:
        metadata: Document metadata dict
        index: Citation index (1-based)

    Returns:
        Formatted citation string
    """
    parts = []

    title = metadata.get("title") or metadata.get("filename", "Unknown Document")
    parts.append(title)

    section = metadata.get("section")
    if section:
        parts.append(f"— {section}")

    page = metadata.get("page_number")
    if page:
        parts.append(f"— Page {page}")

    category = metadata.get("category")
    if category:
        parts.append(f"[{category}]")

    return f"[{index}] " + " ".join(parts)


def format_sources_block(sources: list[dict[str, Any]]) -> str:
    """
    Format a list of source metadata into a markdown sources block.
    """
    if not sources:
        return ""
    lines = ["**Sources:**"]
    for i, meta in enumerate(sources, 1):
        lines.append(format_source_reference(meta, i))
    return "\n".join(lines)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length characters."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """
    Basic text cleaning for ingested documents.
    - Normalize whitespace
    - Remove null bytes
    - Normalize line endings
    """
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def format_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime as ISO 8601 string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimate (4 chars ≈ 1 token for English).
    For Persian/Arabic text, use a different ratio.
    """
    return max(1, len(text) // 4)