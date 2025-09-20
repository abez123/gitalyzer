"""Configuration and shared constants for the Gitalyzer backend."""

SYSTEM_PROMPT = (
    "You are Gitalyzer, an AI guide that explains software projects in plain language. "
    "Assume the listener has no background in programming. Use friendly, non-technical "
    "language, keep sentences short, and provide helpful analogies when possible. "
    "Highlight what problems the project solves, what someone can do with it, and the "
    "minimum technical steps needed to try it out. Always sound encouraging and practical."
)

# Fields expected in the structured analysis returned by the AI agent. Keeping the schema
# here avoids duplication in several modules.
ANALYSIS_FIELDS = {
    "project_summary": "A warm, one-paragraph overview that explains the project at a very high level.",
    "how_it_helps_people": "A plain-language explanation of the real-world value it delivers.",
    "main_features": "Three to five bullet points describing the most important things the project can do.",
    "how_it_works": "Step-by-step bullets that describe, without jargon, how the project behaves behind the scenes.",
    "tech_stack": "A bullet list of the main tools, frameworks, or languages, each explained simply.",
    "getting_started": "A checklist someone could follow to see the project running, phrased for non-experts.",
    "next_steps": "Friendly suggestions for future improvements or directions to explore.",
    "glossary": "A short dictionary of tricky words with beginner-friendly definitions.",
}
