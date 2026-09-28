"""
Document loaders supporting multiple file formats.
Extensible loader registry pattern.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from langchain_community.document_loaders import (
    BSHTMLLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document

from app.core.exceptions import DocumentIngestionError
from app.core.logging_config import get_logger
from app.utils.formatting import clean_text

logger = get_logger(__name__)

# Loader registry: extension → loader factory
LoaderFactory = Callable[[str], list[Document]]

_LOADER_REGISTRY: dict[str, LoaderFactory] = {}


def register_loader(extension: str) -> Callable:
    """Decorator to register a loader for a file extension."""
    def decorator(func: LoaderFactory) -> LoaderFactory:
        _LOADER_REGISTRY[extension.lower()] = func
        return func
    return decorator


@register_loader(".pdf")
def load_pdf(file_path: str) -> list[Document]:
    """Load PDF document with page metadata."""
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    # Ensure page numbers are captured in metadata
    for i, doc in enumerate(docs):
        if "page" not in doc.metadata:
            doc.metadata["page_number"] = i + 1
        else:
            doc.metadata["page_number"] = doc.metadata.pop("page", i + 1) + 1
        doc.page_content = clean_text(doc.page_content)
    return [d for d in docs if d.page_content.strip()]


@register_loader(".txt")
def load_txt(file_path: str) -> list[Document]:
    """Load plain text document."""
    loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
    docs = loader.load()
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    return [d for d in docs if d.page_content.strip()]


@register_loader(".md")
def load_markdown(file_path: str) -> list[Document]:
    """Load Markdown document preserving structure."""
    try:
        loader = UnstructuredMarkdownLoader(file_path, mode="elements")
        docs = loader.load()
    except Exception:
        # Fallback to plain text if unstructured fails
        loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
        docs = loader.load()
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    return [d for d in docs if d.page_content.strip()]


@register_loader(".docx")
def load_docx(file_path: str) -> list[Document]:
    """Load DOCX document."""
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    return [d for d in docs if d.page_content.strip()]


@register_loader(".html")
def load_html(file_path: str) -> list[Document]:
    """Load HTML document extracting text content."""
    loader = BSHTMLLoader(file_path, open_encoding="utf-8")
    docs = loader.load()
    for doc in docs:
        doc.page_content = clean_text(doc.page_content)
    return [d for d in docs if d.page_content.strip()]


@register_loader(".htm")
def load_htm(file_path: str) -> list[Document]:
    """Load HTM document (alias for HTML loader)."""
    return load_html(file_path)


def load_document(file_path: Path) -> list[Document]:
    """
    Load a document using the appropriate loader based on file extension.

    Args:
        file_path: Path to the document

    Returns:
        List of Document objects

    Raises:
        DocumentIngestionError: If loading fails or format unsupported
    """
    ext = file_path.suffix.lower()
    loader_fn = _LOADER_REGISTRY.get(ext)

    if loader_fn is None:
        raise DocumentIngestionError(
            f"Unsupported file format: {ext}",
            details=f"Supported formats: {', '.join(sorted(_LOADER_REGISTRY.keys()))}",
        )

    try:
        logger.info("Loading document", path=str(file_path), format=ext)
        docs = loader_fn(str(file_path))
        logger.info(
            "Document loaded",
            path=str(file_path),
            chunks=len(docs),
        )
        return docs
    except DocumentIngestionError:
        raise
    except Exception as e:
        raise DocumentIngestionError(
            f"Failed to load document: {file_path.name}",
            details=str(e),
        ) from e


def get_supported_extensions() -> list[str]:
    """Return list of supported file extensions."""
    return sorted(_LOADER_REGISTRY.keys())


def scan_directory(
    directory: Path,
    recursive: bool = True,
) -> list[Path]:
    """
    Scan a directory for supported documents.

    Args:
        directory: Root directory to scan
        recursive: Whether to scan subdirectories

    Returns:
        List of file paths for supported documents
    """
    supported = set(get_supported_extensions())
    pattern = "**/*" if recursive else "*"

    found = []
    for path in directory.glob(pattern):
        if path.is_file() and path.suffix.lower() in supported:
            found.append(path)

    logger.info(
        "Directory scan complete",
        directory=str(directory),
        found=len(found),
    )
    return sorted(found)