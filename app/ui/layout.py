"""
Sidebar layout and controls.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from app.llm.model_manager import RECOMMENDED_CHAT_MODELS, get_model_status
from app.ui.components import render_logo_and_title, render_status_indicator
from app.ui.styles import CUSTOM_CSS
from config.settings import get_settings


def inject_css() -> None:
    """Inject custom CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_sidebar(
    ollama_connected: bool,
    doc_count: int,
) -> dict[str, Any]:
    """
    Render the complete sidebar and return user settings.

    Args:
        ollama_connected: Whether Ollama is reachable
        doc_count: Number of documents in vector store

    Returns:
        Dict of user-selected settings
    """
    settings = get_settings()

    with st.sidebar:
        render_logo_and_title()

        st.markdown("---")

        # ── Status ─────────────────────────────────────────────────────────
        render_status_indicator(
            ollama_connected=ollama_connected,
            doc_count=doc_count,
            model_name=st.session_state.get("active_model", settings.ollama_chat_model),
        )

        st.markdown("---")

        # ── Mode Selection ─────────────────────────────────────────────────
        st.markdown("**🎯 Mode**")
        mode = st.selectbox(
            "Select Mode",
            options=["Student", "Company Knowledge", "Expert"],
            index=["Student", "Company Knowledge", "Expert"].index(
                st.session_state.get("mode", "Student")
            ),
            key="mode_selector",
            label_visibility="collapsed",
            help=(
                "Student: Educational explanations\n"
                "Company Knowledge: Company-specific information\n"
                "Expert: Technical deep-dives"
            ),
        )

        # Teaching mode (only in Student mode)
        teaching_mode = False
        if mode == "Student":
            teaching_mode = st.toggle(
                "🎓 Teaching Mode",
                value=st.session_state.get("teaching_mode", False),
                help="Socratic teaching style — guides you to discover answers",
            )

        st.markdown("---")

        # ── Model Selection ────────────────────────────────────────────────
        st.markdown("**🤖 Model**")

        # Get available models
        available_models = []
        try:
            model_status = get_model_status(settings)
            available_models = model_status.available_models
        except Exception:
            pass

        # Combine available + recommended for the dropdown
        all_model_options = list(set(
            [settings.ollama_chat_model]
            + available_models
            + RECOMMENDED_CHAT_MODELS[:3]
        ))
        all_model_options.sort()

        current_model = st.session_state.get("active_model", settings.ollama_chat_model)
        if current_model not in all_model_options:
            all_model_options.insert(0, current_model)

        selected_model = st.selectbox(
            "Chat Model",
            options=all_model_options,
            index=all_model_options.index(current_model) if current_model in all_model_options else 0,
            label_visibility="collapsed",
        )

        st.markdown("---")

        # ── Generation Settings ────────────────────────────────────────────
        with st.expander("⚙️ Generation Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("temperature", settings.temperature),
                step=0.05,
                help="Lower = more focused, Higher = more creative",
            )

            streaming = st.toggle(
                "Streaming",
                value=st.session_state.get("streaming", True),
                help="Show response as it generates",
            )

        # ── Retrieval Settings ─────────────────────────────────────────────
        with st.expander("🔍 Retrieval Settings"):
            show_sources = st.toggle(
                "Show Sources",
                value=st.session_state.get("show_sources", True),
                help="Display document sources with answers",
            )

            retrieval_k = st.slider(
                "Retrieved Chunks",
                min_value=2,
                max_value=12,
                value=st.session_state.get("retrieval_k", settings.retrieval_k),
                help="Number of document chunks to retrieve",
            )

        # ── Developer Options ──────────────────────────────────────────────
        with st.expander("🔧 Developer Options"):
            debug_mode = st.toggle(
                "Debug Mode",
                value=st.session_state.get("debug_mode", settings.debug),
                help="Show retrieval scores, intent, debug info",
            )

        st.markdown("---")

        # ── Conversation Controls ──────────────────────────────────────────
        st.markdown("**💬 Conversation**")

        col1, col2 = st.columns(2)
        with col1:
            new_chat = st.button("🆕 New Chat", use_container_width=True)
        with col2:
            export_md = st.button("📥 Export", use_container_width=True)

        if new_chat:
            st.session_state["trigger_new_chat"] = True

        if export_md:
            st.session_state["trigger_export"] = True

        st.markdown("---")
        st.markdown(
            f"""
            <div style="text-align:center; color:#334155; font-size:0.7em;">
                v{settings.app_version} · Local-First AI
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "mode": mode,
        "teaching_mode": teaching_mode,
        "selected_model": selected_model,
        "temperature": temperature,
        "streaming": streaming,
        "show_sources": show_sources,
        "retrieval_k": retrieval_k,
        "debug_mode": debug_mode,
    }