"""
Retrieval system with configurable strategies.
Supports similarity and MMR retrieval with scoring and metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document

from app.core.exceptions import RetrievalError
from app.core.logging_config import get_logger
from app.rag.vectorstore import VectorStoreBase
from config.settings import Settings, get_settings

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with score and metadata."""

    document: Document
    score: float
    rank: int

    @property
    def content(self) -> str:
        return self.document.page_content

    @property
    def metadata(self) -> dict[str, Any]:
        return self.document.metadata

    @property
    def source(self) -> str:
        return self.metadata.get("source", "unknown")

    @property
    def category(self) -> str:
        return self.metadata.get("category", "general")


@dataclass
class RetrievalResult:
    """Complete retrieval result with all chunks and debug info."""

    query: str
    chunks: list[RetrievedChunk]
    retrieval_mode: str
    total_retrieved: int
    final_count: int
    debug_info: dict[str, Any] = field(default_factory=dict)

    @property
    def documents(self) -> list[Document]:
        return [c.document for c in self.chunks]

    @property
    def has_results(self) -> bool:
        return len(self.chunks) > 0

    @property
    def sources(self) -> list[dict[str, Any]]:
        """Unique sources from retrieved chunks."""
        seen = set()
        sources = []
        for chunk in self.chunks:
            src = chunk.source
            if src not in seen:
                seen.add(src)
                sources.append(chunk.metadata)
        return sources


class DocumentRetriever:
    """
    Manages document retrieval from the vector store.
    Supports multiple retrieval strategies and category filtering.
    """

    def __init__(
        self,
        vector_store: VectorStoreBase,
        settings: Settings | None = None,
    ) -> None:
        self._store = vector_store
        self._settings = settings or get_settings()

    def retrieve(
        self,
        query: str,
        k: int | None = None,
        final_k: int | None = None,
        mode: str | None = None,
        category_filter: str | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            k: Number of documents to retrieve (initial)
            final_k: Number of documents to return after filtering
            mode: Retrieval mode ("similarity" or "mmr")
            category_filter: Optional category to filter by

        Returns:
            RetrievalResult with chunks and metadata
        """
        retrieval_k = k or self._settings.retrieval_k
        context_k = final_k or self._settings.final_context_k
        retrieval_mode = mode or self._settings.retrieval_mode

        if self._store.document_count() == 0:
            logger.warning("Vector store is empty — no retrieval possible")
            return RetrievalResult(
                query=query,
                chunks=[],
                retrieval_mode=retrieval_mode,
                total_retrieved=0,
                final_count=0,
                debug_info={"warning": "Vector store is empty"},
            )

        try:
            # Build category filter for ChromaDB
            chroma_filter = None
            if category_filter:
                chroma_filter = {"category": {"$eq": category_filter}}

            if retrieval_mode == "mmr":
                docs = self._store.max_marginal_relevance_search(
                    query=query,
                    k=retrieval_k,
                    fetch_k=min(retrieval_k * 3, 20),
                    lambda_mult=0.6,  # Balance relevance vs diversity
                    filter=chroma_filter,
                )
                # Assign pseudo-scores (MMR doesn't return scores)
                scored = [(doc, 1.0 - (i * 0.05)) for i, doc in enumerate(docs)]
            else:
                scored = self._store.similarity_search_with_score(
                    query=query,
                    k=retrieval_k,
                    filter=chroma_filter,
                )
                # ChromaDB returns distance (lower = more similar), convert to score
                scored = [(doc, 1.0 - min(score, 1.0)) for doc, score in scored]

            # Sort by score descending
            scored.sort(key=lambda x: x[1], reverse=True)

            # Build RetrievedChunk objects
            all_chunks = [
                RetrievedChunk(document=doc, score=score, rank=i + 1)
                for i, (doc, score) in enumerate(scored)
            ]

            # Apply final_k limit
            final_chunks = all_chunks[:context_k]

            logger.info(
                "Retrieval complete",
                query_len=len(query),
                mode=retrieval_mode,
                retrieved=len(all_chunks),
                final=len(final_chunks),
                category_filter=category_filter,
            )

            return RetrievalResult(
                query=query,
                chunks=final_chunks,
                retrieval_mode=retrieval_mode,
                total_retrieved=len(all_chunks),
                final_count=len(final_chunks),
                debug_info={
                    "mode": retrieval_mode,
                    "retrieval_k": retrieval_k,
                    "final_k": context_k,
                    "category_filter": category_filter,
                    "top_scores": [c.score for c in final_chunks[:3]],
                },
            )

        except Exception as e:
            raise RetrievalError(
                "Retrieval failed",
                details=str(e),
            ) from e

    def retrieve_by_category(
        self,
        query: str,
        category: str,
        k: int | None = None,
    ) -> RetrievalResult:
        """Retrieve documents filtered to a specific category."""
        return self.retrieve(query, k=k, category_filter=category)

    def retrieve_company_docs(self, query: str) -> RetrievalResult:
        """Retrieve from company documentation specifically."""
        return self.retrieve_by_category(query, "company")