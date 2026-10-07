"""
LangGraph workflow orchestration.
Defines the complete conversation processing graph.
"""
from __future__ import annotations

from typing import Any, Generator

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from app.core.logging_config import get_logger
from app.graph.nodes import (
    citation_node,
    error_handler_node,
    generation_node,
    input_validation_node,
    intent_detection_node,
    query_rewriting_node,
    retrieval_decision_node,
    retrieval_node,
)
from app.graph.state import ConversationWorkflowState
from app.rag.pipeline import RAGPipeline

logger = get_logger(__name__)


def should_handle_error(state: dict[str, Any]) -> str:
    """Conditional edge: route to error handler if error occurred."""
    ws = ConversationWorkflowState(**state)
    if ws.error and not ws.response:
        return "error_handler"
    return "continue"


def route_after_retrieval_decision(state: dict[str, Any]) -> str:
    """Conditional edge: route to retrieval or skip to generation based on should_retrieve."""
    ws = ConversationWorkflowState(**state)
    if ws.should_retrieve:
        return "retrieve"
    return "skip_retrieval"


def build_workflow(
    llm: BaseChatModel,
    rag_pipeline: RAGPipeline,
) -> Any:
    """
    Build and compile the LangGraph conversation workflow.

    The graph implements this pipeline:
    START → input_validation → intent_detection → query_rewriting
          → retrieval → generation → citations → END

    Error handling routes to error_handler at any failure point.

    Args:
        llm: Chat language model
        rag_pipeline: Configured RAG pipeline

    Returns:
        Compiled LangGraph workflow
    """
    # Create graph with dict-based state (LangGraph compatible)
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("input_validation", input_validation_node)
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("query_rewriting", query_rewriting_node)
    workflow.add_node("retrieval_decision", retrieval_decision_node)
    workflow.add_node("retrieval", retrieval_node(rag_pipeline))
    workflow.add_node("generation", generation_node(llm))
    workflow.add_node("citations", citation_node)
    workflow.add_node("error_handler", error_handler_node)

    # Primary flow
    workflow.add_edge(START, "input_validation")
    workflow.add_edge("input_validation", "intent_detection")
    workflow.add_edge("intent_detection", "query_rewriting")
    workflow.add_edge("query_rewriting", "retrieval_decision")

    # Conditional retrieval
    workflow.add_conditional_edges(
        "retrieval_decision",
        route_after_retrieval_decision,
        {
            "retrieve": "retrieval",
            "skip_retrieval": "generation",
        },
    )

    workflow.add_edge("retrieval", "generation")

    # Conditional error handling after generation
    workflow.add_conditional_edges(
        "generation",
        should_handle_error,
        {
            "error_handler": "error_handler",
            "continue": "citations",
        },
    )

    workflow.add_edge("citations", END)
    workflow.add_edge("error_handler", END)

    compiled = workflow.compile()

    logger.info("LangGraph workflow compiled")
    return compiled


class CyberSecWorkflow:
    """
    High-level workflow wrapper.
    Manages the LangGraph execution and result extraction.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        rag_pipeline: RAGPipeline,
    ) -> None:
        self._llm = llm
        self._rag_pipeline = rag_pipeline
        self._graph = build_workflow(llm, rag_pipeline)

    def run(
        self,
        user_query: str,
        chat_history: list,
        system_prompt: str,
        mode: str = "Student",
        temperature: float = 0.2,
        model_name: str = "",
    ) -> dict[str, Any]:
        """
        Execute the workflow for a user query.

        Args:
            user_query: The user's question
            chat_history: LangChain message history
            system_prompt: Configured system prompt
            mode: User mode
            temperature: Generation temperature
            model_name: Active model name

        Returns:
            Final workflow state dict
        """
        initial_state = ConversationWorkflowState(
            user_query=user_query,
            chat_history=chat_history,
            system_prompt=system_prompt,
            mode=mode,
            temperature=temperature,
            model_name=model_name,
        )

        logger.info(
            "Workflow started",
            query_preview=user_query[:80],
            mode=mode,
        )

        try:
            result = self._graph.invoke(initial_state.to_dict())
            logger.info(
                "Workflow completed",
                steps=result.get("processing_steps", []),
                has_response=bool(result.get("response")),
                has_context=result.get("has_rag_context", False),
            )
            return result
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            # Return a safe error state
            error_state = initial_state.to_dict()
            error_state["response"] = (
                "I encountered a workflow error. Please try again. "
                "If the issue persists, check that Ollama is running."
            )
            error_state["error"] = str(e)
            return error_state

    def stream(
        self,
        user_query: str,
        chat_history: list,
        system_prompt: str,
        mode: str = "Student",
        temperature: float = 0.2,
        model_name: str = "",
    ) -> Generator[str, None, dict[str, Any]]:
        """
        Stream the response token by token.
        Executes the full pipeline, then streams the generation.

        Yields:
            Response tokens as strings

        Returns:
            Final workflow state
        """
        from langchain_core.output_parsers import StrOutputParser
        from app.prompts.rag import build_no_context_prompt, build_rag_prompt

        # Run pipeline without generation to get context
        initial_state = ConversationWorkflowState(
            user_query=user_query,
            chat_history=chat_history,
            system_prompt=system_prompt,
            mode=mode,
            temperature=temperature,
            model_name=model_name,
        )

        # Run through validation, intent, rewriting, retrieval decision, retrieval
        state = initial_state.to_dict()

        try:
            state = input_validation_node(state)
            state = intent_detection_node(state)
            state = query_rewriting_node(state)
            state = retrieval_decision_node(state)
            
            ws_check = ConversationWorkflowState(**state)
            if ws_check.should_retrieve:
                state = retrieval_node(self._rag_pipeline)(state)

            ws = ConversationWorkflowState(**state)
            query = ws.validated_query or user_query

            # Build streaming chain
            if ws.has_rag_context:
                prompt_template = build_rag_prompt()
                prompt_values = {
                    "system_prompt": system_prompt,
                    "chat_history": chat_history,
                    "context": ws.rag_context,
                    "question": query,
                }
            else:
                prompt_template = build_no_context_prompt()
                prompt_values = {
                    "system_prompt": system_prompt,
                    "chat_history": chat_history,
                    "question": query,
                }

            chain = prompt_template | self._llm | StrOutputParser()

            # Stream tokens
            full_response = ""
            policy_note = ws.debug_info.get("policy_note", "")

            if policy_note:
                yield policy_note + "\n\n"
                full_response += policy_note + "\n\n"

            for token in chain.stream(prompt_values):
                full_response += token
                yield token

            # Finalize state
            state["response"] = full_response
            state["response_validated"] = True
            state = citation_node(state)

            return state

        except Exception as e:
            logger.error("Streaming failed", error=str(e))
            error_msg = (
                "⚠️ Streaming error. Ollama may be unavailable. "
                "Please check that `ollama serve` is running."
            )
            yield error_msg
            state["response"] = error_msg
            state["error"] = str(e)
            return state