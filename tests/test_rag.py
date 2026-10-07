"""
Tests for RAG pipeline components.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.rag.chunking import (
    chunk_documents,
    create_text_splitter,
    extract_section_from_content,
    extract_title_from_content,
)
from app.rag.loaders import (
    get_supported_extensions,
    load_document,
    scan_directory,
)
from app.rag.pipeline import format_context_for_prompt, RAGPipeline
from app.rag.retriever import DocumentRetriever, RetrievedChunk, RetrievalResult
from app.rag.reranker import apply_reranking, rerank_chunks, score_chunk_relevance
from app.rag.vectorstore import ChromaVectorStore, VectorStoreBase
from app.utils.hashing import compute_chunk_id, compute_file_hash, compute_text_hash


class TestHashing:
    """Tests for hashing utilities."""

    def test_compute_file_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            f.flush()
            hash1 = compute_file_hash(Path(f.name))
            hash2 = compute_file_hash(Path(f.name))
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 hex

    def test_compute_text_hash(self):
        hash1 = compute_text_hash("hello world")
        hash2 = compute_text_hash("hello world")
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_compute_chunk_id(self):
        id1 = compute_chunk_id("source.txt", 0, "abc123")
        id2 = compute_chunk_id("source.txt", 0, "abc123")
        id3 = compute_chunk_id("source.txt", 1, "abc123")
        assert id1 == id2
        assert id1 != id3
        assert len(id1) == 16


class TestChunking:
    """Tests for document chunking."""

    def test_create_text_splitter(self):
        from config.settings import Settings
        settings = Settings(chunk_size=500, chunk_overlap=50)
        splitter = create_text_splitter(settings)
        assert splitter._chunk_size == 500
        assert splitter._chunk_overlap == 50

    def test_chunk_documents_basic(self):
        from langchain_core.documents import Document
        from config.settings import Settings

        settings = Settings(chunk_size=100, chunk_overlap=20)
        docs = [Document(page_content="A" * 250, metadata={"source": "test.txt"})]
        chunks = chunk_documents(docs, settings)

        assert len(chunks) >= 2
        for chunk in chunks:
            assert "chunk_id" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "text_hash" in chunk.metadata

    def test_extract_title_from_content(self):
        # Markdown H1
        assert extract_title_from_content("# My Title\n\nContent") == "My Title"
        # First line
        assert extract_title_from_content("Short title\n\nMore content") == "Short title"
        # Long first line (not a title)
        long_line = "x" * 150
        assert extract_title_from_content(long_line + "\n\nContent") is None

    def test_extract_section_from_content(self):
        assert extract_section_from_content("## Section Name\n\nContent") == "Section Name"
        assert extract_section_from_content("### Subsection\nContent") == "Subsection"
        assert extract_section_from_content("No heading here") is None


class TestLoaders:
    """Tests for document loaders."""

    def test_get_supported_extensions(self):
        exts = get_supported_extensions()
        assert ".pdf" in exts
        assert ".txt" in exts
        assert ".md" in exts
        assert ".docx" in exts
        assert ".html" in exts

    def test_load_txt(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello world\nThis is a test.")
            f.flush()
            docs = load_document(Path(f.name))
            assert len(docs) == 1
            assert "Hello world" in docs[0].page_content

    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.txt").write_text("content")
            (tmpdir / "test.md").write_text("# Title")
            (tmpdir / "ignore.xyz").write_text("ignored")
            subdir = tmpdir / "sub"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("nested")

            files = scan_directory(tmpdir, recursive=True)
            assert len(files) == 3
            assert any(f.name == "test.txt" for f in files)
            assert any(f.name == "test.md" for f in files)
            assert any(f.name == "nested.txt" for f in files)


class TestRetriever:
    """Tests for document retriever."""

    def test_retrieved_chunk_properties(self):
        from langchain_core.documents import Document
        doc = Document(page_content="test content", metadata={"source": "test.txt", "category": "test"})
        chunk = RetrievedChunk(document=doc, score=0.9, rank=1)
        assert chunk.content == "test content"
        assert chunk.metadata == doc.metadata
        assert chunk.source == "test.txt"
        assert chunk.category == "test"

    def test_retrieval_result_properties(self):
        from langchain_core.documents import Document
        docs = [
            Document(page_content="c1", metadata={"source": "s1"}),
            Document(page_content="c2", metadata={"source": "s2"}),
        ]
        chunks = [RetrievedChunk(document=d, score=0.9 - i*0.1, rank=i+1) for i, d in enumerate(docs)]
        result = RetrievalResult(
            query="test", chunks=chunks, retrieval_mode="mmr",
            total_retrieved=2, final_count=2
        )
        assert result.has_results
        assert len(result.documents) == 2
        assert len(result.sources) == 2

    def test_retrieval_result_unique_sources(self):
        from langchain_core.documents import Document
        docs = [
            Document(page_content="c1", metadata={"source": "s1"}),
            Document(page_content="c2", metadata={"source": "s1"}),
            Document(page_content="c3", metadata={"source": "s2"}),
        ]
        chunks = [RetrievedChunk(document=d, score=0.9 - i*0.1, rank=i+1) for i, d in enumerate(docs)]
        result = RetrievalResult(query="test", chunks=chunks, retrieval_mode="mmr", total_retrieved=3, final_count=3)
        assert len(result.sources) == 2


class TestReranker:
    """Tests for reranking."""

    def test_score_chunk_relevance(self):
        from langchain_core.documents import Document
        from app.rag.retriever import RetrievedChunk

        query = "tcp syn scan"
        doc = Document(page_content="TCP SYN scanning is a port scanning technique", metadata={})
        chunk = RetrievedChunk(document=doc, score=0.5, rank=1)

        score = score_chunk_relevance(query, chunk)
        assert 0 <= score <= 1
        # Should boost score due to technical term overlap
        assert score > 0.5

    def test_rerank_chunks(self):
        from langchain_core.documents import Document
        from app.rag.retriever import RetrievedChunk

        query = "firewall configuration"
        docs = [
            Document(page_content="How to configure a firewall", metadata={}),
            Document(page_content="Network protocols overview", metadata={}),
        ]
        chunks = [RetrievedChunk(document=d, score=0.5, rank=i+1) for i, d in enumerate(docs)]

        reranked = rerank_chunks(query, chunks)
        assert len(reranked) == 2
        # First should be more relevant
        assert reranked[0].score >= reranked[1].score
        # Ranks should be updated
        assert reranked[0].rank == 1
        assert reranked[1].rank == 2

    def test_apply_reranking(self):
        from langchain_core.documents import Document
        from app.rag.retriever import RetrievedChunk, RetrievalResult

        query = "test query"
        chunks = [RetrievedChunk(document=Document(page_content="c"), score=0.5, rank=1)]
        result = RetrievalResult(query=query, chunks=chunks, retrieval_mode="mmr", total_retrieved=1, final_count=1)

        new_result = apply_reranking(result, query, enabled=True)
        assert new_result.debug_info.get("reranking_applied") is True

        # Test disabled
        new_result2 = apply_reranking(result, query, enabled=False)
        assert new_result2 is result


class TestPipeline:
    """Tests for RAG pipeline."""

    def test_format_context_for_prompt(self):
        from langchain_core.documents import Document
        from app.rag.retriever import RetrievedChunk

        docs = [
            Document(page_content="Content 1", metadata={"filename": "doc1.txt", "category": "cat1", "section": "sec1", "page_number": 5}),
            Document(page_content="Content 2", metadata={"source": "doc2.pdf", "category": "cat2"}),
        ]
        chunks = [RetrievedChunk(document=d, score=0.9 - i*0.1, rank=i+1) for i, d in enumerate(docs)]

        context = format_context_for_prompt(chunks)
        assert "[Source 1: doc1.txt" in context
        assert "Category: cat1" in context
        assert "Section: sec1" in context
        assert "Page: 5" in context
        assert "[Source 2: doc2.pdf" in context

    def test_format_context_empty(self):
        assert format_context_for_prompt([]) == ""


class TestVectorStore:
    """Tests for vector store abstraction."""

    def test_vector_store_base_interface(self):
        # Verify abstract methods exist
        assert hasattr(VectorStoreBase, "add_documents")
        assert hasattr(VectorStoreBase, "similarity_search")
        assert hasattr(VectorStoreBase, "similarity_search_with_score")
        assert hasattr(VectorStoreBase, "max_marginal_relevance_search")
        assert hasattr(VectorStoreBase, "get_retriever")
        assert hasattr(VectorStoreBase, "document_count")
        assert hasattr(VectorStoreBase, "delete_collection")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])