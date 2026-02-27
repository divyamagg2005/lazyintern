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


def extract_from_internship(internship: dict[str, Any]) -> ExtractedEmail | None:
    """
    Regex-based free email extraction over description text only.
    """
    text = (internship.get("description") or "") + "\n" + (internship.get("source_url") or "")
    matches = list(EMAIL_REGEX.finditer(text))
    if not matches:
        return None

    best: ExtractedEmail | None = None
    for m in matches:
        raw = m.group(0)
        email = _normalize_email(raw)
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
