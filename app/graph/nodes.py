"""
LangGraph workflow nodes.
Each node performs a specific step in the conversation processing pipeline.
"""
from __future__ import annotations

import re
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.core.logging_config import get_logger
from app.graph.state import ConversationWorkflowState
from app.prompts.classification import classify_intent
from app.prompts.rag import build_no_context_prompt, build_rag_prompt, build_simple_prompt
from app.rag.pipeline import RAGPipeline
from app.security.policy import evaluate_content_policy
from app.security.sanitizer import validate_and_sanitize

logger = get_logger(__name__)


# ── Node 1: Input Validation ──────────────────────────────────────────────────

def input_validation_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and sanitize user input.
    First line of defense against invalid or malicious input.
    """
    ws = ConversationWorkflowState(**state)
    ws.add_step("input_validation")

    try:
        clean_query = validate_and_sanitize(ws.user_query)
        ws.validated_query = clean_query

        # Evaluate content policy
        policy = evaluate_content_policy(clean_query)
        ws.debug_info["policy"] = {
            "allowed": policy.allowed,
            "requires_framing": policy.requires_defensive_framing,
        }

        # Store guidance note to potentially prepend to response
        if policy.guidance_note:
            ws.debug_info["policy_note"] = policy.guidance_note

        logger.info(
            "Input validated",
            length=len(clean_query),
            requires_framing=policy.requires_defensive_framing,
        )

    except Exception as e:
        ws.set_error(str(e), "validation_error")
        ws.validated_query = ws.user_query  # Fallback

    return ws.to_dict()


# ── Node 2: Intent Detection ──────────────────────────────────────────────────

def intent_detection_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Detect query intent using rule-based classification.
    Routes retrieval to the appropriate knowledge category.
    """
    ws = ConversationWorkflowState(**state)
    ws.add_step("intent_detection")

    query = ws.validated_query or ws.user_query

    # Get recent conversation context for intent classification
    context_str = ""
    if ws.chat_history:
        recent = ws.chat_history[-4:]  # Last 2 turns
        context_str = " ".join(
            m.content for m in recent
            if hasattr(m, "content") and isinstance(m.content, str)
        )

    result = classify_intent(query, context_str)

    ws.intent = result.intent.value
    ws.intent_confidence = result.confidence
    ws.category_filter = result.category_filter
    ws.debug_info["intent"] = {
        "intent": ws.intent,
        "confidence": ws.intent_confidence,
        "category_filter": ws.category_filter,
        "matched_patterns": result.matched_patterns[:3],
    }

    logger.info(
        "Intent detected",
        intent=ws.intent,
        confidence=ws.intent_confidence,
        category=ws.category_filter,
    )

    return ws.to_dict()


# ── Node 3: Query Rewriting ───────────────────────────────────────────────────

def query_rewriting_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Rewrite the query for better retrieval using conversation context.
    Uses simple heuristics to avoid LLM overhead for clear queries.
    """
    ws = ConversationWorkflowState(**state)
    ws.add_step("query_rewriting")

    query = ws.validated_query or ws.user_query

    # Simple heuristic rewriting without LLM call
    # Detect follow-up questions
    followup_patterns = [
        r"^(what|how)\s+about\b",
        r"^(and|but|also|what|why|how)\s+\w{1,4}\b",
        r"^tell\s+me\s+more",
        r"^explain\s+(that|more|it|this)",
        r"^what\s+does\s+that\s+mean",
        r"^(yes|no|ok|sure|go\s+on|continue)",
        r"^(آره|بله|خیر|ادامه|بیشتر)",
    ]

    is_followup = any(
        re.search(p, query.strip().lower())
        for p in followup_patterns
    )

    if is_followup and ws.chat_history:
        # Extract topic from recent messages
        recent_content = []
        for msg in ws.chat_history[-4:]:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                recent_content.append(msg.content[:150])

        if recent_content:
            # Contextual rewrite: append recent topic
            context_snippet = recent_content[-1][:100]
            ws.rewritten_query = f"{query} [Context: {context_snippet}]"
        else:
            ws.rewritten_query = query
    else:
        ws.rewritten_query = query

    ws.debug_info["rewritten_query"] = ws.rewritten_query

    logger.debug(
        "Query rewritten",
        original=query[:80],
        rewritten=ws.rewritten_query[:80],
        is_followup=is_followup,
    )

    return ws.to_dict()


# ── Node 4: Retrieval ─────────────────────────────────────────────────────────

def retrieval_node(
    rag_pipeline: RAGPipeline,
) -> Any:
    """
    Factory that creates a retrieval node with access to the RAG pipeline.
    """
    def _retrieve(state: dict[str, Any]) -> dict[str, Any]:
        ws = ConversationWorkflowState(**state)
        ws.add_step("retrieval")

        query = ws.rewritten_query or ws.validated_query or ws.user_query

        try:
            rag_result = rag_pipeline.run(
                query=query,
                category_filter=ws.category_filter,
                intent=ws.intent,
            )

            ws.rag_context = rag_result.context_text
            ws.sources = rag_result.sources
            ws.has_rag_context = rag_result.has_relevant_context
            ws.retrieval_debug = rag_result.debug_info
            ws.debug_info["retrieval"] = {
                "has_context": rag_result.has_relevant_context,
                "sources_count": len(rag_result.sources),
                "token_estimate": rag_result.token_estimate,
                "latency_ms": round(rag_result.latency_ms, 2),
            }

        except Exception as e:
            logger.error("Retrieval failed", error=str(e))
            ws.rag_context = ""
            ws.has_rag_context = False
            ws.sources = []
            ws.debug_info["retrieval_error"] = str(e)

        return ws.to_dict()

    return _retrieve


# ── Node 5: Answer Generation ─────────────────────────────────────────────────

def generation_node(
    llm: BaseChatModel,
) -> Any:
    """
    Factory that creates an answer generation node.
    """
    def _generate(state: dict[str, Any]) -> dict[str, Any]:
        ws = ConversationWorkflowState(**state)
        ws.add_step("generation")

        query = ws.validated_query or ws.user_query
        start_time = time.perf_counter()

        try:
            if ws.has_rag_context:
                # RAG-augmented prompt
                prompt_template = build_rag_prompt()
                prompt_values = {
                    "system_prompt": ws.system_prompt,
                    "chat_history": ws.chat_history,
                    "context": ws.rag_context,
                    "question": query,
                }
            else:
                # No-context prompt
                prompt_template = build_no_context_prompt()
                prompt_values = {
                    "system_prompt": ws.system_prompt,
                    "chat_history": ws.chat_history,
                    "question": query,
                }

            chain = prompt_template | llm | StrOutputParser()
            response = chain.invoke(prompt_values)

            # Prepend policy note if needed
            policy_note = ws.debug_info.get("policy_note", "")
            if policy_note and policy_note not in response:
                response = f"{policy_note}\n\n{response}"

            ws.response = response

            latency_ms = (time.perf_counter() - start_time) * 1000
            ws.debug_info["generation"] = {
                "latency_ms": round(latency_ms, 2),
                "response_length": len(response),
                "used_rag": ws.has_rag_context,
            }

            logger.info(
                "Response generated",
                length=len(response),
                used_rag=ws.has_rag_context,
                latency_ms=round(latency_ms, 2),
            )

        except Exception as e:
            logger.error("Generation failed", error=str(e))
            ws.set_error(str(e), "generation_error")
            ws.response = (
                "I encountered an error generating a response. "
                "Please check that Ollama is running and the model is available."
            )

        return ws.to_dict()

    return _generate


# ── Node 6: Citation Preparation ──────────────────────────────────────────────

def citation_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare and validate citations.
    Ensures no fabricated sources are included.
    """
    ws = ConversationWorkflowState(**state)
    ws.add_step("citations")

    # Validate that sources exist in actual retrieval results
    # Only include sources that were actually retrieved
    validated_sources = []
    for source in ws.sources:
        # Basic sanity check — must have a source path
        if source.get("source") or source.get("filename"):
            validated_sources.append(source)

    ws.sources = validated_sources
    ws.citations_prepared = True
    ws.debug_info["citations"] = {
        "validated_sources": len(validated_sources),
    }

    return ws.to_dict()


# ── Error Handler ──────────────────────────────────────────────────────────────

def error_handler_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Handle workflow errors gracefully.
    """
    ws = ConversationWorkflowState(**state)
    ws.add_step("error_handler")

    if not ws.response:
        error_type = ws.error_type or "unknown"

        if error_type == "validation_error":
            ws.response = f"⚠️ Input validation error: {ws.error}"
        elif error_type == "generation_error":
            ws.response = (
                "⚠️ I couldn't generate a response. This might be because:\n"
                "- Ollama is not running (`ollama serve`)\n"
                "- The configured model is not installed\n"
                "- The server is temporarily overloaded\n\n"
                f"Technical details: {ws.error}"
            )
        else:
            ws.response = (
                "⚠️ An unexpected error occurred. Please try again. "
                f"If the problem persists, check the application logs."
            )

    logger.error(
        "Error handled",
        error_type=ws.error_type,
        error=ws.error,
    )

    return ws.to_dict()