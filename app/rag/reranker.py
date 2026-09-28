"""
Reranking system to improve retrieval precision.
Implements a lightweight cross-encoder-style reranker using the LLM.
For production, consider a dedicated reranking model.
"""
from __future__ import annotations

import re
from typing import Any

from langchain_core.documents import Document

from app.core.logging_config import get_logger
from app.rag.retriever import RetrievedChunk, RetrievalResult

logger = get_logger(__name__)


def score_chunk_relevance(
    query: str,
    chunk: RetrievedChunk,
) -> float:
    """
    Heuristic relevance scorer.
    Uses keyword overlap + position bias to approximate reranking
    without an additional LLM call.

    Args:
        query: User query
        chunk: Retrieved chunk

    Returns:
        Relevance score 0-1
    """
    content = chunk.content.lower()
    query_terms = set(re.findall(r'\b\w+\b', query.lower()))

    if not query_terms:
        return chunk.score

    # Exact term matches
    exact_matches = sum(1 for term in query_terms if term in content)
    term_score = exact_matches / len(query_terms)

    # Bonus for cybersecurity technical terms matching
    tech_terms = {
        "nmap", "tcp", "udp", "syn", "ack", "rst", "dns", "ssl", "tls",
        "ssh", "http", "https", "firewall", "ids", "ips", "siem", "vpn",
        "kerberos", "ldap", "active", "directory", "metasploit", "wireshark",
        "burp", "suite", "iptables", "nftables", "mitre", "att&ck", "cve",
        "cvss", "cryptography", "cipher", "hash", "rsa", "aes",
    }
    query_tech = query_terms & tech_terms
    content_tech = {t for t in tech_terms if t in content}
    tech_overlap = len(query_tech & content_tech) / max(len(query_tech), 1)

    # Weighted combination
    combined = (
        0.4 * chunk.score +     # Vector similarity
        0.4 * term_score +      # Keyword overlap
        0.2 * tech_overlap      # Technical term bonus
    )

    return min(combined, 1.0)


def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    """
    Rerank retrieved chunks using heuristic scoring.

    Args:
        query: Original user query
        chunks: Retrieved chunks to rerank

    Returns:
        Reranked list of chunks
    """
    if not chunks:
        return chunks

    scored = []
    for chunk in chunks:
        new_score = score_chunk_relevance(query, chunk)
        # Create new chunk with updated score
        reranked = RetrievedChunk(
            document=chunk.document,
            score=new_score,
            rank=chunk.rank,
        )
        scored.append(reranked)

    # Sort by new score
    scored.sort(key=lambda c: c.score, reverse=True)

    # Update ranks
    for i, chunk in enumerate(scored):
        chunk.rank = i + 1

    logger.debug(
        "Reranking complete",
        input_chunks=len(chunks),
        top_score=scored[0].score if scored else 0,
    )

    return scored


def apply_reranking(
    result: RetrievalResult,
    query: str,
    enabled: bool = True,
) -> RetrievalResult:
    """
    Apply reranking to a RetrievalResult.

    Args:
        result: Original retrieval result
        query: User query for reranking
        enabled: Whether reranking is enabled

    Returns:
        Updated RetrievalResult with reranked chunks
    """
    if not enabled or not result.has_results:
        return result

    reranked_chunks = rerank_chunks(query, result.chunks)

    return RetrievalResult(
        query=result.query,
        chunks=reranked_chunks,
        retrieval_mode=result.retrieval_mode,
        total_retrieved=result.total_retrieved,
        final_count=result.final_count,
        debug_info={
            **result.debug_info,
            "reranking_applied": True,
            "post_rerank_scores": [c.score for c in reranked_chunks[:3]],
        },
    )