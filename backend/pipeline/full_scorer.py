from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.supabase_db import db


@dataclass
class FullScoreResult:
    score: float
    breakdown: dict[str, float]


def _compute_components(internship: dict[str, Any], resume: dict[str, Any]) -> dict[str, float]:
    role = (internship.get("role") or "").lower()
    desc = (internship.get("description") or "").lower()

    target_roles = [r.lower() for r in resume.get("target_roles", [])]
    relevance = 100.0 if any(r in role for r in target_roles) else 60.0 if any(
        r.split()[0] in role for r in target_roles
    ) else 40.0

    # crude overlap between resume skills and description
    resume_terms: list[str] = []
    for vals in (resume.get("skills") or {}).values():
        resume_terms.extend([str(v).lower() for v in vals])  # type: ignore[arg-type]

    overlap_hits = sum(1 for t in resume_terms if t in desc)
    resume_overlap = min(100.0, overlap_hits * 10.0)

    tech_stack = min(100.0, overlap_hits * 8.0)

    preferred_locations = [str(x).lower() for x in resume.get("preferred_locations", [])]
    location = (internship.get("location") or "").lower()
    location_score = 100.0 if any(p in location for p in preferred_locations) else 40.0

    # historical_success_score approx from company_domains.reply_history
    link = (internship.get("link") or "").lower()
    domain = link.split("//")[-1].split("/")[0]
    domain = domain.split("@")[-1]
    historical = 50.0
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
            pos = float(hist.get("positive") or 0)
            neg = float(hist.get("negative") or 0)
            total = pos + neg
            if total > 0:
                historical = 40.0 + 60.0 * (pos / total)

    return {
        "relevance_score": relevance,
        "resume_overlap_score": resume_overlap,
        "tech_stack_score": tech_stack,
        "location_score": location_score,
        "historical_success_score": historical,
    }


def full_score(internship: dict[str, Any], resume: dict[str, Any]) -> FullScoreResult:
    weights = db.get_scoring_weights()
    components = _compute_components(internship, resume)

    score = 0.0
    for key, value in components.items():
        w = float(weights.get(key, 0.0))
        score += value * w

    return FullScoreResult(score=score, breakdown=components)

