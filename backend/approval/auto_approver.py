from __future__ import annotations

import random
from datetime import timedelta

from core.config import settings
from core.supabase_db import db, today_utc, utcnow
from core.logger import logger


# Auto-approve ALL drafts after timeout (no score threshold)
TIMEOUT_HOURS = 2

# Add random delay for auto-approved emails to avoid spam detection
# Auto-approved emails will wait an additional 10-30 minutes after approval
AUTO_APPROVE_MIN_DELAY_MINUTES = 10
AUTO_APPROVE_MAX_DELAY_MINUTES = 30


def run_auto_approver() -> None:
    """
    Phase 9 auto-approver:
    - Finds drafts with status 'generated' and approval_sent_at older than 2h.
    - Auto-approves ALL drafts (no score threshold) - user wants all leads to get emails.
    - Adds random delay (10-30 min) via approved_at timestamp to avoid spam detection.
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
        internship_id = row["leads"]["internship_id"]
        
        # Get full_score for logging purposes only (not for filtering)
        internship_res = (
            db.client.table("internships")
            .select("full_score")
            .eq("id", internship_id)
            .limit(1)
            .execute()
        )
        
        full_score = 0
        if internship_res.data:
            full_score = int(internship_res.data[0].get("full_score") or 0)
        
        # Auto-approve ALL drafts regardless of score
        # Add random delay to approved_at timestamp
        # This makes auto-approved emails wait 10-30 minutes before sending
        delay_minutes = random.randint(AUTO_APPROVE_MIN_DELAY_MINUTES, AUTO_APPROVE_MAX_DELAY_MINUTES)
        approved_at = now + timedelta(minutes=delay_minutes)
        
        db.client.table("email_drafts").update({
            "status": "auto_approved",
            "approved_at": approved_at.isoformat()
        }).eq("id", row["id"]).execute()
        
        db.bump_daily_usage(today, auto_approvals=1)
        db.log_event(internship_id, "auto_approved", {
            "draft_id": row["id"],
            "full_score": full_score,
            "delay_minutes": delay_minutes,
            "will_send_after": approved_at.isoformat()
        })
        
        logger.info(f"Auto-approved draft {row['id']} (score: {full_score}) - will send after {delay_minutes} min delay")

