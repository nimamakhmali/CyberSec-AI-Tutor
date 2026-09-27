"""
Strongly-typed application configuration using Pydantic Settings.
All values are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="CyberSec AI Tutor", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Ollama ────────────────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_chat_model: str = Field(default="mistral", alias="OLLAMA_CHAT_MODEL")
    ollama_embed_model: str = Field(
        default="nomic-embed-text", alias="OLLAMA_EMBED_MODEL"
    )

    # ── Vector Database ───────────────────────────────────────────────────────
    vector_db: Literal["chroma"] = Field(default="chroma", alias="VECTOR_DB")
    chroma_persist_directory: str = Field(
        default="./data/chroma", alias="CHROMA_PERSIST_DIRECTORY"
    )
    chroma_collection_name: str = Field(
        default="cybersec_knowledge", alias="CHROMA_COLLECTION_NAME"
    )

    # ── Chunking ──────────────────────────────────────────────────────────────
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE", ge=100, le=4000)
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP", ge=0, le=500)

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieval_k: int = Field(default=8, alias="RETRIEVAL_K", ge=1, le=20)
    final_context_k: int = Field(default=4, alias="FINAL_CONTEXT_K", ge=1, le=10)
    retrieval_mode: Literal["similarity", "mmr"] = Field(
        default="mmr", alias="RETRIEVAL_MODE"
    )

    # ── Memory ────────────────────────────────────────────────────────────────
    memory_turns: int = Field(default=10, alias="MEMORY_TURNS", ge=1, le=50)
    enable_summarization: bool = Field(
        default=True, alias="ENABLE_SUMMARIZATION"
    )

    # ── Generation ────────────────────────────────────────────────────────────
    temperature: float = Field(
        default=0.2, alias="TEMPERATURE", ge=0.0, le=2.0
    )
    max_tokens: int = Field(default=2048, alias="MAX_TOKENS", ge=256, le=8192)

    # ── Security ──────────────────────────────────────────────────────────────
    enable_safety_filter: bool = Field(
        default=True, alias="ENABLE_SAFETY_FILTER"
    )
    max_input_length: int = Field(
        default=4000, alias="MAX_INPUT_LENGTH", ge=100, le=32000
    )

    # ── Document Ingestion ────────────────────────────────────────────────────
    documents_directory: str = Field(
        default="./data/documents", alias="DOCUMENTS_DIRECTORY"
    )

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, v: int, info) -> int:
        if "chunk_size" in info.data and v >= info.data["chunk_size"]:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    @field_validator("final_context_k")
    @classmethod
    def final_k_less_than_retrieval_k(cls, v: int, info) -> int:
        if "retrieval_k" in info.data and v > info.data["retrieval_k"]:
            raise ValueError("final_context_k must be <= retrieval_k")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()