from __future__ import annotations

import random
from datetime import datetime, timedelta

from core.supabase_db import db, today_utc, utcnow
from outreach import gmail_client
from scheduler.warmup import get_daily_limit
from core.logger import logger


def process_email_queue() -> None:
    """
    Process approved and auto-approved email drafts.
    Enforces:
    - Daily email limit
    - 45-55 minute spacing between emails
    - Respects approved_at timestamp (for delayed auto-approvals)
    - Only sends one email per cycle
    """
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)

    # In this minimal version we don't persist account_created_date;
    # assume warmup is already complete and use the configured daily_limit.
    daily_limit = usage.daily_limit or 15

    if usage.emails_sent >= daily_limit:
        return

    # Get last sent timestamp to enforce spacing
    last_sent = (
        db.client.table("email_drafts")
        .select("sent_at")
        .eq("status", "sent")
        .order("sent_at", desc=True)
        .limit(1)
        .execute()
    )

    now = utcnow()
    if last_sent.data:
        last_sent_at = datetime.fromisoformat(
            last_sent.data[0]["sent_at"].replace("Z", "+00:00")
        )
        # 45 minutes + random jitter (0-10 minutes)
        min_gap = timedelta(minutes=45 + random.randint(0, 10))
        time_since_last = now - last_sent_at

        if time_since_last < min_gap:
            # Not enough time has passed, skip this cycle
            return

    # Get drafts with status 'approved' or 'auto_approved'
    # For auto-approved drafts, only include those where approved_at <= now (delay has passed)
    res = (
        db.client.table("email_drafts")
        .select("*, leads!inner(email, internship_id)")
        .in_("status", ["approved", "auto_approved"])
        .order("approved_at", desc=False)  # Send oldest approvals first
        .limit(10)
        .execute()
    )
    drafts = res.data or []
    
    for row in drafts:
        draft = row
        
        # Check if approved_at timestamp has passed (for delayed auto-approvals)
        approved_at = draft.get("approved_at")
        if approved_at:
            approved_at_dt = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
            if approved_at_dt > now:
                # Delay hasn't passed yet, skip this draft
                logger.info(f"Skipping draft {draft['id']} - delay not passed yet (approved_at: {approved_at})")
                continue
        
        lead = {
            "email": row["leads"]["email"],
            "id": row["leads"].get("id"),
            "internship_id": row["leads"].get("internship_id")
        }

        if usage.emails_sent >= daily_limit:
            break

        gmail_client.send_email(draft, lead)
        usage = db.get_or_create_daily_usage(today)
        db.bump_daily_usage(today, emails_sent=1)
        
        # Log whether this was manual or auto-approved
        approval_type = "auto" if draft["status"] == "auto_approved" else "manual"
        logger.info(f"Email sent ({approval_type} approval) to {lead['email']} [{usage.emails_sent}/{daily_limit}]")
        
        # Only send one email per cycle to maintain spacing
        break


def process_followups() -> None:
    now = utcnow()
    today = today_utc()
    res = (
        db.client.table("followup_queue")
        .select(
            "*, email_drafts!inner(followup_body,status), leads!inner(email)"
        )
        .lte("send_after", str(today))
        .eq("sent", False)
        .execute()
    )
    rows = res.data or []
    for row in rows:
        draft = row["email_drafts"]
        if draft["status"] in ("replied_positive", "replied_negative"):
            continue
        payload = {
            "email": row["leads"]["email"],
            "followup_body": draft["followup_body"],
        }
        gmail_client.send_followup(payload)
        db.client.table("followup_queue").update(
            {"sent": True, "sent_at": now.isoformat()}
        ).eq("id", row["id"]).execute()


