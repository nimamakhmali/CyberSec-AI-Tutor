"""
Conversation summarization for long-running sessions.
Compresses old conversation history into a concise summary.
"""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.core.logging_config import get_logger
from app.memory.conversation import ConversationMemory, ConversationTurn

logger = get_logger(__name__)

SUMMARIZATION_SYSTEM_PROMPT = """You are a conversation summarizer for a cybersecurity education assistant.
Create a concise summary of the conversation that captures:
1. Topics discussed
2. Key concepts explained
3. User's apparent knowledge level
4. Any ongoing questions or themes
5. Important context for continuing the conversation

Keep the summary under 300 words. Focus on information that helps answer future questions.
Do NOT include personal information. Write in third person."""

SUMMARIZATION_PROMPT = """Please summarize the following conversation:

{conversation_text}

Provide a concise summary that captures the essential context for continuing this educational session."""


def summarize_conversation(
    turns: list[ConversationTurn],
    llm: BaseChatModel,
) -> str:
    """
    Generate a summary of conversation turns using the LLM.

    Args:
        turns: Conversation turns to summarize
        llm: Language model for summarization

    Returns:
        Concise conversation summary
    """
    if not turns:
        return ""

    # Format conversation for summarization
    conversation_text = []
    for turn in turns:
        conversation_text.append(f"User: {turn.user_message}")
        conversation_text.append(f"Assistant: {turn.assistant_message[:500]}...")

    conversation_str = "\n\n".join(conversation_text)

    messages = [
        SystemMessage(content=SUMMARIZATION_SYSTEM_PROMPT),
        HumanMessage(
            content=SUMMARIZATION_PROMPT.format(
                conversation_text=conversation_str
            )
        ),
    ]

    try:
        logger.info("Generating conversation summary", turns=len(turns))
        response = llm.invoke(messages)
        summary = StrOutputParser().invoke(response)
        logger.info("Summary generated", length=len(summary))
        return summary
    except Exception as e:
        logger.error("Summarization failed", error=str(e))
        return "Previous conversation covered cybersecurity topics. Summary unavailable."


def maybe_summarize(
    memory: ConversationMemory,
    llm: BaseChatModel,
) -> bool:
    """
    Summarize conversation if threshold is reached.
    Modifies memory in place.

    Args:
        memory: Conversation memory to potentially summarize
        llm: Language model for summarization

    Returns:
        True if summarization was performed
    """
    if not memory.needs_summarization():
        return False

    # Summarize everything except the last N turns
    keep_turns = memory._settings.memory_turns
    turns_to_summarize = memory.state.turns[:-keep_turns]

    if not turns_to_summarize:
        return False

    summary = summarize_conversation(turns_to_summarize, llm)

    if summary:
        # Combine with existing summary if present
        existing = memory.state.summary
        if existing:
            summary = f"[Earlier]: {existing}\n\n[Recent]: {summary}"

        memory.update_summary(summary)
        # Trim old turns from active memory
        memory.state.turns = memory.state.turns[-keep_turns:]
        logger.info(
            "Conversation trimmed",
            kept_turns=keep_turns,
            summarized_turns=len(turns_to_summarize),
        )
        return True

    return False