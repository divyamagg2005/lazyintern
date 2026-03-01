from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import httpx

from core.config import settings
from core.supabase_db import db, today_utc, utcnow
from core.logger import logger


@dataclass
class GroqDraft:
    subject: str
    body: str
    followup_body: str


SYSTEM_PROMPT = """You are an expert cold email writer for internship outreach.

Candidate Profile:
Name: {name}
Current Education: {education}
Technical Skills: {skills}
Key Projects: {projects}

Writing Guidelines:
- Tone: professional, concise, genuine
- Never sound like a template or generic
- Be specific about relevant experience
- Show you researched the company
- Highlight concrete achievements

Output Format:
  - Subject line (max 8 words, compelling)
  - Email body (150-200 words, 3 paragraphs)
  - Follow-up template (75 words, for day 5 if no reply)

Output ONLY valid JSON with this exact structure:
{{"subject": "...", "body": "...", "followup": "..."}}

IMPORTANT: Use the EXACT education year specified in the candidate profile above.
"""


def _build_system_prompt(resume: dict[str, Any]) -> str:
    """Build system prompt with resume context for caching."""
    name = resume.get("name", "Candidate")
    education = resume.get("education", {})
    
    # Build education string with explicit year
    year = education.get("year", "")
    current_year = education.get("current_year", year)
    degree = education.get("degree", "")
    college = education.get("college", "")
    
    edu_str = f"{degree} at {college}, {current_year}"
    
    skills = resume.get("skills", {})
    skills_str = ", ".join([
        *skills.get("languages", [])[:5],
        *skills.get("frameworks", [])[:5]
    ])
    
    projects = resume.get("projects", [])[:3]
    projects_str = "\n".join([
        f"- {p.get('name', '')}: {p.get('description', '')[:100]}"
        for p in projects
    ])
    
    return SYSTEM_PROMPT.format(
        name=name,
        education=edu_str,
        skills=skills_str,
        projects=projects_str
    )


def _build_user_prompt(lead: dict[str, Any], internship: dict[str, Any]) -> str:
    """Build user prompt with specific job details."""
    company = internship.get("company", "the company")
    role = internship.get("role", "intern")
    description = internship.get("description", "")[:300]  # First 300 chars
    recruiter = lead.get("recruiter_name") or "Hiring Team"
    
    return f"""Company: {company}
Role: {role}
Recruiter: {recruiter}
Job Description Summary: {description}

Generate a personalized cold email for this internship opportunity."""


def generate_draft(lead: dict[str, Any], internship: dict[str, Any], resume: dict[str, Any]) -> GroqDraft:
    """
    Generate personalized email draft using Groq API.
    Falls back to template if API key is missing or call fails.
    """
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not set, using fallback template")
        return _generate_fallback_draft(lead, internship, resume)
    
    try:
        system_prompt = _build_system_prompt(resume)
        user_prompt = _build_user_prompt(lead, internship)
        
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            },
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        
        # Track usage
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        db.bump_daily_usage(today_utc(), groq_calls=1, groq_tokens_used=tokens_used)
        
        logger.info(f"Groq draft generated. Tokens: {tokens_used}")
        
        return GroqDraft(
            subject=parsed.get("subject", "Application for internship"),
            body=parsed.get("body", ""),
            followup_body=parsed.get("followup", "")
        )
        
    except Exception as e:
        logger.error(f"Groq API failed: {e}")
        
        # Send error notification
        from core.guards import send_error_notification
        send_error_notification(
            error_type="Groq API",
            error_message=str(e),
            context={
                "lead_id": lead.get("id"),
                "internship_id": internship.get("id")
            }
        )
        
        # Add to retry queue
        db.insert_retry(
            phase="groq",
            payload={
                "lead_id": lead.get("id"),
                "internship_id": internship.get("id")
            },
            next_retry_at=utcnow() + timedelta(minutes=5),
            last_error=str(e)
        )
        # Fallback to template
        return _generate_fallback_draft(lead, internship, resume)


def _generate_fallback_draft(lead: dict[str, Any], internship: dict[str, Any], resume: dict[str, Any]) -> GroqDraft:
    """Generate simple template when Groq API is unavailable."""
    company = internship.get("company") or "the company"
    role = internship.get("role") or "intern"
    recruiter = lead.get("recruiter_name") or "Hiring Team"
    name = resume.get("name", "Candidate")
    
    skills = resume.get("skills", {})
    languages = ", ".join(skills.get("languages", [])[:3])
    
    projects = resume.get("projects", [])
    project_names = ", ".join([p.get("name", "") for p in projects[:2]])

    subject = f"Application for {role} at {company}"
    body = (
        f"Hi {recruiter},\n\n"
        f"My name is {name} and I'm writing to express my interest "
        f"in the {role} role at {company}. I have experience with {languages} "
        f"and have worked on projects including {project_names}.\n\n"
        "I'd love the opportunity to discuss how I can contribute to your team this internship season.\n\n"
        "Best regards,\n"
        f"{name}"
    )
    followup = (
        f"Hi {recruiter},\n\n"
        f"Just following up on my application for the {role} role at {company}. "
        "I'd still be excited to explore whether there might be a fit.\n\n"
        "Best,\n"
        f"{name}"
    )

    return GroqDraft(subject=subject, body=body, followup_body=followup)

