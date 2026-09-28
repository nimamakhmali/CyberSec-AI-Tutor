#!/usr/bin/env python3
"""
Document ingestion script for CyberSec AI Tutor.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --force
    python scripts/ingest.py --directory ./data/documents/cybersecurity
    python scripts/ingest.py --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging_config import configure_logging, get_logger
from app.llm.embeddings import EmbeddingManager
from app.llm.ollama_client import check_ollama_health
from app.rag.ingestion import ingest_directory
from app.rag.vectorstore import create_vector_store
from config.settings import get_settings

configure_logging()
logger = get_logger("ingest")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into CyberSec AI Tutor knowledge base"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Directory to ingest (default: data/documents)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of all documents (ignore deduplication)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    settings = get_settings()

    print("\n" + "=" * 60)
    print("  CyberSec AI Tutor — Document Ingestion")
    print("=" * 60)

    # Check Ollama
    print(f"\n📡 Checking Ollama at {settings.ollama_base_url}...")
    if not check_ollama_health(settings):
        print(f"❌ Ollama is not running at {settings.ollama_base_url}")
        print("   Start Ollama with: ollama serve")
        sys.exit(1)
    print("✅ Ollama is running")

    # Initialize embeddings
    print(f"\n🧠 Loading embedding model: {settings.ollama_embed_model}")
    print(f"   If not installed, run: ollama pull {settings.ollama_embed_model}")

    try:
        embedding_manager = EmbeddingManager(settings)
        embeddings = embedding_manager.get_embeddings()
        # Test the embedding
        test_embed = embeddings.embed_query("test")
        print(f"✅ Embeddings ready (dimension: {len(test_embed)})")
    except Exception as e:
        print(f"❌ Embedding initialization failed: {e}")
        sys.exit(1)

    # Initialize vector store
    print(f"\n📊 Initializing vector store...")
    print(f"   Backend: {settings.vector_db}")
    print(f"   Directory: {settings.chroma_dir}")

    try:
        vector_store = create_vector_store(embeddings, settings)
        initial_count = vector_store.document_count()
        print(f"✅ Vector store ready (existing chunks: {initial_count})")
    except Exception as e:
        print(f"❌ Vector store initialization failed: {e}")
        sys.exit(1)

    # Determine documents directory
    docs_dir = Path(args.directory) if args.directory else settings.documents_dir

    if not docs_dir.exists():
        print(f"\n⚠️  Documents directory not found: {docs_dir}")
        print("   Creating it...")
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Add your documents to: {docs_dir}")
        print("   Supported formats: .pdf, .txt, .md, .docx, .html")
        sys.exit(0)

    print(f"\n📂 Documents directory: {docs_dir}")
    if args.force:
        print("⚠️  Force mode: all documents will be re-ingested")

    # Run ingestion
    print("\n" + "-" * 40)
    print("Starting ingestion...")
    print("-" * 40 + "\n")

    def add_to_store(chunks):
        vector_store.add_documents(chunks)

    try:
        stats = ingest_directory(
            documents_dir=docs_dir,
            vector_store_adder=add_to_store,
            settings=settings,
            force_reingest=args.force,
            tracker_path=settings.chroma_dir / "ingestion_tracker.json",
        )

        final_count = vector_store.document_count()

        print("\n" + "=" * 60)
        print("  Ingestion Complete")
        print("=" * 60)
        print(f"  📄 Files processed: {stats['ingested']}")
        print(f"  ⏭️  Files skipped:   {stats['skipped']}")
        print(f"  ❌ Files failed:    {stats['failed']}")
        print(f"  🧩 Total chunks:    {stats['total_chunks']}")
        print(f"  📊 Vector store:    {final_count} total chunks")
        print(f"  ⏱️  Start: {stats['start_time']}")
        print(f"  ⏱️  End:   {stats['end_time']}")
        print("=" * 60 + "\n")

        if stats['failed'] > 0:
            print("⚠️  Some files failed. Check the logs for details.")

        if stats['ingested'] == 0 and stats['skipped'] > 0:
            print("ℹ️  All documents are already up to date.")
            print("   Use --force to re-ingest all documents.")

    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        logger.error("Ingestion error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()