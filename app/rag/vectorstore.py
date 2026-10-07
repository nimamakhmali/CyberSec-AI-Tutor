"""
Vector store abstraction layer.
ChromaDB implementation with clean interface for future backends.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.exceptions import VectorStoreError
from app.core.logging_config import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)


class VectorStoreBase(ABC):
    """
    Abstract interface for vector store backends.
    All vector store implementations must satisfy this interface.
    """

    @abstractmethod
    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to the store. Returns list of IDs."""
        ...

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Search by semantic similarity."""
        ...

    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Document, float]]:
        """Search with similarity scores."""
        ...

    @abstractmethod
    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """MMR search for diverse, relevant results."""
        ...

    @abstractmethod
    def get_retriever(self, search_type: str, search_kwargs: dict) -> Any:
        """Get a LangChain retriever from this store."""
        ...

    @abstractmethod
    def document_count(self) -> int:
        """Return number of documents in the store."""
        ...

    @abstractmethod
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        ...

    @abstractmethod
    def delete_by_source(self, source: str) -> int:
        """
        Delete all documents from a specific source file.

        Args:
            source: Source file path or identifier

        Returns:
            Number of documents deleted
        """
        ...


class ChromaVectorStore(VectorStoreBase):
    """
    ChromaDB vector store implementation.
    Uses persistent storage for durability across sessions.
    """

    def __init__(
        self,
        embeddings: Embeddings,
        settings: Settings | None = None,
    ) -> None:
        if settings is None:
            settings = get_settings()

        self._settings = settings
        self._embeddings = embeddings
        self._persist_dir = settings.chroma_dir
        self._collection_name = settings.chroma_collection_name
        self._store: Chroma | None = None

        self._ensure_directory()
        self._initialize_store()

    def _ensure_directory(self) -> None:
        """Create persist directory if it doesn't exist."""
        self._persist_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_store(self) -> None:
        """Initialize the Chroma store."""
        try:
            self._store = Chroma(
                collection_name=self._collection_name,
                embedding_function=self._embeddings,
                persist_directory=str(self._persist_dir),
            )
            logger.info(
                "ChromaDB initialized",
                collection=self._collection_name,
                persist_dir=str(self._persist_dir),
                doc_count=self.document_count(),
            )
        except Exception as e:
            raise VectorStoreError(
                "Failed to initialize ChromaDB",
                details=str(e),
            ) from e

    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to ChromaDB."""
        if not documents:
            return []
        try:
            # Use chunk_id as the document ID for deduplication
            ids = [
                doc.metadata.get("chunk_id", None)
                for doc in documents
            ]
            # Filter out None IDs
            valid_ids = [id_ for id_ in ids if id_ is not None]

            if len(valid_ids) == len(documents):
                result = self._store.add_documents(documents, ids=valid_ids)
            else:
                result = self._store.add_documents(documents)

            logger.info("Documents added to vector store", count=len(documents))
            return result
        except Exception as e:
            raise VectorStoreError(
                "Failed to add documents",
                details=str(e),
            ) from e

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Semantic similarity search."""
        try:
            return self._store.similarity_search(query, k=k, filter=filter)
        except Exception as e:
            raise VectorStoreError("Similarity search failed", details=str(e)) from e

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Document, float]]:
        """Similarity search returning (doc, score) pairs."""
        try:
            return self._store.similarity_search_with_score(
                query, k=k, filter=filter
            )
        except Exception as e:
            raise VectorStoreError(
                "Similarity search with score failed",
                details=str(e),
            ) from e

    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """MMR search balancing relevance and diversity."""
        try:
            return self._store.max_marginal_relevance_search(
                query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                filter=filter,
            )
        except Exception as e:
            raise VectorStoreError("MMR search failed", details=str(e)) from e

    def get_retriever(
        self,
        search_type: str = "mmr",
        search_kwargs: dict | None = None,
    ) -> Any:
        """
        Get a LangChain retriever.

        Args:
            search_type: "similarity" or "mmr"
            search_kwargs: Additional search parameters
        """
        if search_kwargs is None:
            search_kwargs = {"k": self._settings.retrieval_k}

        return self._store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def document_count(self) -> int:
        """Return total document count in collection."""
        try:
            return self._store._collection.count()
        except Exception:
            return 0

    def delete_collection(self) -> None:
        """Delete the ChromaDB collection."""
        try:
            self._store.delete_collection()
            logger.warning(
                "Vector store collection deleted",
                collection=self._collection_name,
            )
        except Exception as e:
            raise VectorStoreError(
                "Failed to delete collection",
                details=str(e),
            ) from e

    def delete_by_source(self, source: str) -> int:
        """
        Delete all documents from a specific source file.

        Args:
            source: Source file path or identifier

        Returns:
            Number of documents deleted
        """
        try:
            # Query for documents with this source
            results = self._store._collection.get(
                where={"source": source},
                include=["metadatas"]
            )

            ids = results.get("ids", [])
            if not ids:
                logger.info("No documents found for source", source=source)
                return 0

            # Delete by IDs
            self._store._collection.delete(ids=ids)
            logger.info("Deleted documents by source", source=source, count=len(ids))
            return len(ids)
        except Exception as e:
            raise VectorStoreError(
                "Failed to delete documents by source",
                details=str(e),
            ) from e


def create_vector_store(
    embeddings: Embeddings,
    settings: Settings | None = None,
) -> VectorStoreBase:
    """
    Factory function to create the configured vector store.

    Args:
        embeddings: Embedding model to use
        settings: Application settings

    Returns:
        VectorStoreBase implementation

    Raises:
        VectorStoreError: If vector store creation fails
        ConfigurationError: If configured backend is unknown
    """
    if settings is None:
        settings = get_settings()

    backend = settings.vector_db.lower()

    if backend == "chroma":
        return ChromaVectorStore(embeddings, settings)
    else:
        from app.core.exceptions import ConfigurationError
        raise ConfigurationError(
            f"Unknown vector database backend: {backend}",
            details="Supported backends: chroma",
        )