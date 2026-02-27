from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from core.supabase_db import db

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_PATH = PROJECT_ROOT / "data" / "resume.json"


@dataclass
class PreScoreResult:
    score: int
    status: str


def _load_resume() -> dict[str, Any]:
    if RESUME_PATH.exists():
        return json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    return {}


def pre_score(internship: dict[str, Any]) -> PreScoreResult:
    """
    Cheap, local pre-scoring on title + company + location only.
    Mirrors the logic in final_pipeline.md with thresholds enforced
    by the caller.
    """
    resume = _load_resume()
    preferred_locations = set(
        (resume.get("preferred_locations") or [])  # type: ignore[arg-type]
    )

    role_title = (internship.get("role") or "").lower()
    company = (internship.get("company") or "").lower()
    location = (internship.get("location") or "").lower()

    score = 0

    kw_list = ["ai", "ml", "data", "nlp", "research", "llm"]
    if any(kw in role_title for kw in kw_list):
        score += 40

    # Very rough startup / YC heuristic based on company string
    if "labs" in company or "ai" in company or "ml" in company:
        score += 20

    if any(loc.lower() in location for loc in preferred_locations):
        score += 20

    # Simple historical-success heuristic from company_domains.reply_history
    link = (internship.get("link") or "").lower()
    domain = link.split("//")[-1].split("/")[0]
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

    status = "discovered" if score >= 0 else "low_priority"
    return PreScoreResult(score=score, status=status)

