import httpx
import json
from core.config import settings

print("Testing Groq Email Generation (without Supabase)...")

# Load resume
with open("data/resume.json", "r", encoding="utf-8") as f:
    resume = json.load(f)

print(f"✓ Resume loaded: {resume.get('name')}")

# Build prompts
name = resume.get("name", "Candidate")
education = resume.get("education", {})
edu_str = f"{education.get('degree', '')} at {education.get('college', '')}"

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

system_prompt = f"""You are an expert cold email writer for internship outreach.

Candidate Profile:
Name: {name}
Education: {edu_str}
Skills: {skills_str}
Projects: {projects_str}

Tone: professional, concise, genuine. Never sound like a template.

Output ONLY valid JSON with this exact structure:
{{"subject": "...", "body": "...", "followup": "..."}}
"""

user_prompt = """Company: TestCo
Role: AI Intern
Recruiter: John Doe
Job Description: We are looking for an AI intern to work on machine learning projects.

Generate a personalized cold email for this internship opportunity."""

print("\nGenerating email with Groq...")

try:
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
    
    print("\n✓ SUCCESS! Email generated:")
    print(f"\nSubject: {parsed.get('subject')}")
    print(f"\nBody:\n{parsed.get('body')}")
    print(f"\nFollow-up:\n{parsed.get('followup')}")
    
    usage = data.get("usage", {})
    print(f"\nTokens used: {usage.get('total_tokens', 0)}")
    
except Exception as e:
    print(f"\n✗ FAILED: {e}")
