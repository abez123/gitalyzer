"""Functions responsible for calling an LLM (or a graceful fallback) to explain a repo."""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from openai import OpenAI

from .config import ANALYSIS_FIELDS, SYSTEM_PROMPT

# Default model chosen for a balance of quality and cost. Users can change this if needed.
DEFAULT_MODEL = "gpt-4o-mini"


def _build_user_prompt(context: str) -> str:
    """Create the user-facing prompt that instructs the model to return structured JSON."""

    schema_lines = []
    for field, description in ANALYSIS_FIELDS.items():
        schema_lines.append(f"- {field}: {description}")

    return (
        "You will receive a description of a GitHub repository. "
        "Explain the project to a complete beginner and respond with valid JSON.\n\n"
        "Required JSON fields:\n"
        + "\n".join(schema_lines)
        + "\n\n"
        "Important rules:\n"
        "- Keep language friendly and free of jargon.\n"
        "- Every list should contain at least three helpful items when possible.\n"
        "- Definitions in the glossary must be short and clear.\n"
        "- Return only valid JSON. Do not wrap it in code fences.\n\n"
        "Repository information:\n"
        f"{context}"
    )


def call_ai_agent(context: str, api_key: str, model: str = DEFAULT_MODEL) -> Tuple[Dict[str, Any], str]:
    """Send the context to the OpenAI API and parse the structured response."""

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(context)},
        ],
    )

    message = completion.choices[0].message.content or "{}"
    data = json.loads(message)
    return data, message


def generate_rule_based_summary(context: str) -> Dict[str, Any]:
    """Fallback summary used when an API key is missing or an AI call fails."""

    # The context string is structured, so we can extract a few hints from it by hand.
    lines = [line.strip() for line in context.splitlines() if line.strip()]
    description = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("Description:")), "")
    languages = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("Languages:")), "")
    headline = description or "This repository does not include a description on GitHub."

    summary = {
        "project_summary": headline,
        "how_it_helps_people": (
            "This project could be useful to people who are interested in exploring the code base. "
            "Provide an OpenAI API key to unlock a tailored explanation."
        ),
        "main_features": [
            "Automatic GitHub metadata gathering",
            "Displays the README excerpt if one exists",
            "Summarises recent commit messages for a quick update",
        ],
        "how_it_works": [
            "The app downloads information directly from GitHub using their public API.",
            "It organises the repository details, language statistics, and README summary.",
            "Without an AI key it falls back to this simple overview to keep the experience working.",
        ],
        "tech_stack": [
            "GitHub topics: " + (languages if languages else "Not specified"),
            "Primary language reported by GitHub: " + (languages.split(",")[0] if languages else "Unknown"),
            "Recent commits are highlighted to show ongoing work.",
        ],
        "getting_started": [
            "Paste a public GitHub repository URL into the form.",
            "Optionally provide an OpenAI API key so the AI guide can craft a custom explanation.",
            "Review the generated summary online or export it as a PDF.",
        ],
        "next_steps": [
            "Add an OpenAI API key to unlock richer, human-friendly storytelling.",
            "Share the generated PDF with teammates who need a high-level overview.",
            "Explore the README and commits directly on GitHub for deeper technical context.",
        ],
        "glossary": [
            {"term": "Repository", "definition": "A storage space on GitHub that holds a project's files."},
            {"term": "Commit", "definition": "A snapshot of changes developers save to the project."},
            {"term": "README", "definition": "A document that usually explains what the project is about."},
        ],
    }
    return summary
