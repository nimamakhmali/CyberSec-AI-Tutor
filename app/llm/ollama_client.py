"""
Ollama LLM client with health checking, retry logic and streaming support.
Wraps LangChain's Ollama integration with application-level error handling.
"""

from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGeneration

from app.core.exceptions import OllamaConnectionError, OllamaModelNotFoundError
from app.core.logging_config import get_logger
from config.settings import Settings

logger = get_logger(__name__)


def check_ollama_health(base_url: str, timeout: float = 5.0) -> bool:
    """
    Verify that the Ollama server is reachable.

    Returns True if healthy, False otherwise.
    Does NOT raise — callers decide how to handle unavailability.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{base_url}/api/tags")
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, Exception):
        return False


def check_model_available(base_url: str, model_name: str, timeout: float = 5.0) -> bool:
    """
    Check if a specific model is available in Ollama.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{base_url}/api/tags")
            if response.status_code != 200:
                return False
            data = response.json()
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            model_base = model_name.split(":")[0]
            return model_base in models
    except Exception:
        return False


def get_available_models(base_url: str, timeout: float = 5.0) -> list[str]:
    """Return list of models available in Ollama."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{base_url}/api/tags")
            if response.status_code != 200:
                return []
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def create_chat_llm(settings: Settings, streaming: bool = False) -> ChatOllama:
    """
    Create a configured ChatOllama instance.

    Args:
        settings: Application settings
        streaming: Enable streaming mode

    Returns:
        Configured ChatOllama instance

    Raises:
        OllamaConnectionError: If Ollama server is not reachable
        OllamaModelNotFoundError: If the model is not available
    """
    if not check_ollama_health(settings.ollama_base_url):
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {settings.ollama_base_url}. "
            "Please ensure Ollama is running."
        )

    logger.info(
        "Creating ChatOllama instance",
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
        streaming=streaming,
        temperature=settings.temperature,
    )

    return ChatOllama(
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
        num_predict=settings.max_tokens,
        streaming=streaming,
    )


def create_streaming_llm(settings: Settings) -> ChatOllama:
    """Create a streaming-enabled ChatOllama instance."""
    return create_chat_llm(settings, streaming=True)