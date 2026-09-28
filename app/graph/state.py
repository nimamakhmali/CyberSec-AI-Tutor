"""
LangGraph state definition for the conversation workflow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage


@dataclass
class ConversationWorkflowState:
    """
    Complete state for the LangGraph conversation workflow.
    Passed between nodes and updated at each step.
    """

    # Input
    user_query: str = ""
    chat_history: list[BaseMessage] = field(default_factory=list)
    mode: str = "Student"
    system_prompt: str = ""
    temperature: float = 0.2
    model_name: str = ""

    # Processing
    validated_query: str = ""
    rewritten_query: str = ""
    intent: str = "UNKNOWN"
    intent_confidence: float = 0.0
    category_filter: str | None = None
    should_retrieve: bool = True

    # Retrieval
    rag_context: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    has_rag_context: bool = False
    retrieval_debug: dict[str, Any] = field(default_factory=dict)

    # Generation
    response: str = ""
    is_streaming: bool = False

    # Quality
    response_validated: bool = False
    citations_prepared: bool = False

    # Error handling
    error: str | None = None
    error_type: str | None = None

    # Debug
    debug_info: dict[str, Any] = field(default_factory=dict)
    processing_steps: list[str] = field(default_factory=list)

    def add_step(self, step: str) -> None:
        """Track processing steps for debugging."""
        self.processing_steps.append(step)

    def set_error(self, error: str, error_type: str = "general") -> None:
        """Set error state."""
        self.error = error
        self.error_type = error_type

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for LangGraph compatibility."""
        return {
            "user_query": self.user_query,
            "chat_history": self.chat_history,
            "mode": self.mode,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "model_name": self.model_name,
            "validated_query": self.validated_query,
            "rewritten_query": self.rewritten_query,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "category_filter": self.category_filter,
            "should_retrieve": self.should_retrieve,
            "rag_context": self.rag_context,
            "sources": self.sources,
            "has_rag_context": self.has_rag_context,
            "retrieval_debug": self.retrieval_debug,
            "response": self.response,
            "is_streaming": self.is_streaming,
            "response_validated": self.response_validated,
            "citations_prepared": self.citations_prepared,
            "error": self.error,
            "error_type": self.error_type,
            "debug_info": self.debug_info,
            "processing_steps": self.processing_steps,
        }