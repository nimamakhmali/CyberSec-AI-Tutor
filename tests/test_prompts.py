"""
Tests for prompt components.
"""
from __future__ import annotations

import pytest

from app.prompts.classification import Intent, classify_intent, ClassificationResult
from app.prompts.education import get_mode_instructions, get_depth_instruction, format_quiz_prompt
from app.prompts.rag import build_rag_prompt, build_no_context_prompt, build_simple_prompt
from app.prompts.system import get_system_prompt


class TestClassification:
    """Tests for intent classification."""

    def test_intent_enum_values(self):
        assert Intent.GENERAL_CYBERSECURITY == "GENERAL_CYBERSECURITY"
        assert Intent.COMPANY_KNOWLEDGE == "COMPANY_KNOWLEDGE"
        assert Intent.UNKNOWN == "UNKNOWN"

    def test_classify_security_tool(self):
        result = classify_intent("How to use nmap for port scanning?")
        assert result.intent == Intent.SECURITY_TOOL
        assert result.confidence > 0
        assert result.method == "rule_based"
        assert any("nmap" in p for p in result.matched_patterns)

    def test_classify_network_security(self):
        result = classify_intent("Explain TCP SYN flood attack")
        assert result.intent == Intent.NETWORK_SECURITY

    def test_classify_linux_security(self):
        result = classify_intent("How to configure iptables firewall?")
        assert result.intent == Intent.LINUX_SECURITY

    def test_classify_windows_security(self):
        result = classify_intent("Explain Active Directory Kerberos")
        assert result.intent == Intent.WINDOWS_SECURITY

    def test_classify_cryptography(self):
        result = classify_intent("Difference between AES and RSA encryption")
        assert result.intent == Intent.CRYPTOGRAPHY

    def test_classify_incident_response(self):
        result = classify_intent("Incident response procedure for ransomware")
        assert result.intent == Intent.INCIDENT_RESPONSE

    def test_classify_security_architecture(self):
        result = classify_intent("Zero trust architecture principles")
        assert result.intent == Intent.SECURITY_ARCHITECTURE

    def test_classify_company_knowledge(self):
        result = classify_intent("What services does our company offer?")
        assert result.intent == Intent.COMPANY_KNOWLEDGE

    def test_classify_course_education(self):
        result = classify_intent("Teach me about network security")
        assert result.intent == Intent.COURSE_EDUCATION

    def test_classify_document_qa(self):
        result = classify_intent("According to the document, what is the policy?")
        assert result.intent == Intent.DOCUMENT_QA

    def test_classify_persian_queries(self):
        # Persian educational queries
        result = classify_intent("توضیح دهید TCP چیست")
        assert result.intent == Intent.COURSE_EDUCATION

    def test_classify_unknown_fallback(self):
        result = classify_intent("Random unrelated text xyz123")
        assert result.intent == Intent.GENERAL_CYBERSECURITY
        assert result.confidence == 0.5

    def test_category_filter_mapping(self):
        result = classify_intent("Our company services")
        assert result.category_filter == "company"

        result = classify_intent("Linux iptables")
        assert result.category_filter == "linux_security"

        result = classify_intent("What is TCP?")
        assert result.category_filter is None  # Search all


class TestEducationPrompts:
    """Tests for educational prompt helpers."""

    def test_get_mode_instructions_student(self):
        instructions = get_mode_instructions("Student")
        assert "STUDENT MODE" in instructions
        assert "university student" in instructions.lower()

    def test_get_mode_instructions_company(self):
        instructions = get_mode_instructions("Company Knowledge")
        assert "COMPANY KNOWLEDGE" in instructions
        assert "company documentation" in instructions.lower()

    def test_get_mode_instructions_expert(self):
        instructions = get_mode_instructions("Expert")
        assert "EXPERT MODE" in instructions
        assert "technical proficiency" in instructions.lower()

    def test_get_mode_instructions_unknown_defaults_student(self):
        instructions = get_mode_instructions("Unknown")
        assert "STUDENT MODE" in instructions

    def test_get_depth_instruction(self):
        assert "simple terms" in get_depth_instruction("beginner")
        assert "balanced technical" in get_depth_instruction("intermediate")
        assert "deep technical" in get_depth_instruction("advanced")
        assert "quiz" in get_depth_instruction("quiz").lower()
        assert "exam" in get_depth_instruction("exam").lower()
        assert "analogy" in get_depth_instruction("analogy").lower()
        assert "defensive" in get_depth_instruction("defense").lower()

    def test_format_quiz_prompt(self):
        prompt = format_quiz_prompt("TCP", num_questions=3, difficulty="beginner")
        assert "3" in prompt
        assert "TCP" in prompt
        assert "beginner" in prompt
        assert "conceptual" in prompt.lower()


class TestRAGPrompts:
    """Tests for RAG prompt templates."""

    def test_build_rag_prompt(self):
        prompt = build_rag_prompt()
        assert hasattr(prompt, "format_messages")
        # Check template variables
        messages = prompt.format_messages(
            system_prompt="Test system",
            chat_history=[],
            context="Test context",
            question="Test question",
        )
        # When chat_history is empty, we get 2 messages: system + human
        assert len(messages) == 2
        assert "Test system" in messages[0].content
        assert "Test context" in messages[1].content
        assert "Test question" in messages[1].content

    def test_build_no_context_prompt(self):
        prompt = build_no_context_prompt()
        messages = prompt.format_messages(
            system_prompt="Test system",
            chat_history=[],
            question="Test question",
        )
        assert len(messages) == 2
        assert "No relevant documents" in messages[1].content

    def test_build_simple_prompt(self):
        prompt = build_simple_prompt()
        messages = prompt.format_messages(
            system_prompt="Test system",
            chat_history=[],
            question="Test question",
        )
        assert len(messages) == 2
        assert messages[1].content == "Test question"


class TestSystemPrompt:
    """Tests for system prompt generation."""

    def test_get_system_prompt_basic(self):
        prompt = get_system_prompt(mode="Student", user_level="INTERMEDIATE")
        assert "CYBERSEC AI TUTOR" in prompt
        assert "STUDENT" in prompt
        assert "INTERMEDIATE" in prompt
        assert "IDENTITY" in prompt
        assert "ROLE" in prompt
        assert "PROMPT INJECTION DEFENSE" in prompt

    def test_get_system_prompt_teaching_mode(self):
        prompt = get_system_prompt(mode="Student", user_level="BEGINNER", teaching_mode=True)
        assert "TEACHING MODE (ACTIVE)" in prompt
        assert "Socratic tutor" in prompt

    def test_get_system_prompt_all_modes(self):
        for mode in ["Student", "Company Knowledge", "Expert"]:
            prompt = get_system_prompt(mode=mode, user_level="INTERMEDIATE")
            assert mode.upper() in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])