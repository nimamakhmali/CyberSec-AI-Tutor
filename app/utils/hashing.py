"""
Document hashing utilities for deduplication.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute hash of a file for deduplication.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (sha256 recommended)

    Returns:
        Hex digest string
    """
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_text_hash(text: str) -> str:
    """
    Compute hash of text content.

    Args:
        text: Text to hash

    Returns:
        SHA-256 hex digest
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_chunk_id(source: str, chunk_index: int, text_hash: str) -> str:
    """
    Create a deterministic unique ID for a document chunk.

    Args:
        source: Source file path
        chunk_index: Index of chunk in document
        text_hash: Hash of chunk text

    Returns:
        Unique chunk identifier
    """
    raw = f"{source}::{chunk_index}::{text_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]