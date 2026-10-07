"""
Tests for conversation memory components.
"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from app.memory.conversation import ConversationMemory, ConversationState, ConversationTurn
from app.memory.summarizer import maybe_summarize, summarize_conversation


class TestConversationTurn:
    """Tests for ConversationTurn dataclass."""

    def test_turn_creation(self):
        turn = ConversationTurn(
            user_message="What is TCP?",
            assistant_message="TCP is a transport protocol...",
            sources=[{"source": "doc1.txt"}],
            intent="NETWORK_SECURITY",
            model="mistral",
        )
        assert turn.user_message == "What is TCP?"
        assert turn.assistant_message == "TCP is a transport protocol..."
        assert turn.sources == [{"source": "doc1.txt"}]
        assert turn.intent == "NETWORK_SECURITY"
        assert turn.model == "mistral"
        assert turn.feedback is None

    def test_token_estimate(self):
        turn = ConversationTurn(user_message="Short", assistant_message="Short response")
        # 12 chars / 4 = 3 tokens minimum
        assert turn.token_estimate >= 3


class TestConversationState:
    """Tests for ConversationState dataclass."""

    def test_state_creation(self):
        state = ConversationState(
            conversation_id="test-123",
            mode="Student",
            model="mistral",
        )
        assert state.conversation_id == "test-123"
        assert state.mode == "Student"
        assert state.model == "mistral"
        assert state.turns == []
        assert state.is_empty
        assert state.total_turns == 0

    def test_last_user_message(self):
        state = ConversationState(conversation_id="test", mode="Student")
        assert state.last_user_message is None

        state.turns.append(ConversationTurn(user_message="Q1", assistant_message="A1"))
        state.turns.append(ConversationTurn(user_message="Q2", assistant_message="A2"))
        assert state.last_user_message == "Q2"


class TestConversationMemory:
    """Tests for ConversationMemory."""

    def setup_method(self):
        self.state = ConversationState(conversation_id="test", mode="Student", model="mistral")
        from config.settings import Settings
        self.settings = Settings(memory_turns=3, enable_summarization=True, summary_threshold=5)
        self.memory = ConversationMemory(self.state, self.settings)

    def test_add_turn(self):
        turn = ConversationTurn(user_message="Q1", assistant_message="A1")
        self.memory.add_turn(turn)
        assert len(self.memory.state.turns) == 1
        assert self.memory.state.turns[0].user_message == "Q1"

    def test_get_recent_turns(self):
        for i in range(5):
            self.memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        recent = self.memory.get_recent_turns(3)
        assert len(recent) == 3
        assert recent[0].user_message == "Q2"
        assert recent[-1].user_message == "Q4"

    def test_get_recent_turns_default_limit(self):
        for i in range(5):
            self.memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        recent = self.memory.get_recent_turns()  # Uses settings.memory_turns (3)
        assert len(recent) == 3

    def test_get_langchain_messages(self):
        self.memory.add_turn(ConversationTurn(user_message="Q1", assistant_message="A1"))
        self.memory.add_turn(ConversationTurn(user_message="Q2", assistant_message="A2"))
        self.memory.state.summary = "Previous conversation summary"

        messages = self.memory.get_langchain_messages(include_summary=True)
        # System message + 2 Human + 2 AI = 5 messages
        assert len(messages) == 5
        assert messages[0].content.startswith("[Conversation Summary]")

        messages_no_summary = self.memory.get_langchain_messages(include_summary=False)
        assert len(messages_no_summary) == 4

    def test_get_context_string(self):
        self.memory.add_turn(ConversationTurn(user_message="What is TCP?", assistant_message="TCP is..."))
        self.memory.add_turn(ConversationTurn(user_message="How about UDP?", assistant_message="UDP is..."))

        context = self.memory.get_context_string(n_turns=1)
        assert "UDP" in context
        assert "TCP" not in context  # Only last turn

    def test_update_summary(self):
        self.memory.update_summary("Test summary")
        assert self.memory.state.summary == "Test summary"

    def test_needs_summarization(self):
        # Below threshold
        assert not self.memory.needs_summarization()

        # Add enough turns to exceed threshold (5)
        for i in range(6):
            self.memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        assert self.memory.needs_summarization()

    def test_should_trim_history(self):
        # Below 2 * max_turns
        assert not self.memory.should_trim_history()

        # Exceed 2 * max_turns (6)
        for i in range(7):
            self.memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        assert self.memory.should_trim_history()

    def test_get_total_token_estimate(self):
        self.memory.add_turn(ConversationTurn(user_message="Q1", assistant_message="A1"))
        self.memory.add_turn(ConversationTurn(user_message="Q2", assistant_message="A2"))
        tokens = self.memory.get_total_token_estimate()
        assert tokens > 0

    def test_export_to_markdown(self):
        self.memory.state.summary = "Summary text"
        self.memory.add_turn(ConversationTurn(
            user_message="Q1", assistant_message="A1",
            sources=[{"filename": "doc1.txt"}]
        ))

        md = self.memory.export_to_markdown()
        assert "# Student — Conversation Export" in md
        assert "## Conversation Summary" in md
        assert "Summary text" in md
        assert "**User:** Q1" in md
        assert "**Assistant:** A1" in md
        assert "doc1.txt" in md

    def test_export_to_json(self):
        self.memory.add_turn(ConversationTurn(
            user_message="Q1", assistant_message="A1",
            intent="NETWORK_SECURITY", model="mistral"
        ))

        data = self.memory.export_to_json()
        assert data["conversation_id"] == "test"
        assert data["mode"] == "Student"
        assert len(data["turns"]) == 1
        assert data["turns"][0]["user"] == "Q1"
        assert data["turns"][0]["intent"] == "NETWORK_SECURITY"
        assert data["turns"][0]["model"] == "mistral"


class TestSummarizer:
    """Tests for conversation summarization."""

    def test_summarize_conversation_empty(self):
        llm = Mock()
        result = summarize_conversation([], llm)
        assert result == ""

    def test_summarize_conversation(self):
        llm = Mock()
        # Mock the chain invoke
        mock_response = Mock()
        mock_response.content = "Summary of conversation"
        llm.invoke.return_value = mock_response

        turns = [
            ConversationTurn(user_message="What is TCP?", assistant_message="TCP is a protocol..."),
            ConversationTurn(user_message="How about UDP?", assistant_message="UDP is another protocol..."),
        ]

        with patch("app.memory.summarizer.StrOutputParser") as mock_parser:
            mock_parser.return_value.invoke.return_value = "Generated summary"
            result = summarize_conversation(turns, llm)

        assert result == "Generated summary"
        llm.invoke.assert_called_once()

    def test_maybe_summarize_not_needed(self):
        from config.settings import Settings
        settings = Settings(memory_turns=3, enable_summarization=True, summary_threshold=5)
        state = ConversationState(conversation_id="test", mode="Student")
        memory = ConversationMemory(state, settings)

        # Add only 2 turns (below threshold of 5)
        memory.add_turn(ConversationTurn(user_message="Q1", assistant_message="A1"))
        memory.add_turn(ConversationTurn(user_message="Q2", assistant_message="A2"))

        llm = Mock()
        result = maybe_summarize(memory, llm)
        assert result is False
        assert len(memory.state.turns) == 2

    def test_maybe_summarize_performed(self):
        from config.settings import Settings
        settings = Settings(memory_turns=3, enable_summarization=True, summary_threshold=5)
        state = ConversationState(conversation_id="test", mode="Student")
        memory = ConversationMemory(state, settings)

        # Add 6 turns (exceeds threshold of 5)
        for i in range(6):
            memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        llm = Mock()
        mock_response = Mock()
        mock_response.content = "Summary"
        llm.invoke.return_value = mock_response

        with patch("app.memory.summarizer.StrOutputParser") as mock_parser:
            mock_parser.return_value.invoke.return_value = "Generated summary"
            result = maybe_summarize(memory, llm)

        assert result is True
        assert memory.state.summary == "Generated summary"
        # Should keep only last 3 turns
        assert len(memory.state.turns) == 3

    def test_maybe_summarize_disabled(self):
        from config.settings import Settings
        settings = Settings(memory_turns=3, enable_summarization=False, summary_threshold=5)
        state = ConversationState(conversation_id="test", mode="Student")
        memory = ConversationMemory(state, settings)

        for i in range(10):
            memory.add_turn(ConversationTurn(user_message=f"Q{i}", assistant_message=f"A{i}"))

        llm = Mock()
        result = maybe_summarize(memory, llm)
        assert result is False
        # No summarization, all turns kept
        assert len(memory.state.turns) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])