"""
Input sanitization and validation.
"""
from __future__ import annotations

import re

from app.core.exceptions import InputValidationError
from app.core.logging_config import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

# Patterns that indicate potential prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"forget\s+everything\s+(you\s+)?(were\s+)?told",
    r"you\s+are\s+now\s+(a\s+)?different",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?instructions",
    r"bypass\s+(safety|filter|restriction)",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+you\s+(have\s+)?no\s+(restriction|limit|filter)",
]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input.
    
    - Strip leading/trailing whitespace
    - Remove null bytes
    - Normalize line endings
    - Apply length limit

    Args:
        text: Raw user input

    Returns:
        Sanitized text

    Raises:
        InputValidationError: If input is invalid
    """
    settings = get_settings()

    if not text or not text.strip():
        raise InputValidationError("Empty input received")

    # Basic cleanup
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()

    # Length check
    if len(text) > settings.max_input_length:
        raise InputValidationError(
            f"Input too long: {len(text)} characters (max: {settings.max_input_length})",
            details="Please shorten your message",
        )

    return text


def detect_injection_attempt(text: str) -> tuple[bool, str]:
    """
    Detect potential prompt injection patterns.

    Args:
        text: User input to check

    Returns:
        Tuple of (is_suspicious, reason)
    """
    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(
                "Potential injection detected",
                pattern=pattern,
                input_preview=text[:100],
            )
            return True, f"Suspicious pattern detected: {pattern}"

    return False, ""


def validate_and_sanitize(text: str) -> str:
    """
    Full validation and sanitization pipeline.

    Args:
        text: Raw user input

    Returns:
        Clean, validated input

    Raises:
        InputValidationError: If input is invalid or suspicious
    """
    settings = get_settings()

    # Basic sanitization
    clean = sanitize_input(text)

    # Injection detection (warn but don't block — log for monitoring)
    if settings.enable_content_filter:
        is_suspicious, reason = detect_injection_attempt(clean)
        if is_suspicious:
            logger.warning("Suspicious input processed with extra caution", reason=reason)
            # We don't block — just log and let the system prompt handle it
            # A production system might add a warning to the context

    return clean