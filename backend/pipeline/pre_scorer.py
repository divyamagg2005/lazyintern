from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json
import re

from core.supabase_db import db
from core.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_PATH = PROJECT_ROOT / "data" / "resume.json"
KEYWORDS_PATH = PROJECT_ROOT / "data" / "keywords.json"


@dataclass
class PreScoreResult:
    score: int
    status: str
    breakdown: dict[str, int]


def _load_resume() -> dict[str, Any]:
    if RESUME_PATH.exists():
        return json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    return {}


def _load_keywords() -> dict[str, Any]:
    if KEYWORDS_PATH.exists():
        return json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))
    return {}


def whole_word_match(keyword: str, text: str) -> bool:
    """
    Check if keyword matches as a whole word in text (case-insensitive).
    Prevents false positives like 'pr' matching 'product', 'prior', 'research'.
    
    Examples:
        whole_word_match('ml', 'ml engineer') -> True
        whole_word_match('ml', 'html developer') -> False
        whole_word_match('ai', 'ai research') -> True
        whole_word_match('ai', 'email') -> False
    """
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))


def pre_score(internship: dict[str, Any]) -> PreScoreResult:
    """
    Cheap, local pre-scoring on title + company + location only.
    Uses keywords from data/keywords.json with case-insensitive matching.
    """
    resume = _load_resume()
    keywords = _load_keywords()
    
    preferred_locations = set(
        str(loc).lower() for loc in (resume.get("preferred_locations") or [])
    )

    role_title = (internship.get("role") or "").lower()
    company = (internship.get("company") or "").lower()
    location = (internship.get("location") or "").lower()

    score = 0
    breakdown = {}

    # Check for disqualifying keywords first
    role_keywords = keywords.get("role_keywords", {})
    disqualify_keywords = [kw.lower() for kw in role_keywords.get("disqualify", [])]
    
    for kw in disqualify_keywords:
        if whole_word_match(kw, role_title):
            logger.info(f"Pre-score DISQUALIFIED: '{role_title}' contains '{kw}'")
            return PreScoreResult(score=0, status="disqualified", breakdown={"disqualify": -100})

    # High priority role keywords (+40)
    high_priority_role = [kw.lower() for kw in role_keywords.get("high_priority", [])]
    role_match = False
    for kw in high_priority_role:
        if whole_word_match(kw, role_title):
            score += 40
            breakdown["high_priority_role"] = 40
            role_match = True
            break

    # Medium priority role keywords (+20)
    if not role_match:
        medium_priority_role = [kw.lower() for kw in role_keywords.get("medium_priority", [])]
        for kw in medium_priority_role:
            if whole_word_match(kw, role_title):
                score += 20
                breakdown["medium_priority_role"] = 20
                role_match = True
                break

    # Company keywords
    company_keywords = keywords.get("company_keywords", {})
    high_priority_company = [kw.lower() for kw in company_keywords.get("high_priority", [])]
    
    for kw in high_priority_company:
        if whole_word_match(kw, company):
            score += 20
            breakdown["high_priority_company"] = 20
            break

    # Location match (+20)
    # Check both the location field AND the role title (for LinkedIn/sources that embed location in title)
    location_keywords = keywords.get("location_keywords", {})
    all_preferred_locations = []
    all_preferred_locations.extend([loc.lower() for loc in location_keywords.get("preferred_remote", [])])
    all_preferred_locations.extend([loc.lower() for loc in location_keywords.get("preferred_cities_india", [])])
    all_preferred_locations.extend([loc.lower() for loc in location_keywords.get("preferred_cities_global", [])])
    all_preferred_locations.extend(list(preferred_locations))
    
    location_found = False
    for loc_kw in all_preferred_locations:
        # Check dedicated location field first
        if whole_word_match(loc_kw, location):
            score += 20
            breakdown["location_match"] = 20
            location_found = True
            break
    
    # If no location field match, scan the role title for location keywords
    # Examples: "AI Internship in Mumbai", "ML Intern - (paid - india/remote)"
    if not location_found:
        for loc_kw in all_preferred_locations:
            if whole_word_match(loc_kw, role_title):
                score += 20
                breakdown["location_match_from_title"] = 20
                logger.info(f"Location '{loc_kw}' found in role title: '{role_title}'")
                break

    # Historical success from company_domains.reply_history
    link = (internship.get("link") or "").lower()
    domain = link.split("//")[-1].split("/")[0] if "//" in link else link.split("/")[0]
    domain = domain.split("@")[-1]
    
    if domain:
        res = (
            db.client.table("company_domains")
            .select("reply_history")
            .eq("domain", domain)
            .limit(1)
            .execute()
        )
        if res.data:
            hist = res.data[0].get("reply_history") or {}
            if (hist.get("positive") or 0) > 0:
                score += 20
                breakdown["historical_success"] = 20

    # Log breakdown for debugging
    logger.info(
        f"Pre-score: {score} | Role: '{role_title}' | Company: '{company}' | "
        f"Location: '{location}' | Breakdown: {breakdown}"
    )

    status = "discovered" if score >= 0 else "low_priority"
    return PreScoreResult(score=score, status=status, breakdown=breakdown)
