"""
Custom CSS styles for CyberSec AI Tutor.
Dark cybersecurity aesthetic with professional design language.
"""
from __future__ import annotations

CUSTOM_CSS = """
<style>
/* ── Base & Typography ──────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #00d4ff;
    --primary-dim: #0099bb;
    --secondary: #7c3aed;
    --accent: #22d3ee;
    --bg-primary: #0a0e1a;
    --bg-secondary: #0f1629;
    --bg-card: #141b2d;
    --bg-card-hover: #1a2438;
    --border: #1e293b;
    --border-accent: #0e7490;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --code-bg: #0d1117;
}

/* Main app background */
.stApp {
    background: var(--bg-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
}

/* Main content area */
.main .block-container {
    padding: 1rem 1.5rem 5rem 1.5rem;
    max-width: 900px;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1rem 1rem;
}

/* ── Chat Messages ───────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}

/* User message */
[data-testid="stChatMessage"][data-author="user"] {
    background: linear-gradient(135deg, #1e3a5f 0%, #152c4a 100%) !important;
    border-left: 3px solid var(--primary) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
}

/* Assistant message */
[data-testid="stChatMessage"][data-author="assistant"] {
    background: var(--bg-card) !important;
    border-left: 3px solid var(--secondary) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 0.5rem 0 !important;
}

/* ── Code Blocks ─────────────────────────────────────────────────────────── */
code {
    background: var(--code-bg) !important;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.875em !important;
    padding: 0.15em 0.4em !important;
    border-radius: 4px !important;
    border: 1px solid var(--border) !important;
}

pre {
    background: var(--code-bg) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    overflow-x: auto !important;
}

pre code {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: #c9d1d9 !important;
}

/* ── Source Cards ────────────────────────────────────────────────────────── */
.source-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.85em;
    color: var(--text-secondary);
    transition: border-color 0.2s;
}

.source-card:hover {
    border-color: var(--primary);
    color: var(--text-primary);
}

.source-number {
    color: var(--primary);
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.source-filename {
    color: var(--text-primary);
    font-weight: 500;
}

.source-meta {
    color: var(--text-muted);
    font-size: 0.8em;
}

.source-category {
    display: inline-block;
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: var(--primary);
    font-size: 0.75em;
    padding: 0.1em 0.5em;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Welcome Cards ───────────────────────────────────────────────────────── */
.welcome-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 0.5rem 0;
    cursor: pointer;
    transition: all 0.2s;
}

.welcome-card:hover {
    border-color: var(--primary-dim);
    background: var(--bg-card-hover);
    transform: translateX(2px);
}

.welcome-card-icon {
    font-size: 1.2em;
    margin-right: 0.5rem;
}

.welcome-card-text {
    color: var(--text-secondary);
    font-size: 0.9em;
}

/* ── Status Indicators ───────────────────────────────────────────────────── */
.status-online {
    color: var(--success);
}

.status-offline {
    color: var(--error);
}

.status-warning {
    color: var(--warning);
}

/* ── Mode Badges ─────────────────────────────────────────────────────────── */
.mode-badge {
    display: inline-block;
    padding: 0.2em 0.8em;
    border-radius: 20px;
    font-size: 0.75em;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}

.mode-student {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #10b981;
}

.mode-company {
    background: rgba(124, 58, 237, 0.1);
    border: 1px solid rgba(124, 58, 237, 0.4);
    color: #8b5cf6;
}

.mode-expert {
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid rgba(0, 212, 255, 0.4);
    color: var(--primary);
}

/* ── Metric Cards ────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
}

/* ── Input ───────────────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: 12px !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    font-size: 0.85em !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background: rgba(0, 212, 255, 0.05) !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0e7490, #0891b2) !important;
    border: none !important;
    color: white !important;
}

/* ── Expanders ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

[data-testid="stExpander"]:hover {
    border-color: var(--border-accent) !important;
}

/* ── Select boxes ────────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

/* ── Sliders ─────────────────────────────────────────────────────────────── */
[data-testid="stSlider"] {
    color: var(--primary) !important;
}

/* ── Markdown ────────────────────────────────────────────────────────────── */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text-primary) !important;
}

.stMarkdown a {
    color: var(--primary) !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-accent);
}

/* ── Logo area ───────────────────────────────────────────────────────────── */
.logo-container {
    text-align: center;
    padding: 0.5rem 0 1.5rem 0;
}

.logo-title {
    font-size: 1.1em;
    font-weight: 700;
    color: var(--primary);
    letter-spacing: 0.05em;
    margin-top: 0.5rem;
}

.logo-subtitle {
    font-size: 0.75em;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── Debug panel ─────────────────────────────────────────────────────────── */
.debug-panel {
    background: var(--code-bg);
    border: 1px solid var(--border-accent);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8em;
    color: var(--text-secondary);
}

/* ── Dividers ────────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Toast messages ──────────────────────────────────────────────────────── */
[data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── Hide Streamlit branding ─────────────────────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Feedback buttons ────────────────────────────────────────────────────── */
.feedback-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    border-radius: 20px;
    padding: 0.2em 0.8em;
    font-size: 0.8em;
    cursor: pointer;
    transition: all 0.2s;
    margin-right: 0.5em;
}

.feedback-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}
</style>
"""


LOGO_SVG = """
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Shield background -->
  <path d="M32 4L8 14V32C8 44.8 18.4 56.6 32 60C45.6 56.6 56 44.8 56 32V14L32 4Z" 
        fill="#0f1629" stroke="#00d4ff" stroke-width="1.5"/>
  
  <!-- Network nodes -->
  <circle cx="32" cy="24" r="4" fill="#00d4ff" opacity="0.9"/>
  <circle cx="20" cy="36" r="3" fill="#7c3aed" opacity="0.8"/>
  <circle cx="44" cy="36" r="3" fill="#7c3aed" opacity="0.8"/>
  <circle cx="26" cy="46" r="2.5" fill="#22d3ee" opacity="0.7"/>
  <circle cx="38" cy="46" r="2.5" fill="#22d3ee" opacity="0.7"/>
  
  <!-- Network connections -->
  <line x1="32" y1="24" x2="20" y2="36" stroke="#00d4ff" stroke-width="1" opacity="0.5"/>
  <line x1="32" y1="24" x2="44" y2="36" stroke="#00d4ff" stroke-width="1" opacity="0.5"/>
  <line x1="20" y1="36" x2="26" y2="46" stroke="#7c3aed" stroke-width="1" opacity="0.5"/>
  <line x1="44" y1="36" x2="38" y2="46" stroke="#7c3aed" stroke-width="1" opacity="0.5"/>
  <line x1="26" y1="46" x2="38" y2="46" stroke="#22d3ee" stroke-width="1" opacity="0.4"/>
  
  <!-- AI sparkle -->
  <path d="M32 16 L33.5 20 L37 20 L34.2 22.5 L35.3 26 L32 23.8 L28.7 26 L29.8 22.5 L27 20 L30.5 20 Z" 
        fill="#00d4ff" opacity="0.6"/>
</svg>
"""