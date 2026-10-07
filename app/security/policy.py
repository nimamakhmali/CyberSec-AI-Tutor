"""
Cybersecurity content policy enforcement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Topics that should trigger defensive framing
SENSITIVE_TOPICS = [
    "exploit", "payload", "rootkit", "backdoor", "keylogger",
    "ransomware creation", "malware development", "zero-day",
    "ddos attack against", "scanning without permission",
    "bypass authentication", "crack password of",
    "hack into", "gain unauthorized",
    "buffer overflow", "sql injection", "xss", "cross-site scripting",
]

# Topics that are clearly educational/legitimate
LEGITIMATE_TOPICS = [
    "how does", "what is", "explain", "concept", "theory",
    "defense", "detection", "prevention", "mitigation",
    "lab environment", "ctf", "penetration testing methodology",
    "security research",
]


@dataclass
class PolicyResult:
    """Result of content policy evaluation."""

    allowed: bool
    requires_defensive_framing: bool
    guidance_note: str


def evaluate_content_policy(query: str) -> PolicyResult:
    """
    Evaluate whether a query requires special handling.

    Args:
        query: User query text

    Returns:
        PolicyResult with guidance
    """
    query_lower = query.lower()

    # Check for clearly legitimate educational context
    has_educational_markers = any(
        marker in query_lower for marker in LEGITIMATE_TOPICS
    )

    # Check for sensitive topics
    sensitive_matches = [
        topic for topic in SENSITIVE_TOPICS
        if topic in query_lower
    ]

    if not sensitive_matches:
        return PolicyResult(
            allowed=True,
            requires_defensive_framing=False,
            guidance_note="",
        )

    # Sensitive topic with educational context
    if has_educational_markers:
        return PolicyResult(
            allowed=True,
            requires_defensive_framing=True,
            guidance_note=(
                "⚠️ *Educational context: This information is provided for "
                "security education and defensive purposes. Always obtain "
                "proper authorization before testing any system.*"
            ),
        )

    # Sensitive topic without clear educational context
    return PolicyResult(
        allowed=True,  # Still allow — educational system
        requires_defensive_framing=True,
        guidance_note=(
            "⚠️ *This topic is explained for educational and defensive "
            "security purposes only. Unauthorized use of these techniques "
            "against systems you don't own is illegal and unethical. "
            "Always work in authorized lab environments.*"
        ),
    )