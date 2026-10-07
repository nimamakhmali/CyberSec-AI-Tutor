"""
Application settings using Pydantic Settings.
All configuration is driven by environment variables or .env file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Strongly-typed application settings.
    Values are loaded from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = Field(default="CyberSec AI Tutor")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ── Ollama ────────────────────────────────────────────────────────────────
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_chat_model: str = Field(default="mistral")
    ollama_embed_model: str = Field(default="nomic-embed-text")
    ollama_timeout: int = Field(default=120)
    ollama_num_ctx: int = Field(default=8192)

    # ── Vector Database ───────────────────────────────────────────────────────
    vector_db: Literal["chroma"] = Field(default="chroma")
    chroma_persist_directory: str = Field(default="./data/chroma")
    chroma_collection_name: str = Field(default="cybersec_knowledge")

    # ── Chunking ──────────────────────────────────────────────────────────────
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=120, ge=0, le=500)

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieval_k: int = Field(default=8, ge=1, le=20)
    final_context_k: int = Field(default=4, ge=1, le=10)
    retrieval_mode: Literal["similarity", "mmr"] = Field(default="mmr")
    enable_reranking: bool = Field(default=True)

    # ── Memory ────────────────────────────────────────────────────────────────
    memory_turns: int = Field(default=10, ge=1, le=50)
    enable_summarization: bool = Field(default=True)
    summary_threshold: int = Field(default=15, ge=5, le=100)

    # ── Generation ────────────────────────────────────────────────────────────
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_new_tokens: int = Field(default=2048, ge=256, le=8192)
    streaming: bool = Field(default=True)

    # ── Security ──────────────────────────────────────────────────────────────
    max_input_length: int = Field(default=4000, ge=100)
    enable_content_filter: bool = Field(default=True)

    # ── Paths ─────────────────────────────────────────────────────────────────
    @property
    def documents_dir(self) -> Path:
        return Path("./data/documents")

    @property
    def chroma_dir(self) -> Path:
        return Path(self.chroma_persist_directory)

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, v: int, info) -> int:
        """Ensure chunk_overlap < chunk_size."""
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and v >= chunk_size:
            raise ValueError(f"chunk_overlap ({v}) must be less than chunk_size ({chunk_size})")
        return v

    @field_validator("final_context_k")
    @classmethod
    def final_k_lte_retrieval_k(cls, v: int, info) -> int:
        """Ensure final_context_k <= retrieval_k."""
        retrieval_k = info.data.get("retrieval_k")
        if retrieval_k is not None and v > retrieval_k:
            raise ValueError(f"final_context_k ({v}) must be <= retrieval_k ({retrieval_k})")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()