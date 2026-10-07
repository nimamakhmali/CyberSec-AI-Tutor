"""
Bounded conversation memory management.
Prevents unlimited context growth through windowed history.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.core.logging_config import get_logger
from app.utils.formatting import estimate_tokens, format_timestamp
from config.settings import Settings, get_settings

logger = get_logger(__name__)


@dataclass
class ConversationTurn:
    """A single conversation exchange (user + assistant)."""

    user_message: str
    assistant_message: str
    timestamp: str = field(default_factory=format_timestamp)
    sources: list[dict[str, Any]] = field(default_factory=list)
    intent: str = ""
    model: str = ""
    feedback: str | None = None  # "helpful" | "not_helpful" | None

    @property
    def token_estimate(self) -> int:
        return estimate_tokens(self.user_message + self.assistant_message)


@dataclass
class ConversationState:
    """
    Complete conversation state including history and summary.
    Designed to be serializable and independent of UI framework.
    """

    conversation_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    summary: str = ""
    mode: str = "Student"
    model: str = ""
    created_at: str = field(default_factory=format_timestamp)
    updated_at: str = field(default_factory=format_timestamp)

    @property
    def total_turns(self) -> int:
        return len(self.turns)

    @property
    def is_empty(self) -> bool:
        return len(self.turns) == 0

    @property
    def last_user_message(self) -> str | None:
        if self.turns:
            return self.turns[-1].user_message
        return None


class ConversationMemory:
    """
    Manages bounded conversation memory with automatic windowing.

    Keeps the last N turns in active memory.
    Older turns can be compressed into a summary.
    """

    def __init__(
        self,
        state: ConversationState,
        settings: Settings | None = None,
    ) -> None:
        self._state = state
        self._settings = settings or get_settings()
        self._max_turns = self._settings.memory_turns

    @property
    def state(self) -> ConversationState:
        return self._state

    def add_turn(self, turn: ConversationTurn) -> None:
        """
        Add a conversation turn to memory.

        Args:
            turn: The conversation exchange to record
        """
        self._state.turns.append(turn)
        self._state.updated_at = format_timestamp()

        total = len(self._state.turns)
        logger.debug(
            "Turn added to memory",
            total_turns=total,
            max_turns=self._max_turns,
        )

    def get_recent_turns(self, n: int | None = None) -> list[ConversationTurn]:
        """
        Get the most recent N turns.

        Args:
            n: Number of turns (defaults to settings.memory_turns)

        Returns:
            List of recent turns
        """
        limit = n or self._max_turns
        return self._state.turns[-limit:]

    def get_langchain_messages(
        self,
        include_summary: bool = True,
    ) -> list[BaseMessage]:
        """
        Convert conversation history to LangChain message format.

        Args:
            include_summary: Whether to include conversation summary

        Returns:
            List of LangChain messages for prompt construction
        """
        messages: list[BaseMessage] = []

        # Include conversation summary if available
        if include_summary and self._state.summary:
            messages.append(
                SystemMessage(
                    content=f"[Conversation Summary]\n{self._state.summary}"
                )
            )

        # Include recent turns
        recent = self.get_recent_turns()
        for turn in recent:
            messages.append(HumanMessage(content=turn.user_message))
            messages.append(AIMessage(content=turn.assistant_message))

        return messages

    def get_context_string(self, n_turns: int = 3) -> str:
        """
        Get recent conversation as a plain text string.
        Used for query rewriting and intent classification.

        Args:
            n_turns: Number of recent turns to include

        Returns:
            Conversation context string
        """
        recent = self.get_recent_turns(n_turns)
        if not recent:
            return ""

        lines = []
        for turn in recent:
            lines.append(f"User: {turn.user_message}")
            lines.append(f"Assistant: {turn.assistant_message[:200]}...")
        return "\n".join(lines)

    def update_summary(self, summary: str) -> None:
        """Update the conversation summary."""
        self._state.summary = summary
        self._state.updated_at = format_timestamp()

    def needs_summarization(self) -> bool:
        """Check if the conversation is long enough to need summarization."""
        return (
            self._settings.enable_summarization
            and len(self._state.turns) > self._settings.summary_threshold
        )

    def should_trim_history(self) -> bool:
        """Check if we should trim old messages from active memory."""
        return len(self._state.turns) > self._max_turns * 2

    def get_total_token_estimate(self) -> int:
        """Estimate total tokens in active conversation memory."""
        recent = self.get_recent_turns()
        return sum(t.token_estimate for t in recent)

    def export_to_markdown(self) -> str:
        """
        Export conversation to Markdown format.

        Returns:
            Markdown-formatted conversation string
        """
        lines = [
            f"# {self._state.mode} — Conversation Export",
            f"**Date:** {self._state.created_at}",
            f"**Model:** {self._state.model}",
            "",
        ]

        if self._state.summary:
            lines.extend([
                "## Conversation Summary",
                self._state.summary,
                "",
            ])

        lines.append("## Conversation")

        for i, turn in enumerate(self._state.turns, 1):
            lines.extend([
                f"### Turn {i} — {turn.timestamp}",
                f"**User:** {turn.user_message}",
                "",
                f"**Assistant:** {turn.assistant_message}",
                "",
            ])

            if turn.sources:
                lines.append("**Sources:**")
                for j, src in enumerate(turn.sources, 1):
                    from app.utils.formatting import format_source_reference
                    lines.append(format_source_reference(src, j))
                lines.append("")

        return "\n".join(lines)

    def export_to_json(self) -> dict[str, Any]:
        """Export conversation to JSON-serializable format."""
        return {
            "conversation_id": self._state.conversation_id,
            "mode": self._state.mode,
            "model": self._state.model,
            "created_at": self._state.created_at,
            "updated_at": self._state.updated_at,
            "summary": self._state.summary,
            "turns": [
                {
                    "user": t.user_message,
                    "assistant": t.assistant_message,
                    "timestamp": t.timestamp,
                    "sources": t.sources,
                    "intent": t.intent,
                    "model": t.model,
                    "feedback": t.feedback,
                }
                for t in self._state.turns
            ],
        }