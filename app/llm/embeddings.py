"""
Embedding management with caching.
Abstracts embedding creation to allow future backend swaps.
"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.core.logging_config import get_logger
from app.llm.ollama_client import create_embeddings
from config.settings import Settings, get_settings

logger = get_logger(__name__)


class EmbeddingManager:
    """
    Manages embedding model lifecycle.
    Designed for single initialization, cached for performance.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._embeddings: Embeddings | None = None

    def get_embeddings(self) -> Embeddings:
        """
        Get or create the embedding model instance.
        Lazy initialization for performance.
        """
        if self._embeddings is None:
            logger.info(
                "Initializing embedding model",
                model=self._settings.ollama_embed_model,
            )
            self._embeddings = create_embeddings(self._settings)
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self.get_embeddings().embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""
        return self.get_embeddings().embed_documents(texts)