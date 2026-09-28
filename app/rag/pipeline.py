"""
Complete RAG pipeline orchestrator.
Combines retrieval, reranking, and context preparation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from langchain_core.documents import Document

from app.core.logging_config import get_logger
from app.rag.retriever import DocumentRetriever, RetrievalResult
from app.rag.reranker import apply_reranking
from app.utils.formatting import estimate_tokens, format_source_reference
from config.settings import Settings, get_settings

logger = get_logger(__name__)

MAX_CONTEXT_CHARS = 6000  # Approximate character limit for context


@dataclass
class RAGContext:
    """
    Prepared RAG context ready for prompt construction.
    """

    context_text: str
    sources: list[dict[str, Any]]
    retrieval_result: RetrievalResult
    has_relevant_context: bool
    token_estimate: int
    latency_ms: float
    debug_info: dict[str, Any] = field(default_factory=dict)

    @property
    def source_references(self) -> str:
        """Format sources as markdown references."""
        if not self.sources:
            return ""
        lines = []
        for i, meta in enumerate(self.sources, 1):
            lines.append(format_source_reference(meta, i))
        return "\n".join(lines)


def format_context_for_prompt(chunks: list[Any]) -> str:
    """
    Format retrieved chunks into a structured context block.
    Each chunk is labeled with its source for transparency.
    """
    if not chunks:
        return ""

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.metadata
        source = meta.get("filename", meta.get("source", "Unknown"))
        category = meta.get("category", "")
        section = meta.get("section", "")
        page = meta.get("page_number", "")

        # Build source label
        label_parts = [f"[Source {i}: {source}"]
        if category:
            label_parts.append(f"Category: {category}")
        if section:
            label_parts.append(f"Section: {section}")
        if page:
            label_parts.append(f"Page: {page}")
        label = " | ".join(label_parts) + "]"

        parts.append(f"{label}\n{chunk.content}")

    return "\n\n---\n\n".join(parts)


class RAGPipeline:
    """
    Complete RAG pipeline: retrieve → rerank → prepare context.
    """

    def __init__(
        self,
        retriever: DocumentRetriever,
        settings: Settings | None = None,
    ) -> None:
        self._retriever = retriever
        self._settings = settings or get_settings()

    def run(
        self,
        query: str,
        category_filter: str | None = None,
        intent: str | None = None,
    ) -> RAGContext:
        """
        Execute the full RAG pipeline for a query.

        Args:
            query: User query (possibly rewritten)
            category_filter: Optional category to restrict search
            intent: Detected query intent for logging

        Returns:
            RAGContext ready for prompt injection
        """
        start_time = time.perf_counter()

        # --- Retrieval ---
        result = self._retriever.retrieve(
            query=query,
            category_filter=category_filter,
        )

        # --- Reranking ---
        if self._settings.enable_reranking and result.has_results:
            result = apply_reranking(result, query, enabled=True)

        # --- Context preparation ---
        # Limit context to avoid token overflow
        selected_chunks = self._select_chunks_within_limit(result.chunks)

        context_text = format_context_for_prompt(selected_chunks)
        token_estimate = estimate_tokens(context_text)

        # Determine if we have meaningful context
        has_relevant = (
            len(selected_chunks) > 0
            and any(c.score > 0.3 for c in selected_chunks)
        )

        # Extract unique sources
        seen_sources: set[str] = set()
        sources: list[dict[str, Any]] = []
        for chunk in selected_chunks:
            src = chunk.metadata.get("source", "")
            if src not in seen_sources:
                seen_sources.add(src)
                sources.append(chunk.metadata)

        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "RAG pipeline complete",
            query_len=len(query),
            intent=intent,
            retrieved=result.total_retrieved,
            selected=len(selected_chunks),
            has_context=has_relevant,
            tokens=token_estimate,
            latency_ms=round(latency_ms, 2),
        )

        return RAGContext(
            context_text=context_text,
            sources=sources,
            retrieval_result=result,
            has_relevant_context=has_relevant,
            token_estimate=token_estimate,
            latency_ms=latency_ms,
            debug_info={
                "query": query,
                "intent": intent,
                "category_filter": category_filter,
                "retrieval_debug": result.debug_info,
                "selected_chunks": len(selected_chunks),
                "token_estimate": token_estimate,
            },
        )

    def _select_chunks_within_limit(self, chunks: list[Any]) -> list[Any]:
        """
        Select chunks that fit within the context character limit.
        Prioritizes higher-scored chunks.
        """
        selected = []
        total_chars = 0

        for chunk in chunks:
            chunk_chars = len(chunk.content)
            if total_chars + chunk_chars > MAX_CONTEXT_CHARS:
                # If we can't fit even partial content, skip
                if not selected:
                    # Always include at least one chunk
                    selected.append(chunk)
                break
            selected.append(chunk)
            total_chars += chunk_chars

        return selected