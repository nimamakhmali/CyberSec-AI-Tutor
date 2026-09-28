"""
Model manager: tracks available models and validates configuration.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.exceptions import OllamaModelError
from app.core.logging_config import get_logger
from app.llm.ollama_client import list_ollama_models
from config.settings import Settings, get_settings

logger = get_logger(__name__)

# Popular models that work well for cybersecurity education
RECOMMENDED_CHAT_MODELS = [
    "mistral",
    "mistral:7b",
    "llama3.2",
    "llama3.2:3b",
    "llama3.1",
    "llama3.1:8b",
    "qwen2.5",
    "qwen2.5:7b",
    "deepseek-r1:7b",
    "phi4",
    "gemma2",
    "gemma2:9b",
]

RECOMMENDED_EMBED_MODELS = [
    "nomic-embed-text",
    "mxbai-embed-large",
    "all-minilm",
    "bge-m3",
]


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    is_chat_model: bool
    is_embed_model: bool
    available: bool


@dataclass
class ModelStatus:
    """Current model configuration status."""

    chat_model: str
    embed_model: str
    chat_available: bool
    embed_available: bool
    available_models: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        """True if both models are available."""
        return self.chat_available and self.embed_available

    @property
    def status_message(self) -> str:
        """Human-readable status message."""
        if self.is_ready:
            return f"✅ Ready — Chat: {self.chat_model} | Embed: {self.embed_model}"
        issues = []
        if not self.chat_available:
            issues.append(f"Chat model '{self.chat_model}' not found")
        if not self.embed_available:
            issues.append(f"Embed model '{self.embed_model}' not found")
        return "❌ " + " | ".join(issues)


def get_model_status(settings: Settings | None = None) -> ModelStatus:
    """
    Check which models are available and whether configured models exist.
    """
    if settings is None:
        settings = get_settings()

    available = list_ollama_models(settings)
    available_names = [m.split(":")[0] for m in available]

    def is_available(model_name: str) -> bool:
        base = model_name.split(":")[0]
        return model_name in available or base in available_names

    return ModelStatus(
        chat_model=settings.ollama_chat_model,
        embed_model=settings.ollama_embed_model,
        chat_available=is_available(settings.ollama_chat_model),
        embed_available=is_available(settings.ollama_embed_model),
        available_models=available,
    )