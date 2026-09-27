"""
Model manager: centralizes LLM and embedding model lifecycle.
Provides health status and model metadata to the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama

from app.core.logging_config import get_logger
from app.llm.ollama_client import (
    check_ollama_health,
    check_model_available,
    get_available_models,
    create_chat_llm,
)
from app.llm.embeddings import create_embeddings
from config.settings import Settings

logger = get_logger(__name__)


@dataclass
class ModelStatus:
    """Health and availability status for a model."""

    ollama_reachable: bool = False
    chat_model_available: bool = False
    embed_model_available: bool = False
    available_models: list[str] = field(default_factory=list)
    error_message: Optional[str] = None


class ModelManager:
    """
    Manages LLM and embedding model instances.

    Uses lazy initialization — models are created on first access
    rather than at startup to improve startup latency.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm: Optional[ChatOllama] = None
        self._streaming_llm: Optional[ChatOllama] = None
        self._embeddings: Optional[Embeddings] = None

    def get_status(self) -> ModelStatus:
        """Return current model availability status."""
        base_url = self._settings.ollama_base_url
        reachable = check_ollama_health(base_url)

        if not reachable:
            return ModelStatus(
                ollama_reachable=False,
                error_message=f"Ollama not reachable at {base_url}",
            )

        available = get_available_models(base_url)
        chat_ok = check_model_available(base_url, self._settings.ollama_chat_model)
        embed_ok = check_model_available(base_url, self._settings.ollama_embed_model)

        return ModelStatus(
            ollama_reachable=True,
            chat_model_available=chat_ok,
            embed_model_available=embed_ok,
            available_models=available,
        )

    def get_llm(self, streaming: bool = False) -> ChatOllama:
        """Return the LLM instance, creating it if necessary."""
        if streaming:
            if self._streaming_llm is None:
                self._streaming_llm = create_chat_llm(self._settings, streaming=True)
            return self._streaming_llm

        if self._llm is None:
            self._llm = create_chat_llm(self._settings, streaming=False)
        return self._llm

    def get_embeddings(self) -> Embeddings:
        """Return the embedding model instance, creating it if necessary."""
        if self._embeddings is None:
            self._embeddings = create_embeddings(self._settings)
        return self._embeddings

    def reset(self) -> None:
        """Reset all cached model instances (useful after config change)."""
        self._llm = None
        self._streaming_llm = None
        self._embeddings = None
        logger.info("Model manager reset")

    def update_settings(self, settings: Settings) -> None:
        """Update settings and reset models so new settings take effect."""
        self._settings = settings
        self.reset()