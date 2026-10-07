#!/usr/bin/env python3
"""
Reset the vector store (delete all documents).

Usage:
    python scripts/reset_vectorstore.py
    python scripts/reset_vectorstore.py --confirm
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset CyberSec AI Tutor vector store")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    settings = get_settings()
    chroma_dir = settings.chroma_dir
    tracker_file = chroma_dir / "ingestion_tracker.json"

    print("\n⚠️  VECTOR STORE RESET")
    print("=" * 40)
    print(f"This will delete: {chroma_dir}")
    print("All ingested documents will be removed.")
    print("You will need to re-run: python scripts/ingest.py")
    print()

    if not args.confirm:
        response = input("Are you sure? Type 'yes' to confirm: ").strip().lower()
        if response != "yes":
            print("Cancelled.")
            sys.exit(0)

    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
        print(f"✅ Deleted: {chroma_dir}")
        print()

    if tracker_file.exists():
        tracker_file.unlink()
        print(f"✅ Deleted: {tracker_file}")
        print()

    print("✅ Done.")


if __name__ == "__main__":
    main()  