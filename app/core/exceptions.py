"""
Application-specific exception hierarchy.
All domain errors inherit from CyberSecTutorError for consistent handling.
"""


class CyberSecTutorError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ── LLM Errors ───────────────────────────────────────────────────────────────

class OllamaConnectionError(CyberSecTutorError):
    """Raised when Ollama server is unreachable."""


class OllamaModelNotFoundError(CyberSecTutorError):
    """Raised when the requested model is not available in Ollama."""


class LLMGenerationError(CyberSecTutorError):
    """Raised when LLM fails to generate a response."""


class EmbeddingError(CyberSecTutorError):
    """Raised when embedding generation fails."""


# ── RAG Errors ────────────────────────────────────────────────────────────────

class DocumentLoadError(CyberSecTutorError):
    """Raised when a document cannot be loaded."""


class ChunkingError(CyberSecTutorError):
    """Raised when document chunking fails."""


class VectorStoreError(CyberSecTutorError):
    """Raised when vector store operations fail."""


class RetrievalError(CyberSecTutorError):
    """Raised when document retrieval fails."""


class IngestionError(CyberSecTutorError):
    """Raised during document ingestion pipeline."""


# ── Security Errors ───────────────────────────────────────────────────────────

class InputValidationError(CyberSecTutorError):
    """Raised when user input fails validation."""


class SafetyPolicyViolation(CyberSecTutorError):
    """Raised when input violates safety policy."""


# ── Memory Errors ─────────────────────────────────────────────────────────────

class MemoryError(CyberSecTutorError):
    """Raised when conversation memory operations fail."""


# ── Configuration Errors ──────────────────────────────────────────────────────

class ConfigurationError(CyberSecTutorError):
    """Raised when required configuration is missing or invalid."""