"""
Ollama LLM client factory.
Creates configured LangChain Ollama instances.
"""
from __future__ import annotations

import httpx
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.exceptions import OllamaConnectionError, OllamaModelError
from app.core.logging_config import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)


def check_ollama_health(settings: Settings | None = None) -> bool:
    """
    Check if Ollama server is reachable.
    Returns True if healthy, False otherwise.
    """
    if settings is None:
        settings = get_settings()
    try:
        response = httpx.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=5.0,
        )
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, Exception):
        return False


def list_ollama_models(settings: Settings | None = None) -> list[str]:
    """
    List models available in the local Ollama instance.
    Returns list of model names.
    """
    if settings is None:
        settings = get_settings()
    try:
        response = httpx.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        logger.warning("Failed to list Ollama models", error=str(e))
        return []


def create_chat_llm(
    settings: Settings | None = None,
    model: str | None = None,
    temperature: float | None = None,
    streaming: bool = True,
) -> ChatOllama:
    """
    Create a ChatOllama instance with configured parameters.

    Args:
        settings: Application settings (uses global if None)
        model: Override model name
        temperature: Override temperature
        streaming: Whether to enable streaming

    Returns:
        Configured ChatOllama instance

    Raises:
        OllamaConnectionError: If server is unreachable
    """
    if settings is None:
        settings = get_settings()

    if not check_ollama_health(settings):
        raise OllamaConnectionError(
            f"Ollama server unreachable at {settings.ollama_base_url}",
            details="Ensure Ollama is running: ollama serve",
        )

    resolved_model = model or settings.ollama_chat_model
    resolved_temp = temperature if temperature is not None else settings.temperature

    logger.info(
        "Creating chat LLM",
        model=resolved_model,
        temperature=resolved_temp,
        streaming=streaming,
    )

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=resolved_model,
        temperature=resolved_temp,
        num_ctx=settings.ollama_num_ctx,
        num_predict=settings.max_new_tokens,
        timeout=settings.ollama_timeout,
    )


def create_embeddings(
    settings: Settings | None = None,
    model: str | None = None,
) -> OllamaEmbeddings:
    """
    Create an OllamaEmbeddings instance.

    Args:
        settings: Application settings (uses global if None)
        model: Override embedding model name

    Returns:
        Configured OllamaEmbeddings instance

    Raises:
        OllamaConnectionError: If server is unreachable
    """
    if settings is None:
        settings = get_settings()

    if not check_ollama_health(settings):
        raise OllamaConnectionError(
            f"Ollama server unreachable at {settings.ollama_base_url}",
            details="Ensure Ollama is running: ollama serve",
        )

    resolved_model = model or settings.ollama_embed_model

    logger.info("Creating embeddings model", model=resolved_model)

    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=resolved_model,
    )