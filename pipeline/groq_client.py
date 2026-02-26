from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from core.config import settings


@dataclass
class GroqDraft:
    subject: str
    body: str
    followup_body: str


SYSTEM_PROMPT = """You are an expert cold email writer for internship outreach.
Tone: professional, concise, genuine. Never sound like a template.
Format:
  - Subject line (max 8 words)
  - Email body (150-200 words, 3 paragraphs)
  - Follow-up template (75 words, day 5 if no reply)
Output as JSON: {subject, body, followup}
"""


def generate_draft(lead: dict[str, Any], internship: dict[str, Any], resume: dict[str, Any]) -> GroqDraft:
    """
    Initial version: if GROQ_API_KEY is missing, generate a simple
    deterministic template so you can test the pipeline without
    external calls.
    """
    company = internship.get("company") or "the company"
    role = internship.get("role") or "intern"
    recruiter = lead.get("recruiter_name") or "Hiring Team"

    subject = f"Application for {role} at {company}"
    body = (
        f"Hi {recruiter},\n\n"
        f"My name is {resume.get('name', 'a candidate')} and I'm writing to express my interest "
        f"in the {role} role at {company}. I have experience with {', '.join(resume.get('skills', {}).get('languages', []))} "
        f"and have worked on projects involving {', '.join(p.get('name', '') for p in resume.get('projects', []))}.\n\n"
        "I'd love the opportunity to discuss how I can contribute to your team this internship season.\n\n"
        "Best regards,\n"
        f"{resume.get('name', '')}"
    )
    followup = (
        f"Hi {recruiter},\n\n"
        f"Just following up on my application for the {role} role at {company}. "
        "I'd still be excited to explore whether there might be a fit.\n\n"
        "Best,\n"
        f"{resume.get('name', '')}"
    )

    return GroqDraft(subject=subject, body=body, followup_body=followup)

