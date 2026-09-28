"""
Intelligent document chunking strategies.
Preserves document structure where possible.
"""
from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.core.logging_config import get_logger
from app.utils.hashing import compute_chunk_id, compute_text_hash
from config.settings import Settings, get_settings

logger = get_logger(__name__)


def create_text_splitter(settings: Settings | None = None) -> RecursiveCharacterTextSplitter:
    """
    Create a RecursiveCharacterTextSplitter configured for cybersecurity documents.
    Uses separators that respect document structure.
    """
    if settings is None:
        settings = get_settings()

    # Separators ordered by preference — try to split at structural boundaries
    separators = [
        "\n## ",     # Major sections
        "\n### ",    # Subsections
        "\n#### ",   # Sub-subsections
        "\n\n",      # Paragraphs
        "\n",        # Lines
        ". ",        # Sentences
        " ",         # Words (last resort)
        "",          # Characters (absolute last resort)
    ]

    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=separators,
        keep_separator=True,
        length_function=len,
    )


def chunk_documents(
    documents: list[Document],
    settings: Settings | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> list[Document]:
    """
    Split documents into chunks with enriched metadata.

    Args:
        documents: Input documents from loader
        settings: Application settings
        source_metadata: Additional metadata to attach to all chunks

    Returns:
        List of chunked Document objects with metadata
    """
    if settings is None:
        settings = get_settings()

    splitter = create_text_splitter(settings)
    all_chunks: list[Document] = []

    for doc in documents:
        if not doc.page_content.strip():
            continue

        # Split this document
        chunks = splitter.split_documents([doc])

        for i, chunk in enumerate(chunks):
            text_hash = compute_text_hash(chunk.page_content)
            source = chunk.metadata.get("source", "unknown")
            chunk_id = compute_chunk_id(source, i, text_hash)

            # Enrich metadata
            chunk.metadata.update({
                "chunk_id": chunk_id,
                "chunk_index": i,
                "chunk_total": len(chunks),
                "text_hash": text_hash,
                "chunk_size": len(chunk.page_content),
            })

            if source_metadata:
                # Don't overwrite existing metadata
                for k, v in source_metadata.items():
                    if k not in chunk.metadata:
                        chunk.metadata[k] = v

            all_chunks.append(chunk)

    logger.info(
        "Chunking complete",
        input_docs=len(documents),
        output_chunks=len(all_chunks),
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    return all_chunks


def extract_title_from_content(content: str) -> str | None:
    """
    Attempt to extract a title from document content.
    Looks for markdown headings or first non-empty line.
    """
    # Try markdown H1
    h1_match = re.match(r"^#\s+(.+)$", content.strip(), re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # Try first meaningful line
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if lines:
        first = lines[0]
        # Treat as title if it's short enough (< 100 chars)
        if len(first) < 100:
            return first.strip("#").strip()

    return None


def extract_section_from_content(content: str) -> str | None:
    """
    Attempt to extract the section heading from a chunk.
    """
    heading_match = re.match(r"^#{1,4}\s+(.+)$", content.strip(), re.MULTILINE)
    if heading_match:
        return heading_match.group(1).strip()
    return None