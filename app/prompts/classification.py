"""
Intent classification for query routing.
Uses rule-based classification with optional LLM fallback.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Intent(str, Enum):
    """Query intent classification."""
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


# Keyword patterns for each intent
INTENT_PATTERNS: dict[Intent, list[str]] = {
    Intent.SECURITY_TOOL: [
        r"\bnmap\b", r"\bwireshark\b", r"\bburp\b", r"\bmetasploit\b",
        r"\baircrack\b", r"\bjohn\s+the\s+ripper\b", r"\bhashcat\b",
        r"\bnessus\b", r"\bopenvas\b", r"\bhydra\b", r"\bsqlmap\b",
        r"\bsnort\b", r"\bzeek\b", r"\bsuricata\b", r"\bghost\b",
    ],
    Intent.NETWORK_SECURITY: [
        r"\btcp\b", r"\budp\b", r"\bsyn\s+flood\b", r"\bdos\b",
        r"\bddos\b", r"\barp\s+spoofing\b", r"\bdns\s+poisoning\b",
        r"\bman.in.the.middle\b", r"\bmitm\b", r"\bpacket\s+sniff",
        r"\bfirewall\b", r"\brout\b", r"\bswitch\b", r"\bvlan\b",
        r"\bsubnet\b", r"\bcidr\b", r"\bnat\b", r"\bport\s+scan",
        r"\bnetwork\s+securit", r"\bprotocol\b",
    ],
    Intent.LINUX_SECURITY: [
        r"\blinux\b", r"\biptables\b", r"\bnftables\b", r"\bselinux\b",
        r"\bapparmor\b", r"\bsudo\b", r"\bchmod\b", r"\bchown\b",
        r"\bssh\b", r"\bbash\b", r"\bshell\b", r"\bdaemon\b",
        r"\bsystemd\b", r"\bcron\b", r"\bkernel\b",
    ],
    Intent.WINDOWS_SECURITY: [
        r"\bwindows\b", r"\bactive\s+directory\b", r"\bkerberos\b",
        r"\bldap\b", r"\bntlm\b", r"\bpowershell\b", r"\bregistry\b",
        r"\bgroup\s+policy\b", r"\bgpo\b", r"\bwindows\s+defender\b",
        r"\bbitlocker\b", r"\bwmi\b", r"\bsmb\b", r"\brdp\b",
    ],
    Intent.CRYPTOGRAPHY: [
        r"\bcrypt", r"\bencrypt", r"\bdecrypt", r"\bhash\b", r"\bhashing\b",
        r"\baes\b", r"\brsa\b", r"\bsha\b", r"\bmd5\b", r"\bpki\b",
        r"\bcertificate\b", r"\btls\b", r"\bssl\b", r"\bcipher\b",
        r"\bkey\s+exchange\b", r"\bdiffie.hellman\b", r"\belliptic\b",
        r"\bdigital\s+signature\b", r"\bhmac\b",
    ],
    Intent.INCIDENT_RESPONSE: [
        r"\bincident\s+response\b", r"\bforensic", r"\bmalware\b",
        r"\bransom", r"\bthreat\s+hunt", r"\bsoc\b", r"\bsiem\b",
        r"\bioc\b", r"\bcontainment\b", r"\beradication\b",
        r"\brecovery\b", r"\bpost.mortem\b",
    ],
    Intent.SECURITY_ARCHITECTURE: [
        r"\bzero.trust\b", r"\bdefense\s+in\s+depth\b", r"\bsegment",
        r"\barchitectur", r"\bhardening\b", r"\bbaseline\b",
        r"\bsecurity\s+design\b", r"\bmitre\b", r"\batt&ck\b",
        r"\bcve\b", r"\bcvss\b",
    ],
    Intent.COMPANY_KNOWLEDGE: [
        r"\bour\s+company\b", r"\byour\s+company\b", r"\bcompany\s+service",
        r"\bcompany\s+product", r"\bcompany\s+capabilit",
        r"\bwhat\s+(do\s+)?we\s+offer\b", r"\bour\s+service",
        r"\bour\s+product", r"\bour\s+team\b", r"\babout\s+(the\s+)?company",
        r"\bشرکت\b", r"\bخدمات\s+ما\b", r"\bمحصولات\s+ما\b",
    ],
    Intent.COURSE_EDUCATION: [
        r"\bwhat\s+is\b", r"\bexplain\b", r"\bdefine\b",
        r"\bhow\s+does\b", r"\bhow\s+do\b", r"\bwhy\s+is\b",
        r"\bteach\s+me\b", r"\blearn\b", r"\bquiz\b", r"\bexercise\b",
        r"\bexample\b", r"\bstudy\b", r"\bcourse\b",
        r"\bتوضیح\b", r"\bیاد\b", r"\bچیست\b", r"\bچگونه\b",
    ],
    Intent.DOCUMENT_QA: [
        r"\baccording\s+to\b", r"\bin\s+the\s+document\b",
        r"\bfrom\s+the\s+(document|pdf|file)\b",
        r"\bدر\s+سند\b", r"\bطبق\s+مدرک\b",
    ],
}


@dataclass
class ClassificationResult:
    """Result of intent classification."""
    intent: Intent
    confidence: float
    method: str  # "rule_based" or "llm"
    matched_patterns: list[str]

    @property
    def category_filter(self) -> str | None:
        """Map intent to vector store category filter."""
        mapping = {
            Intent.COMPANY_KNOWLEDGE: "company",
            Intent.LINUX_SECURITY: "linux_security",
            Intent.WINDOWS_SECURITY: "windows_security",
            Intent.CRYPTOGRAPHY: "cryptography",
            Intent.SECURITY_TOOL: "security_tools",
            Intent.NETWORK_SECURITY: "network_security",
            Intent.COURSE_EDUCATION: None,  # Search all
            Intent.GENERAL_CYBERSECURITY: None,
        }
        return mapping.get(self.intent)


def classify_intent(
    query: str,
    conversation_context: str = "",
) -> ClassificationResult:
    """
    Classify the intent of a user query using rule-based pattern matching.
    This avoids an LLM call for every query.

    Args:
        query: User query text
        conversation_context: Recent conversation for context

    Returns:
        ClassificationResult with intent and confidence
    """
    combined_text = (query + " " + conversation_context).lower()
    scores: dict[Intent, float] = {}
    matched_patterns: dict[Intent, list[str]] = {}

    for intent, patterns in INTENT_PATTERNS.items():
        matches = []
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                matches.append(pattern)
        if matches:
            scores[intent] = len(matches) / len(patterns)
            matched_patterns[intent] = matches

    if not scores:
        return ClassificationResult(
            intent=Intent.GENERAL_CYBERSECURITY,
            confidence=0.5,
            method="rule_based",
            matched_patterns=[],
        )

    # Priority resolution when multiple intents match
    # Company knowledge takes priority for company-specific queries
    if Intent.COMPANY_KNOWLEDGE in scores:
        best_intent = Intent.COMPANY_KNOWLEDGE
    else:
        best_intent = max(scores, key=lambda i: scores[i])

    return ClassificationResult(
        intent=best_intent,
        confidence=min(scores[best_intent] * 2, 1.0),
        method="rule_based",
        matched_patterns=matched_patterns.get(best_intent, []),
    )