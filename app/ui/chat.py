"""
Chat interface rendering and message handling.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import streamlit as st

from app.memory.conversation import ConversationTurn
from app.ui.components import (
    render_debug_panel,
    render_quick_action_bar,
    render_sources_section,
)


def render_chat_message(
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
    debug_info: dict[str, Any] | None = None,
    turn_index: int = 0,
    show_sources: bool = True,
    debug_mode: bool = False,
) -> None:
    """
    Render a single chat message with sources and debug info.

    Args:
        role: "user" or "assistant"
        content: Message content (Markdown)
        sources: Optional source metadata list
        debug_info: Optional debug information
        turn_index: Message index for unique keys
        show_sources: Whether to show source cards
        debug_mode: Whether to show debug panel
    """
    avatar = "🧑‍💻" if role == "user" else "🛡️"

    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

        if role == "assistant":
            # Sources section
            if show_sources and sources:
                render_sources_section(sources)

            # Debug panel
            if debug_mode and debug_info:
                render_debug_panel(debug_info)

            # Feedback (only for assistant)
            st.markdown(
                """
                <div style="margin-top:0.5rem; padding-top:0.5rem; 
                     border-top:1px solid #1e293b;">
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2, col_space = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"thumbs_up_{turn_index}", help="Helpful"):
                    if "feedback" not in st.session_state:
                        st.session_state["feedback"] = {}
                    st.session_state["feedback"][turn_index] = "helpful"
                    st.toast("Thanks for your feedback! 👍")

            with col2:
                if st.button("👎", key=f"thumbs_down_{turn_index}", help="Not helpful"):
                    if "feedback" not in st.session_state:
                        st.session_state["feedback"] = {}
                    st.session_state["feedback"][turn_index] = "not_helpful"
                    st.toast("Thanks for your feedback! We'll work to improve.")


def render_conversation_history(
    messages: list[dict[str, Any]],
    show_sources: bool = True,
    debug_mode: bool = False,
) -> None:
    """
    Render the complete conversation history.

    Args:
        messages: List of message dicts with role, content, sources, debug_info
        show_sources: Whether to show sources
        debug_mode: Whether to show debug info
    """
    for i, msg in enumerate(messages):
        render_chat_message(
            role=msg["role"],
            content=msg["content"],
            sources=msg.get("sources"),
            debug_info=msg.get("debug_info"),
            turn_index=i,
            show_sources=show_sources,
            debug_mode=debug_mode,
        )


def handle_export(memory_json: dict[str, Any]) -> None:
    """
    Handle conversation export trigger.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Markdown export
    md_content = _build_markdown_export(memory_json)
    st.download_button(
        label="📄 Download Markdown",
        data=md_content,
        file_name=f"cybersec_conversation_{timestamp}.md",
        mime="text/markdown",
        key=f"dl_md_{timestamp}",
    )

    # JSON export
    json_content = json.dumps(memory_json, indent=2, default=str)
    st.download_button(
        label="📊 Download JSON",
        data=json_content,
        file_name=f"cybersec_conversation_{timestamp}.json",
        mime="application/json",
        key=f"dl_json_{timestamp}",
    )


def _build_markdown_export(memory_json: dict[str, Any]) -> str:
    """Build Markdown export from memory JSON."""
    lines = [
        f"# CyberSec AI Tutor — Conversation Export",
        f"**Date:** {memory_json.get('created_at', 'Unknown')}",
        f"**Mode:** {memory_json.get('mode', 'Unknown')}",
        f"**Model:** {memory_json.get('model', 'Unknown')}",
        "",
    ]

    if memory_json.get("summary"):
        lines.extend([
            "## Summary",
            memory_json["summary"],
            "",
        ])

    lines.append("## Conversation")

    for i, turn in enumerate(memory_json.get("turns", []), 1):
        lines.extend([
            f"### Turn {i}",
            f"**User:** {turn.get('user', '')}",
            "",
            f"**Assistant:** {turn.get('assistant', '')}",
            "",
        ])

        if turn.get("sources"):
            lines.append("**Sources:**")
            for j, src in enumerate(turn["sources"], 1):
                fname = src.get("filename", src.get("source", "Unknown"))
                lines.append(f"- [{j}] {fname}")
            lines.append("")

    return "\n".join(lines)