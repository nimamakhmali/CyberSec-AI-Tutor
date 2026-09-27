"""
Document fingerprinting utilities for incremental ingestion.
Uses SHA-256 of file content to detect changes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path, chunk_size: int = 65536) -> str:
    """
    Compute SHA-256 hash of a file's contents.

    Reads in chunks to handle large files without loading into RAM.

    Args:
        file_path: Path to the file
        chunk_size: Read chunk size in bytes

    Returns:
        Hex-encoded SHA-256 hash string
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while data := f.read(chunk_size):
            sha256.update(data)
    return sha256.hexdigest()


def compute_text_hash(text: str) -> str:
    """
    Compute SHA-256 hash of a text string.

    Used for detecting duplicate document content regardless of filename.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()