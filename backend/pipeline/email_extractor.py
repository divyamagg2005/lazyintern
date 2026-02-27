from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+"
    r"\s*(?:@|\[at\]|\(at\)|\sat\s|\s_at_)\s*"
    r"[a-zA-Z0-9.-]+"
    r"\s*(?:\.|dot|\(dot\)|\sdot\s)\s*"
    r"[a-zA-Z]{2,}",
    re.IGNORECASE,
)


RECRUITER_KEYWORDS = ["hr", "hiring", "talent", "recruiter", "careers"]


@dataclass
class ExtractedEmail:
    email: str
    confidence: int
    recruiter_name: str | None
    source: str


def _normalize_email(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"\s*\[at\]|\(at\)|\sat\s|\s_at_\s*", "@", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*(?:dot|\(dot\)|\sdot\s)\s*", ".", s, flags=re.IGNORECASE)
    return s


def _extract_domain_from_url(url: str) -> str:
    """
    Extract the base domain from a URL.
    Examples:
        https://www.linkedin.com/jobs/123 -> linkedin.com
        https://internshala.com/internships/ml -> internshala.com
        https://wellfound.com/jobs?role=AI -> wellfound.com
    """
    if not url:
        return ""
    
    # Remove protocol
    domain = url.split("//")[-1] if "//" in url else url
    
    # Remove path and query params
    domain = domain.split("/")[0].split("?")[0]
    
    # Remove port if present
    domain = domain.split(":")[0]
    
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]
    
    return domain.lower()


def _is_platform_email(email: str, source_url: str) -> bool:
    """
    Check if the email domain matches the job board platform domain.
    Platform emails should be rejected as they're not recruiter contacts.
    
    Examples:
        email=ecombes@linkedin.com, source=linkedin.com -> True (REJECT)
        email=hr@internshala.com, source=internshala.com -> True (REJECT)
        email=hr@blitzenx.com, source=linkedin.com -> False (KEEP)
        email=careers@startup.ai, source=wellfound.com -> False (KEEP)
    """
    if not email or "@" not in email:
        return False
    
    email_domain = email.split("@")[1].lower()
    platform_domain = _extract_domain_from_url(source_url)
    
    if not platform_domain:
        return False
    
    # Direct match
    if email_domain == platform_domain:
        return True
    
    # Check if email domain is a subdomain of platform
    # e.g., mail.linkedin.com should match linkedin.com
    if email_domain.endswith("." + platform_domain):
        return True
    
    # Check if platform domain is a subdomain of email domain
    # e.g., linkedin.com should match mail.linkedin.com
    if platform_domain.endswith("." + email_domain):
        return True
    
    return False


def extract_from_internship(internship: dict[str, Any]) -> ExtractedEmail | None:
    """
    Regex-based free email extraction over description text only.
    Rejects platform emails (e.g., emails from linkedin.com when source is LinkedIn).
    """
    text = (internship.get("description") or "") + "\n" + (internship.get("source_url") or "")
    source_url = internship.get("link") or internship.get("source_url") or ""
    
    matches = list(EMAIL_REGEX.finditer(text))
    if not matches:
        return None

    best: ExtractedEmail | None = None
    for m in matches:
        raw = m.group(0)
        email = _normalize_email(raw)
        
        # CRITICAL: Reject platform emails (e.g., ecombes@linkedin.com from LinkedIn job pages)
        if _is_platform_email(email, source_url):
            continue  # Skip this email, it's from the job board platform, not the company
        
        local = email.split("@", 1)[0].lower()
        confidence = 60
        if any(kw in local for kw in RECRUITER_KEYWORDS):
            confidence = 85

        rec_name = None
        candidate = ExtractedEmail(
            email=email,
            confidence=confidence,
            recruiter_name=rec_name,
            source="regex",
        )
        if best is None or candidate.confidence > best.confidence:
            best = candidate

    return best
