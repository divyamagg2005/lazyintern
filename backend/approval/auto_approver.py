from __future__ import annotations

from datetime import timedelta

from core.config import settings
from core.supabase_db import db, today_utc, utcnow


AUTO_APPROVE_THRESHOLD = 90
TIMEOUT_HOURS = 2


def run_auto_approver() -> None:
    """
    Phase 9 auto-approver:
    - Finds drafts with status 'generated' and approval_sent_at older than 2h.
    - If full_score >= AUTO_APPROVE_THRESHOLD → mark auto_approved and bump counter.
    """
    now = utcnow()
    cutoff = now - timedelta(hours=TIMEOUT_HOURS)

    res = (
        db.client.table("email_drafts")
        .select("*, leads!inner(internship_id)")
        .eq("status", "generated")
        .lte("approval_sent_at", cutoff.isoformat())
        .execute()
    )
    rows = res.data or []
    today = today_utc()

    for row in rows:
        # Get the internship to check full_score
        internship_id = row["leads"]["internship_id"]
        internship_res = (
            db.client.table("internships")
            .select("full_score")
            .eq("id", internship_id)
            .limit(1)
            .execute()
        )
        
        if not internship_res.data:
            continue
            
        full_score = int(internship_res.data[0].get("full_score") or 0)
        if full_score >= AUTO_APPROVE_THRESHOLD:
            db.client.table("email_drafts").update(
                {"status": "auto_approved"}
            ).eq("id", row["id"]).execute()
            db.bump_daily_usage(today, auto_approvals=1)

