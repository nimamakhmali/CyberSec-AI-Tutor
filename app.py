"""
CyberSec AI Tutor — Main Streamlit Application

Entry point for the application.
Run with: streamlit run app.py
"""
from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

# Page config must be FIRST Streamlit call
st.set_page_config(
    page_title="CyberSec AI Tutor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "CyberSec AI Tutor — Local AI for Cybersecurity Education",
    },
)

from app.core.logging_config import configure_logging, get_logger
from app.graph.workflow import CyberSecWorkflow
from app.llm.embeddings import EmbeddingManager
from app.llm.model_manager import get_model_status
from app.llm.ollama_client import check_ollama_health, create_chat_llm
from app.memory.conversation import (
    ConversationMemory,
    ConversationState,
    ConversationTurn,
)
from app.memory.summarizer import maybe_summarize
from app.prompts.education import get_mode_instructions
from app.prompts.system import get_system_prompt
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import DocumentRetriever
from app.rag.vectorstore import create_vector_store
from app.ui.chat import handle_export, render_conversation_history
from app.ui.components import render_welcome_screen
from app.ui.layout import inject_css, render_sidebar
from config.settings import get_settings

# Configure logging
configure_logging()
logger = get_logger(__name__)

settings = get_settings()


# ── Cached Resource Initialization ─────────────────────────────────────────────

@st.cache_resource(show_spinner="Initializing embedding model...")
def get_embedding_manager() -> EmbeddingManager:
    """Initialize and cache the embedding manager."""
    manager = EmbeddingManager()
    logger.info("Embedding manager initialized")
    return manager


@st.cache_resource(show_spinner="Connecting to knowledge base...")
def get_vector_store_and_retriever():
    """Initialize and cache vector store and retriever."""
    embedding_manager = get_embedding_manager()
    embeddings = embedding_manager.get_embeddings()
    vector_store = create_vector_store(embeddings)
    retriever = DocumentRetriever(vector_store)
    logger.info(
        "Vector store connected",
        doc_count=vector_store.document_count(),
    )
    return vector_store, retriever


@st.cache_resource(show_spinner="Loading AI model...")
def get_llm(model_name: str, temperature: float):
    """Initialize and cache the chat LLM."""
    try:
        llm = create_chat_llm(
            model=model_name,
            temperature=temperature,
            streaming=True,
        )
        logger.info("LLM initialized", model=model_name)
        return llm
    except Exception as e:
        logger.error("LLM initialization failed", error=str(e))
        return None


# ── Session State Initialization ───────────────────────────────────────────────

def init_session_state() -> None:
    """Initialize Streamlit session state with defaults."""
    defaults = {
        "conversation_id": str(uuid.uuid4()),
        "messages": [],               # UI message list
        "conversation_state": None,    # ConversationState object
        "mode": "Student",
        "teaching_mode": False,
        "active_model": settings.ollama_chat_model,
        "temperature": settings.temperature,
        "streaming": settings.streaming,
        "show_sources": True,
        "retrieval_k": settings.retrieval_k,
        "debug_mode": settings.debug,
        "trigger_new_chat": False,
        "trigger_export": False,
        "feedback": {},
        "pending_question": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize conversation state if needed
    if st.session_state["conversation_state"] is None:
        st.session_state["conversation_state"] = ConversationState(
            conversation_id=st.session_state["conversation_id"],
            mode=st.session_state["mode"],
            model=st.session_state["active_model"],
        )


def reset_conversation() -> None:
    """Reset conversation state for a new chat."""
    st.session_state["conversation_id"] = str(uuid.uuid4())
    st.session_state["messages"] = []
    st.session_state["conversation_state"] = ConversationState(
        conversation_id=st.session_state["conversation_id"],
        mode=st.session_state.get("mode", "Student"),
        model=st.session_state.get("active_model", settings.ollama_chat_model),
    )
    st.session_state["trigger_new_chat"] = False
    logger.info("Conversation reset")


# ── Main Application ────────────────────────────────────────────────────────────

def main() -> None:
    """Main application entry point."""
    # Inject CSS
    inject_css()

    # Initialize session
    init_session_state()

    # ── Check Ollama Health ───────────────────────────────────────────────────
    ollama_connected = check_ollama_health(settings)

    # ── Initialize Resources ──────────────────────────────────────────────────
    doc_count = 0
    vector_store = None
    retriever = None
    rag_pipeline = None

    try:
        vector_store, retriever = get_vector_store_and_retriever()
        doc_count = vector_store.document_count()
        rag_pipeline = RAGPipeline(retriever)
    except Exception as e:
        logger.error("Resource initialization failed", error=str(e))

    # ── Sidebar ───────────────────────────────────────────────────────────────
    sidebar_settings = render_sidebar(
        ollama_connected=ollama_connected,
        doc_count=doc_count,
    )

    # Update session state from sidebar
    st.session_state["mode"] = sidebar_settings["mode"]
    st.session_state["teaching_mode"] = sidebar_settings["teaching_mode"]
    st.session_state["temperature"] = sidebar_settings["temperature"]
    st.session_state["streaming"] = sidebar_settings["streaming"]
    st.session_state["show_sources"] = sidebar_settings["show_sources"]
    st.session_state["retrieval_k"] = sidebar_settings["retrieval_k"]
    st.session_state["debug_mode"] = sidebar_settings["debug_mode"]

    # Handle model change
    new_model = sidebar_settings["selected_model"]
    if new_model != st.session_state.get("active_model"):
        st.session_state["active_model"] = new_model
        # Cache will reload with new model on next LLM call

    # ── Handle New Chat ────────────────────────────────────────────────────────
    if st.session_state.get("trigger_new_chat"):
        reset_conversation()
        st.rerun()

    # ── Handle Export ──────────────────────────────────────────────────────────
    if st.session_state.get("trigger_export"):
        conv_state: ConversationState = st.session_state["conversation_state"]
        if conv_state and conv_state.turns:
            memory = ConversationMemory(conv_state)
            export_data = memory.export_to_json()
            handle_export(export_data)
        st.session_state["trigger_export"] = False

    # ── Ollama Warning ─────────────────────────────────────────────────────────
    if not ollama_connected:
        st.error(
            "⚠️ **Ollama is not running.** "
            "Start it with `ollama serve` and refresh this page.\n\n"
            f"Configured URL: `{settings.ollama_base_url}`"
        )

    # ── Main Chat Interface ────────────────────────────────────────────────────
    messages = st.session_state["messages"]

    # Welcome screen when no messages
    if not messages:
        selected_question = render_welcome_screen()
        if selected_question:
            st.session_state["pending_question"] = selected_question
            st.rerun()
    else:
        # Render conversation history
        render_conversation_history(
            messages=messages,
            show_sources=st.session_state["show_sources"],
            debug_mode=st.session_state["debug_mode"],
        )

    # ── Chat Input ─────────────────────────────────────────────────────────────
    # Handle pending question from welcome screen
    pending = st.session_state.pop("pending_question", None)

    user_input = st.chat_input(
        placeholder="Ask about cybersecurity, network security, or company knowledge...",
        disabled=not ollama_connected,
    )

    # Use pending question or typed input
    query = pending or user_input

    if query and ollama_connected:
        _process_user_query(
            query=query,
            rag_pipeline=rag_pipeline,
            sidebar_settings=sidebar_settings,
        )


def _process_user_query(
    query: str,
    rag_pipeline: RAGPipeline | None,
    sidebar_settings: dict[str, Any],
) -> None:
    """
    Process a user query through the full pipeline.

    Args:
        query: User's question
        rag_pipeline: RAG pipeline instance
        sidebar_settings: Current sidebar configuration
    """
    mode = sidebar_settings["mode"]
    teaching_mode = sidebar_settings["teaching_mode"]
    selected_model = sidebar_settings["selected_model"]
    temperature = sidebar_settings["temperature"]
    streaming = sidebar_settings["streaming"]
    show_sources = sidebar_settings["show_sources"]
    debug_mode = sidebar_settings["debug_mode"]

    # Add user message to UI
    st.session_state["messages"].append({
        "role": "user",
        "content": query,
    })

    # Display user message immediately
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(query)

    # Get conversation memory
    conv_state: ConversationState = st.session_state["conversation_state"]
    memory = ConversationMemory(conv_state)

    # Build system prompt
    system_prompt = get_system_prompt(
        mode=mode,
        user_level=_detect_user_level(memory),
        teaching_mode=teaching_mode,
    ) + "\n\n" + get_mode_instructions(mode)

    # Get LLM
    llm = get_llm(selected_model, temperature)

    if llm is None:
        error_msg = (
            "⚠️ Could not load the language model. "
            "Check that Ollama is running and the model is installed.\n\n"
            f"Install the model with: `ollama pull {selected_model}`"
        )
        with st.chat_message("assistant", avatar="🛡️"):
            st.error(error_msg)
        st.session_state["messages"].append({
            "role": "assistant",
            "content": error_msg,
        })
        return

    # Check if RAG is available
    if rag_pipeline is None:
        # Fallback: direct LLM without RAG
        workflow = None
    else:
        workflow = CyberSecWorkflow(llm=llm, rag_pipeline=rag_pipeline)

    # Get chat history for context
    chat_history = memory.get_langchain_messages(include_summary=True)

    # Generate response
    with st.chat_message("assistant", avatar="🛡️"):
        response_placeholder = st.empty()
        full_response = ""
        final_state = {}

        if streaming and workflow:
            # Streaming mode
            stream_gen = workflow.stream(
                user_query=query,
                chat_history=chat_history,
                system_prompt=system_prompt,
                mode=mode,
                temperature=temperature,
                model_name=selected_model,
            )

            try:
                # Manually iterate to capture generator return value (final state)
                while True:
                    try:
                        token = next(stream_gen)
                        full_response += token
                        response_placeholder.markdown(full_response + "▋")
                    except StopIteration as e:
                        final_state = e.value if e.value else {}
                        break

            except Exception as e:
                logger.error("Streaming error", error=str(e))
                full_response = (
                    "⚠️ Streaming error occurred. "
                    "Please try again or disable streaming in settings."
                )

            response_placeholder.markdown(full_response)

        elif workflow:
            # Non-streaming mode
            with st.spinner("Thinking..."):
                final_state = workflow.run(
                    user_query=query,
                    chat_history=chat_history,
                    system_prompt=system_prompt,
                    mode=mode,
                    temperature=temperature,
                    model_name=selected_model,
                )
            full_response = final_state.get("response", "")
            response_placeholder.markdown(full_response)

        else:
            # No RAG fallback
            with st.spinner("Thinking..."):
                from langchain_core.messages import HumanMessage, SystemMessage
                from langchain_core.output_parsers import StrOutputParser

                msgs = [
                    SystemMessage(content=system_prompt),
                    *chat_history,
                    HumanMessage(content=query),
                ]
                response = llm.invoke(msgs)
                full_response = StrOutputParser().invoke(response)
            response_placeholder.markdown(full_response)

        # Extract state info
        sources = final_state.get("sources", [])
        debug_info = final_state.get("debug_info", {})

        # Show sources
        if show_sources and sources:
            from app.ui.components import render_sources_section
            render_sources_section(sources)

        # Show debug
        if debug_mode and debug_info:
            from app.ui.components import render_debug_panel
            render_debug_panel(debug_info)

        # Feedback buttons
        turn_idx = len(st.session_state["messages"])
        col1, col2, _ = st.columns([1, 1, 8])
        with col1:
            if st.button("👍", key=f"up_{turn_idx}"):
                st.toast("Thanks! 👍")
        with col2:
            if st.button("👎", key=f"down_{turn_idx}"):
                st.toast("Thanks for the feedback!")

    # Update conversation memory
    turn = ConversationTurn(
        user_message=query,
        assistant_message=full_response,
        sources=sources,
        intent=final_state.get("intent", ""),
        model=selected_model,
    )
    memory.add_turn(turn)

    # Store in session
    st.session_state["messages"].append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
        "debug_info": debug_info if debug_mode else {},
    })

    # Maybe summarize
    if memory.needs_summarization() and llm:
        try:
            maybe_summarize(memory, llm)
            logger.info("Conversation summarized")
        except Exception as e:
            logger.warning("Summarization failed", error=str(e))

    # Update session state
    st.session_state["conversation_state"] = memory.state


def _detect_user_level(memory: ConversationMemory) -> str:
    """
    Detect user expertise level from conversation history.
    Simple heuristic based on question complexity.
    """
    if memory.state.is_empty:
        return "INTERMEDIATE"

    recent = memory.get_recent_turns(3)
    if not recent:
        return "INTERMEDIATE"

    # Heuristic: length of questions and technical term density
    avg_question_length = sum(len(t.user_message) for t in recent) / len(recent)

    expert_terms = [
        "tcp", "udp", "syn", "ack", "rst", "iptables", "nmap", "wireshark",
        "metasploit", "kerberos", "ldap", "mitm", "cvss", "mitre", "att&ck",
        "buffer overflow", "sql injection", "xss", "csrf", "zero-day",
    ]

    recent_text = " ".join(t.user_message.lower() for t in recent)
    expert_term_count = sum(1 for term in expert_terms if term in recent_text)

    if expert_term_count >= 3 or avg_question_length > 200:
        return "ADVANCED"
    elif expert_term_count >= 1 or avg_question_length > 80:
        return "INTERMEDIATE"
    else:
        return "BEGINNER"


if __name__ == "__main__":
    main()