"""
Educational prompt templates and helpers.
Provides mode-specific prompt enrichment.
"""
from __future__ import annotations

from app.prompts.classification import Intent


def get_mode_instructions(mode: str) -> str:
    """
    Get mode-specific behavioral instructions.

    Args:
        mode: User mode (Student, Company Knowledge, Expert)

    Returns:
        Mode-specific instruction string
    """
    modes = {
        "Student": """
STUDENT MODE INSTRUCTIONS:
- Use clear, accessible language appropriate for a university student
- Define technical terms on first use
- Provide concrete examples to illustrate abstract concepts
- Structure explanations from simple → complex
- Suggest what to study next when relevant
- Encourage curiosity and further exploration
""",
        "Company Knowledge": """
COMPANY KNOWLEDGE MODE INSTRUCTIONS:
- Prioritize retrieved company documentation above all other sources
- Be precise and factual about company information
- If company documents don't cover a topic, say so clearly
- Do not speculate about company capabilities or services
- Provide professional, business-appropriate responses
""",
        "Expert": """
EXPERT MODE INSTRUCTIONS:
- Assume technical proficiency — skip basic definitions unless asked
- Provide implementation-level detail
- Discuss trade-offs, limitations, and edge cases
- Include relevant RFCs, standards, or technical references when applicable
- Discuss both offensive and defensive perspectives for completeness
- Be concise — experts don't need hand-holding
""",
    }
    return modes.get(mode, modes["Student"])


def get_depth_instruction(depth: str) -> str:
    """
    Get depth-specific instruction based on user request.
    """
    depths = {
        "beginner": "Explain this in simple terms suitable for someone new to cybersecurity.",
        "intermediate": "Provide a balanced technical explanation with practical examples.",
        "advanced": "Provide a deep technical explanation covering implementation details, edge cases, and trade-offs.",
        "quiz": "Format your response as an educational quiz or exercise on this topic.",
        "exam": "Provide a concise, exam-focused summary covering the most important points.",
        "analogy": "Explain this concept using a real-world analogy that makes it intuitive.",
        "defense": "Focus specifically on the defensive and detection aspects of this topic.",
        "simple": "Explain this as simply as possible, using plain language.",
    }
    return depths.get(depth.lower(), "")


QUIZ_GENERATION_PROMPT = """
Generate {num_questions} educational quiz questions about: {topic}

Requirements:
- Mix of question types: conceptual, practical, true/false
- Include the correct answer for each
- Add a brief explanation for why the answer is correct
- Appropriate difficulty: {difficulty}
- Format clearly with numbered questions

Topic: {topic}
"""


def format_quiz_prompt(topic: str, num_questions: int = 5, difficulty: str = "intermediate") -> str:
    """Format a quiz generation prompt."""
    return QUIZ_GENERATION_PROMPT.format(
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
    )