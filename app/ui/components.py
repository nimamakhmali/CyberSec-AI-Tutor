"""
Reusable UI components for the CyberSec AI Tutor.
"""
from __future__ import annotations

import json
from typing import Any

import streamlit as st
import hashlib

from app.ui.styles import LOGO_SVG

def _stable_hash(text: str) -> str:
    """Generate a stable short hash for UI keys."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def render_logo_and_title() -> None:
    """Render the CyberSec AI Tutor logo and title in sidebar."""
    st.markdown(
        f"""
        <div class="logo-container">
            {LOGO_SVG}
            <div class="logo-title">CyberSec AI Tutor</div>
            <div class="logo-subtitle">Local · Private · Intelligent</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mode_badge(mode: str) -> None:
    """Render a styled mode badge."""
    mode_lower = mode.lower().replace(" ", "_").replace("knowledge", "company")
    css_class = f"mode-{mode_lower}"
    st.markdown(
        f'<span class="mode-badge {css_class}">{mode}</span>',
        unsafe_allow_html=True,
    )


def render_source_card(metadata: dict[str, Any], index: int) -> None:
    """
    Render a styled source reference card.

    Args:
        metadata: Document metadata dict
        index: 1-based citation index
    """
    filename = metadata.get("filename", metadata.get("source", "Unknown"))
    category = metadata.get("category", "")
    section = metadata.get("section", "")
    page = metadata.get("page_number", "")
    title = metadata.get("title", "")

    display_name = title or filename

    meta_parts = []
    if section:
        meta_parts.append(f"📍 {section}")
    if page:
        meta_parts.append(f"📄 Page {page}")

    meta_str = " · ".join(meta_parts)

    category_badge = ""
    if category:
        category_badge = f'<span class="source-category">{category}</span>'

    st.markdown(
        f"""
        <div class="source-card">
            <span class="source-number">[{index}]</span>
            <span class="source-filename"> {display_name}</span>
            {category_badge}
            {'<br><span class="source-meta">' + meta_str + '</span>' if meta_str else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources_section(sources: list[dict[str, Any]]) -> None:
    """
    Render all source cards in an expandable section.

    Args:
        sources: List of source metadata dicts
    """
    if not sources:
        return

    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for i, source in enumerate(sources, 1):
            render_source_card(source, i)


def render_debug_panel(debug_info: dict[str, Any]) -> None:
    """
    Render developer debug information.

    Args:
        debug_info: Debug information from workflow state
    """
    with st.expander("🔧 Debug Information", expanded=False):
        st.markdown(
            f"""<div class="debug-panel">
            <pre>{json.dumps(debug_info, indent=2, default=str)}</pre>
            </div>""",
            unsafe_allow_html=True,
        )


def render_status_indicator(
    ollama_connected: bool,
    doc_count: int,
    model_name: str,
) -> None:
    """
    Render system status in sidebar.
    """
    col1, col2 = st.columns(2)

    with col1:
        status_icon = "🟢" if ollama_connected else "🔴"
        status_text = "Connected" if ollama_connected else "Offline"
        st.markdown(f"{status_icon} **Ollama**\n\n{status_text}")

    with col2:
        st.markdown(f"📚 **Knowledge Base**\n\n{doc_count} chunks")

    if model_name:
        st.caption(f"🤖 Model: `{model_name}`")


def render_feedback_buttons(turn_index: int) -> str | None:
    """
    Render helpful/not helpful feedback buttons.

    Args:
        turn_index: Index of the conversation turn

    Returns:
        "helpful", "not_helpful", or None
    """
    col1, col2, col3 = st.columns([1, 1, 6])
    feedback = None

    with col1:
        if st.button("👍", key=f"helpful_{turn_index}", help="Helpful"):
            feedback = "helpful"
    with col2:
        if st.button("👎", key=f"not_helpful_{turn_index}", help="Not helpful"):
            feedback = "not_helpful"

    return feedback


def render_quick_action_bar(question: str) -> str | None:
    """
    Render quick action buttons that modify the current question.

    Args:
        question: Current question context

    Returns:
        Modified question or None
    """
    st.markdown("**Quick Actions:**")
    actions = {
        "🔤 Explain Simply": f"Please explain this in simple terms: {question}",
        "🔬 Explain Deeply": f"Please provide a deep technical explanation of: {question}",
        "💡 Give Example": f"Please give a practical example of: {question}",
        "🎓 Quiz Me": f"Create a short quiz about: {question}",
        "🛡️ Defensive View": f"Explain the defensive perspective and countermeasures for: {question}",
        "🔄 Analogy": f"Explain using a real-world analogy: {question}",
    }

    import hashlib
    
    def _stable_hash(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    cols = st.columns(3)
    for i, (label, modified_q) in enumerate(actions.items()):
        with cols[i % 3]:
            if st.button(label, key=f"action_{_stable_hash(label)}_{_stable_hash(question)}"):
                return modified_q

    return None


def render_welcome_screen() -> str | None:
    """
    Render the welcome screen with suggested questions.
    Returns selected question or None.
    """
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <h1 style="color: #00d4ff; font-size: 2em; font-weight: 700; margin-bottom: 0.25rem;">
                CyberSec AI Tutor
            </h1>
            <p style="color: #64748b; font-size: 1em; margin-bottom: 0;">
                Your local, private AI for cybersecurity education
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎓 Learning & Concepts**")
        questions_left = [
            ("🔍", "What is Nmap and how does it work?"),
            ("🌐", "Explain TCP SYN scanning"),
            ("🔐", "What is the CIA Triad?"),
            ("🛡️", "What is the difference between IDS and IPS?"),
            ("🔥", "How does a firewall work?"),
        ]
        for icon, q in questions_left:
            if st.button(f"{icon} {q}", key=f"welcome_{_stable_hash(q)}", use_container_width=True):
                return q

    with col2:
        st.markdown("**⚙️ Security Tools & Concepts**")
        questions_right = [
            ("🔑", "Explain symmetric vs asymmetric encryption"),
            ("🕵️", "How does Wireshark capture network traffic?"),
            ("⚡", "What is a SQL injection attack?"),
            ("🔮", "What is a VPN and how does it protect you?"),
            ("📊", "Quiz me on network security concepts"),
        ]
        for icon, q in questions_right:
            if st.button(f"{icon} {q}", key=f"welcome_{_stable_hash(q)}", use_container_width=True):
                return q

    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #475569; font-size: 0.8em; padding: 0.5rem 0;">
            🔒 Local · Private · No data sent to external servers
        </div>
        """,
        unsafe_allow_html=True,
    )

    return None