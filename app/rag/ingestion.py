"""
Document ingestion pipeline.
Handles loading, chunking, metadata extraction, and vector store storage.
Supports incremental ingestion with deduplication.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from app.core.exceptions import DocumentIngestionError
from app.core.logging_config import get_logger
from app.rag.chunking import (
    chunk_documents,
    extract_section_from_content,
    extract_title_from_content,
)
from app.rag.loaders import load_document, scan_directory
from app.utils.formatting import format_timestamp
from app.utils.hashing import compute_file_hash
from config.settings import Settings, get_settings

logger = get_logger(__name__)

# Category detection based on directory structure
CATEGORY_MAP: dict[str, str] = {
    "company": "company",
    "cybersecurity": "cybersecurity",
    "network_security": "network_security",
    "linux": "linux_security",
    "windows": "windows_security",
    "cryptography": "cryptography",
    "security_tools": "security_tools",
    "university": "university",
    "course": "course_material",
    "policies": "policies",
    "technical": "technical_documentation",
}


def detect_category(file_path: Path, base_dir: Path) -> str:
    """
    Detect document category from its directory path.

    Args:
        file_path: Path to the document
        base_dir: Base documents directory

    Returns:
        Category string
    """
    try:
        relative = file_path.relative_to(base_dir)
        parts = [p.lower() for p in relative.parts[:-1]]  # Exclude filename
        for part in parts:
            for key, category in CATEGORY_MAP.items():
                if key in part:
                    return category
    except ValueError:
        pass
    return "general"


def build_document_metadata(
    file_path: Path,
    base_dir: Path,
    file_hash: str,
    doc_index: int = 0,
) -> dict[str, Any]:
    """
    Build rich metadata for a document.

    Args:
        file_path: Path to the source file
        base_dir: Base directory for relative path computation
        file_hash: Hash of the file content
        doc_index: Index of this document within the file

    Returns:
        Metadata dictionary
    """
    try:
        relative_path = str(file_path.relative_to(base_dir))
    except ValueError:
        relative_path = str(file_path)

    category = detect_category(file_path, base_dir)

    return {
        "source": relative_path,
        "filename": file_path.name,
        "file_extension": file_path.suffix.lower(),
        "category": category,
        "document_hash": file_hash,
        "ingestion_timestamp": format_timestamp(),
        "doc_index": doc_index,
    }


class IngestionTracker:
    """
    Tracks ingested document hashes to enable incremental ingestion.
    Persists state to a JSON file.
    """

    def __init__(self, tracker_path: Path) -> None:
        self._path = tracker_path
        self._hashes: dict[str, str] = {}  # file_path → hash
        self._load()

    def _load(self) -> None:
        """Load existing tracker state."""
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    self._hashes = json.load(f)
            except Exception:
                self._hashes = {}

    def _save(self) -> None:
        """Persist tracker state."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._hashes, f, indent=2)

    def is_ingested(self, file_path: Path, current_hash: str) -> bool:
        """Check if this file with this hash was already ingested."""
        stored_hash = self._hashes.get(str(file_path))
        return stored_hash == current_hash

    def mark_ingested(self, file_path: Path, file_hash: str) -> None:
        """Mark a file as ingested."""
        self._hashes[str(file_path)] = file_hash
        self._save()

    def remove(self, file_path: Path) -> None:
        """Remove a file from tracking."""
        self._hashes.pop(str(file_path), None)
        self._save()

    @property
    def ingested_count(self) -> int:
        """Number of tracked files."""
        return len(self._hashes)


def ingest_file(
    file_path: Path,
    base_dir: Path,
    settings: Settings | None = None,
) -> tuple[list[Document], dict[str, Any]]:
    """
    Ingest a single file: load → enrich metadata → chunk.

    Args:
        file_path: Path to the file
        base_dir: Base documents directory
        settings: Application settings

    Returns:
        Tuple of (chunks, metadata)
    """
    if settings is None:
        settings = get_settings()

    file_hash = compute_file_hash(file_path)

    # Load raw documents
    raw_docs = load_document(file_path)

    if not raw_docs:
        logger.warning("No content loaded from file", path=str(file_path))
        return [], {}

    # Build base metadata
    base_metadata = build_document_metadata(file_path, base_dir, file_hash)

    # Enrich each doc's metadata before chunking
    for i, doc in enumerate(raw_docs):
        doc.metadata.update(base_metadata)
        doc.metadata["doc_index"] = i

        # Try to extract title if not present
        if "title" not in doc.metadata:
            title = extract_title_from_content(doc.page_content)
            if title:
                doc.metadata["title"] = title

        # Try to extract section
        if "section" not in doc.metadata:
            section = extract_section_from_content(doc.page_content)
            if section:
                doc.metadata["section"] = section

    # Chunk documents
    chunks = chunk_documents(raw_docs, settings, source_metadata=base_metadata)

    # Post-chunk: extract section from each chunk
    for chunk in chunks:
        if "section" not in chunk.metadata or not chunk.metadata.get("section"):
            section = extract_section_from_content(chunk.page_content)
            if section:
                chunk.metadata["section"] = section

    logger.info(
        "File ingested",
        file=file_path.name,
        raw_docs=len(raw_docs),
        chunks=len(chunks),
        category=base_metadata.get("category"),
    )

    return chunks, base_metadata


def ingest_directory(
    documents_dir: Path,
    vector_store_adder: Any,
    settings: Settings | None = None,
    force_reingest: bool = False,
    tracker_path: Path | None = None,
) -> dict[str, Any]:
    """
    Ingest all supported documents from a directory.

    Args:
        documents_dir: Root directory containing documents
        vector_store_adder: Callable that accepts list[Document] and adds to vector store
        settings: Application settings
        force_reingest: Skip deduplication check
        tracker_path: Path to ingestion tracker file

    Returns:
        Ingestion statistics
    """
    if settings is None:
        settings = get_settings()

    if tracker_path is None:
        tracker_path = settings.chroma_dir / "ingestion_tracker.json"

    tracker = IngestionTracker(tracker_path)

    files = scan_directory(documents_dir, recursive=True)

    stats = {
        "total_files": len(files),
        "ingested": 0,
        "skipped": 0,
        "failed": 0,
        "total_chunks": 0,
        "start_time": format_timestamp(),
    }

    for file_path in files:
        try:
            file_hash = compute_file_hash(file_path)

            if not force_reingest and tracker.is_ingested(file_path, file_hash):
                logger.info("Skipping unchanged file", file=file_path.name)
                stats["skipped"] += 1
                continue

            chunks, metadata = ingest_file(file_path, documents_dir, settings)

            if not chunks:
                stats["failed"] += 1
                continue

            # Add to vector store
            vector_store_adder(chunks)

            tracker.mark_ingested(file_path, file_hash)

            stats["ingested"] += 1
            stats["total_chunks"] += len(chunks)

            logger.info(
                "File processed",
                file=file_path.name,
                chunks=len(chunks),
            )

        except DocumentIngestionError as e:
            logger.error("Ingestion failed", file=str(file_path), error=str(e))
            stats["failed"] += 1
        except Exception as e:
            logger.error(
                "Unexpected ingestion error",
                file=str(file_path),
                error=str(e),
            )
            stats["failed"] += 1

    stats["end_time"] = format_timestamp()

    logger.info("Ingestion complete", **stats)
    return stats