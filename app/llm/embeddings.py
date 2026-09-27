"""
Local embedding model integration via Ollama.
Abstracted behind a factory so the embedding backend can be swapped.
"""

from __future__ import annotations

from langchain_ollama import OllamaEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.exceptions import EmbeddingError, OllamaConnectionError
from app.core.logging_config import get_logger
from app.llm.ollama_client import check_ollama_health
from config.settings import Settings

logger = get_logger(__name__)


def create_embeddings(settings: Settings) -> Embeddings:
    """
    Create the embedding model instance.

    Currently uses Ollama embeddings. The factory pattern allows
    switching to other backends (HuggingFace, sentence-transformers, etc.)
    via configuration without changing calling code.

    Args:
        settings: Application settings

    Returns:
        LangChain-compatible Embeddings instance

    Raises:
        OllamaConnectionError: If Ollama is unavailable
        EmbeddingError: If embedding model initialization fails
    """
    if not check_ollama_health(settings.ollama_base_url):
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {settings.ollama_base_url}"
        )

    logger.info(
        "Initializing embedding model",
        model=settings.ollama_embed_model,
        backend="ollama",
    )

    try:
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        # Perform a quick smoke test
        _ = embeddings.embed_query("test")
        logger.info("Embedding model initialized successfully")
        return embeddings
    except Exception as e:
        raise EmbeddingError(
            f"Failed to initialize embedding model '{settings.ollama_embed_model}': {e}",
            details={"model": settings.ollama_embed_model, "error": str(e)},
        ) from e