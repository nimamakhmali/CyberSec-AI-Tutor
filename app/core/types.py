"""
Shared type definitions for CyberSec AI Tutor.
Central location for all TypedDicts, enums, and type aliases.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, TypeAlias

# ── Enums ─────────────────────────────────────────────────────────────────────

class Intent(str, Enum):
    """User query intent categories."""
    GENERAL_CYBERSECURITY = "GENERAL_CYBERSECURITY"
    COMPANY_KNOWLEDGE = "COMPANY_KNOWLEDGE"
    COURSE_EDUCATION = "COURSE_EDUCATION"
    DOCUMENT_QA = "DOCUMENT_QA"
    SECURITY_TOOL = "SECURITY_TOOL"
    NETWORK_SECURITY = "NETWORK_SECURITY"
    LINUX_SECURITY = "LINUX_SECURITY"
    WINDOWS_SECURITY = "WINDOWS_SECURITY"
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    INCIDENT_RESPONSE = "INCIDENT_RESPONSE"
    SECURITY_ARCHITECTURE = "SECURITY_ARCHITECTURE"
    UNKNOWN = "UNKNOWN"


class UserMode(str, Enum):
    """User interaction mode."""
    STUDENT = "student"
    COMPANY = "company"
    EXPERT = "expert"


class TeachingMode(str, Enum):
    """Teaching style for educational responses."""
    SIMPLE = "simple"
    DEEP = "deep"
    EXAMPLE = "example"
    ANALOGY = "analogy"
    QUIZ = "quiz"
    SUMMARY = "summary"
    PREREQUISITES = "prerequisites"
    COMPARISON = "comparison"
    DEFENSIVE = "defensive"
    EXERCISE = "exercise"


class RetrievalMode(str, Enum):
    """Vector store retrieval algorithm."""
    SIMILARITY = "similarity"
    MMR = "mmr"


class MessageRole(str, Enum):
    """Conversation message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── Type Aliases ──────────────────────────────────────────────────────────────

Metadata: TypeAlias = dict[str, Any]
JsonDict: TypeAlias = dict[str, Any]

# Intent → categories that should be searched
INTENT_CATEGORIES: dict[Intent, list[str]] = {
    Intent.GENERAL_CYBERSECURITY: ["cybersecurity", "security_tools"],
    Intent.COMPANY_KNOWLEDGE: ["company", "policies"],
    Intent.COURSE_EDUCATION: ["course_material", "university"],
    Intent.DOCUMENT_QA: [],  # search all
    Intent.SECURITY_TOOL: ["security_tools", "cybersecurity"],
    Intent.NETWORK_SECURITY: ["network_security", "cybersecurity"],
    Intent.LINUX_SECURITY: ["linux_security", "cybersecurity"],
    Intent.WINDOWS_SECURITY: ["windows_security", "cybersecurity"],
    Intent.CRYPTOGRAPHY: ["cryptography", "cybersecurity"],
    Intent.INCIDENT_RESPONSE: ["cybersecurity", "policies"],
    Intent.SECURITY_ARCHITECTURE: ["cybersecurity", "technical_documentation"],
    Intent.UNKNOWN: [],  # search all
}

# Intents that generally require retrieval
RETRIEVAL_REQUIRED_INTENTS: set[Intent] = {
    Intent.GENERAL_CYBERSECURITY,
    Intent.COMPANY_KNOWLEDGE,
    Intent.COURSE_EDUCATION,
    Intent.DOCUMENT_QA,
    Intent.SECURITY_TOOL,
    Intent.NETWORK_SECURITY,
    Intent.LINUX_SECURITY,
    Intent.WINDOWS_SECURITY,
    Intent.CRYPTOGRAPHY,
    Intent.INCIDENT_RESPONSE,
    Intent.SECURITY_ARCHITECTURE,
}