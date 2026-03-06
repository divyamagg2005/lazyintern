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

# Daily send limits
MAX_SMS_PER_DAY = 50
MAX_EMAILS_PER_DAY = 50


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


def scan_jd_keywords(jd_text: str, keywords: dict[str, Any]) -> dict[str, Any]:
    """
    Scan job description for technical keywords across 3 tiers.
    
    Tier 1 (frameworks/tools): +8 each, max +40
    Tier 2 (algorithms/tasks): +4 each, max +20
    Tier 3 (general practices): +2 each, max +10
    
    Args:
        jd_text: Job description text to scan
        keywords: Keywords dictionary containing jd_keywords section
    
    Returns:
        Dict with tier1_score, tier2_score, tier3_score, total_jd_score,
        tier1_matches, tier2_matches, tier3_matches (sets of matched keywords)
    """
    jd_keywords = keywords.get("jd_keywords", {})
    
    # Track unique matches per tier to avoid double-counting
    tier1_matches = set()
    tier2_matches = set()
    tier3_matches = set()
    
    # Scan Tier 1 keywords
    tier1_keywords = [kw.lower() for kw in jd_keywords.get("tier1", [])]
    for kw in tier1_keywords:
        if whole_word_match(kw, jd_text):
            tier1_matches.add(kw)
    
    # Scan Tier 2 keywords
    tier2_keywords = [kw.lower() for kw in jd_keywords.get("tier2", [])]
    for kw in tier2_keywords:
        if whole_word_match(kw, jd_text):
            tier2_matches.add(kw)
    
    # Scan Tier 3 keywords
    tier3_keywords = [kw.lower() for kw in jd_keywords.get("tier3", [])]
    for kw in tier3_keywords:
        if whole_word_match(kw, jd_text):
            tier3_matches.add(kw)
    
    # Apply tier-specific scoring with caps
    tier1_score = min(len(tier1_matches) * 8, 40)
    tier2_score = min(len(tier2_matches) * 4, 20)
    tier3_score = min(len(tier3_matches) * 2, 10)
    total_jd_score = tier1_score + tier2_score + tier3_score
    
    return {
        "tier1_score": tier1_score,
        "tier2_score": tier2_score,
        "tier3_score": tier3_score,
        "total_jd_score": total_jd_score,
        "tier1_matches": tier1_matches,
        "tier2_matches": tier2_matches,
        "tier3_matches": tier3_matches
    }


def detect_track(role_title: str, company: str, jd_text: str, keywords: dict[str, Any]) -> str:
    """
    Detect whether a lead is tech or finance track based on keyword analysis.
    
    Args:
        role_title: Job role title
        company: Company name
        jd_text: Job description text
        keywords: Keywords dictionary containing finance_track_signals
    
    Returns:
        "finance" if finance signals detected, else "tech"
        
    Logic:
        - If finance_track_hits >= 2: track = "finance"
        - If finance_track_hits == 1 AND finance keyword in title: track = "finance"
        - Else: track = "tech"
    """
    finance_signals = [kw.lower() for kw in keywords.get("finance_track_signals", [])]
    
    # Combine title, company, and JD for analysis
    combined_text = f"{role_title} {company} {jd_text}".lower()
    
    # Count finance signal matches across all fields
    finance_track_hits = 0
    for signal in finance_signals:
        if whole_word_match(signal, combined_text):
            finance_track_hits += 1
    
    # Check if any finance signal appears in title specifically
    finance_in_title = False
    for signal in finance_signals:
        if whole_word_match(signal, role_title):
            finance_in_title = True
            break
    
    # Apply 2-tier logic
    if finance_track_hits >= 2:
        return "finance"
    elif finance_track_hits == 1 and finance_in_title:
        return "finance"
    else:
        return "tech"


def should_rescue_generic_title(
    role_title: str, 
    company: str,
    jd_text: str, 
    jd_results: dict[str, int],
    keywords: dict[str, Any]
) -> tuple[bool, int, str]:
    """
    Determine if a generic-titled role should be rescued based on JD strength.
    
    Generic titles score low on title matching but may have strong JD content.
    Uses tier-based rescue logic with separate handling for tech vs finance roles.
    
    Args:
        role_title: Job role title
        company: Company name (for logging)
        jd_text: Job description text
        jd_results: Results from scan_jd_keywords() with tier scores and matches
        keywords: Keywords dictionary containing generic title lists
    
    Returns:
        Tuple of (should_rescue, bonus_points, rescue_type)
    """
    # Check if title matches tech generic titles
    tech_generic_titles = [kw.lower() for kw in keywords.get("tech_generic_titles", [])]
    is_tech_generic = False
    for kw in tech_generic_titles:
        if whole_word_match(kw, role_title):
            is_tech_generic = True
            break
    
    if is_tech_generic:
        # Count tier 1 and tier 2 hits
        tier1_matches = len(jd_results.get("tier1_matches", set()))
        tier2_matches = len(jd_results.get("tier2_matches", set()))
        
        # Tech Strong: tier1_hits >= 3
        if tier1_matches >= 3:
            logger.info(
                f"🔬 JD RESCUE (TECH STRONG): '{role_title}' at '{company}' "
                f"tier1={tier1_matches}, bumped +30"
            )
            return (True, 30, "tech_jd_strong")
        
        # Tech Moderate: tier1_hits >= 1 AND tier2_hits >= 2
        elif tier1_matches >= 1 and tier2_matches >= 2:
            logger.info(
                f"🔬 JD RESCUE (TECH MODERATE): '{role_title}' at '{company}' "
                f"tier1={tier1_matches}, tier2={tier2_matches}, bumped +20"
            )
            return (True, 20, "tech_jd_moderate")
    
    # Check if title matches finance generic titles
    finance_generic_titles = [kw.lower() for kw in keywords.get("finance_generic_titles", [])]
    is_finance_generic = False
    for kw in finance_generic_titles:
        if whole_word_match(kw, role_title):
            is_finance_generic = True
            break
    
    if is_finance_generic:
        # Count finance JD signals
        finance_jd_signals = [kw.lower() for kw in keywords.get("finance_jd_signals", [])]
        finance_hits = 0
        for signal in finance_jd_signals:
            if whole_word_match(signal, jd_text):
                finance_hits += 1
        
        # Finance Strong: finance_hits >= 3
        if finance_hits >= 3:
            logger.info(
                f"💰 JD RESCUE (FINANCE STRONG): '{role_title}' at '{company}' "
                f"finance_hits={finance_hits}, bumped +30"
            )
            return (True, 30, "finance_jd_strong")
        
        # Finance Moderate: finance_hits >= 1
        elif finance_hits >= 1:
            logger.info(
                f"💰 JD RESCUE (FINANCE MODERATE): '{role_title}' at '{company}' "
                f"finance_hits={finance_hits}, bumped +20"
            )
            return (True, 20, "finance_jd_moderate")
    
    return (False, 0, "")



def pre_score(internship: dict[str, Any]) -> PreScoreResult:
    """
    Cheap, local pre-scoring on title + company + location only.
    Uses keywords from data/keywords.json with case-insensitive matching.
    Filters out non-India locations before scoring.
    """
    resume = _load_resume()
    keywords = _load_keywords()
    
    preferred_locations = set(
        str(loc).lower() for loc in (resume.get("preferred_locations") or [])
    )

    role_title = (internship.get("role") or "").lower()
    company = (internship.get("company") or "").lower()
    location = (internship.get("location") or "").lower()

    # REGION FILTER: Check for non-India locations BEFORE scoring
    # Disqualify if location contains non-India indicators
    non_india_indicators = [
        "usa", "us only", "united states", "uk", "united kingdom",
        "london", "new york", "san francisco", "canada", "australia",
        "europe", "germany", "singapore", "uae"
    ]
    
    # Combine role title and location for checking
    combined_text = f"{role_title} {location}"
    
    for indicator in non_india_indicators:
        if whole_word_match(indicator, combined_text):
            # Check if it also mentions India or remote (exception)
            has_india = whole_word_match("india", combined_text)
            has_remote = whole_word_match("remote", combined_text)
            
            if not (has_india or has_remote):
                logger.info(f"Disqualified: non-India location detected: {indicator} in '{role_title}' / '{location}'")
                return PreScoreResult(
                    score=0, 
                    status="disqualified", 
                    breakdown={"non_india_location": -100}
                )

    score = 0
    breakdown = {}

    # High priority role keywords (+40) - CHECK FIRST before disqualification
    role_keywords = keywords.get("role_keywords", {})
    high_priority_role = [kw.lower() for kw in role_keywords.get("high_priority", [])]
    role_match = False
    for kw in high_priority_role:
        if whole_word_match(kw, role_title):
            score += 40
            breakdown["high_priority_role"] = 40
            role_match = True
            break

    # Check for disqualifying keywords AFTER high-priority check
    # If high_priority_role matched, skip disqualification (override rule)
    disqualify_keywords = [kw.lower() for kw in role_keywords.get("disqualify", [])]
    
    if "high_priority_role" not in breakdown:
        # No high-priority match, apply disqualification normally
        for kw in disqualify_keywords:
            if whole_word_match(kw, role_title):
                logger.info(f"Pre-score DISQUALIFIED: '{role_title}' contains '{kw}'")
                return PreScoreResult(score=0, status="disqualified", breakdown={"disqualify": -100})
    else:
        # High-priority match found, check if disqualification would have applied
        for kw in disqualify_keywords:
            if whole_word_match(kw, role_title):
                logger.info(f"Disqualification OVERRIDDEN: '{role_title}' contains '{kw}' but matched high-priority keyword")
                breakdown["disqualify_overridden"] = True
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

    # Company keywords (+20 for high-priority match)
    # Uses case-insensitive substring matching
    company_keywords = keywords.get("company_keywords", {})
    high_priority_company = [kw.lower() for kw in company_keywords.get("high_priority", [])]
    
    if company:  # Gracefully skip if company is None
        for kw in high_priority_company:
            if kw in company:  # Substring match (case-insensitive)
                score += 20
                breakdown["high_priority_company"] = 20
                break

    # Location match (+20)
    # Check both the location field AND the role title
    # Uses case-insensitive substring matching
    location_keywords = keywords.get("location_keywords", {})
    all_preferred_locations = [loc.lower() for loc in location_keywords.get("preferred", [])]
    all_preferred_locations.extend(list(preferred_locations))
    
    location_found = False
    
    # Check location field first (if not None)
    if location:
        for loc_kw in all_preferred_locations:
            if loc_kw in location:  # Substring match
                score += 20
                breakdown["location_match"] = 20
                location_found = True
                break
    
    # If no location field match, scan the role title for location keywords
    # Examples: "AI Internship in Mumbai", "ML Intern - (paid - india/remote)"
    if not location_found:
        for loc_kw in all_preferred_locations:
            if loc_kw in role_title:  # Substring match
                score += 20
                breakdown["location_match_from_title"] = 20
                logger.info(f"Location '{loc_kw}' found in role title: '{role_title}'")
                break

    # JD-based keyword scanning (3-tier system)
    jd_text = (internship.get("description") or "").lower()
    jd_results = {}
    if jd_text:
        jd_results = scan_jd_keywords(jd_text, keywords)
        if jd_results["total_jd_score"] > 0:
            score += jd_results["total_jd_score"]
            breakdown["jd_tier1"] = jd_results["tier1_score"]
            breakdown["jd_tier2"] = jd_results["tier2_score"]
            breakdown["jd_tier3"] = jd_results["tier3_score"]

    # Track detection (tech vs finance)
    track = detect_track(role_title, company, jd_text, keywords)
    breakdown["track"] = track

    # Generic title rescue mechanism (AFTER JD scanning)
    if jd_text and jd_results:
        should_rescue, rescue_bonus, rescue_type = should_rescue_generic_title(
            role_title, company, jd_text, jd_results, keywords
        )
        if should_rescue:
            score += rescue_bonus
            breakdown["generic_title_rescued"] = rescue_bonus
            breakdown["rescue_type"] = rescue_type


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

    # Log comprehensive breakdown for debugging
    title_score = breakdown.get("high_priority_role", 0) or breakdown.get("medium_priority_role", 0)
    company_score = breakdown.get("high_priority_company", 0)
    location_score = breakdown.get("location_match", 0) or breakdown.get("location_match_from_title", 0)
    jd_tier1 = breakdown.get("jd_tier1", 0)
    jd_tier2 = breakdown.get("jd_tier2", 0)
    jd_tier3 = breakdown.get("jd_tier3", 0)
    track_value = breakdown.get("track", "unknown")
    rescued = breakdown.get("generic_title_rescued", 0) > 0
    rescue_type = breakdown.get("rescue_type", None)
    
    logger.info(
        f"Pre-score: {score} | Track: {track_value} | Role: '{role_title}' | "
        f"Company: '{company}' | Location: '{location}' | "
        f"Breakdown: {{ role_title: +{title_score}, company_bonus: +{company_score}, "
        f"location: +{location_score}, jd_tier1: +{jd_tier1}, jd_tier2: +{jd_tier2}, "
        f"jd_tier3: +{jd_tier3}, rescued: {rescued}, rescue_type: {rescue_type} }}"
    )

    status = "discovered" if score >= 0 else "low_priority"
    return PreScoreResult(score=score, status=status, breakdown=breakdown)
