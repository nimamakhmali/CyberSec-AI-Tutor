"""
Custom exception hierarchy for CyberSec AI Tutor.
"""
from __future__ import annotations


class CyberSecTutorError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class OllamaConnectionError(CyberSecTutorError):
    """Raised when Ollama server is unreachable."""


class OllamaModelError(CyberSecTutorError):
    """Raised when the requested model is not available."""


class EmbeddingError(CyberSecTutorError):
    """Raised when embedding generation fails."""


class VectorStoreError(CyberSecTutorError):
    """Raised when vector store operations fail."""


class DocumentIngestionError(CyberSecTutorError):
    """Raised when document ingestion fails."""


class RetrievalError(CyberSecTutorError):
    """Raised when retrieval fails."""


class InputValidationError(CyberSecTutorError):
    """Raised when user input fails validation."""


class PromptConstructionError(CyberSecTutorError):
    """Raised when prompt construction fails."""


class WorkflowError(CyberSecTutorError):
    """Raised when LangGraph workflow execution fails."""


class ConfigurationError(CyberSecTutorError):
    """Raised when configuration is invalid."""