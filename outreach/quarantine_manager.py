from __future__ import annotations

from datetime import date

from core.supabase_db import db, utcnow, today_utc
from pipeline.full_scorer import full_score
from pipeline.pre_scorer import _load_resume  # type: ignore[attr-defined]


def move_to_quarantine(lead_id: str, draft_id: str) -> None:
    today = today_utc()
    db.client.table("quarantine").insert(
        {
            "lead_id": lead_id,
            "draft_id": draft_id,
            "re_evaluate_after": str(today.replace(day=today.day + 14)),
        }
    ).execute()


def process_quarantine_re_evaluations() -> None:
    today = today_utc()
    res = (
        db.client.table("quarantine")
        .select("*, leads!inner(*), email_drafts!inner(*)")
        .lte("re_evaluate_after", str(today))
        .eq("re_evaluated", False)
        .execute()
    )
    rows = res.data or []
    resume = _load_resume()

    for row in rows:
        lead = row["leads"]
        internship_id = lead["internship_id"]
        intern = (
            db.client.table("internships")
            .select("*")
            .eq("id", internship_id)
            .limit(1)
            .execute()
        ).data[0]

        fs = full_score(intern, resume)
        db.client.table("quarantine").update(
            {
                "re_evaluated": True,
                "re_evaluation_score": int(fs.score),
            }
        ).eq("id", row["id"]).execute()

