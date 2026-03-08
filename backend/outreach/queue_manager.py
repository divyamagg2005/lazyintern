from __future__ import annotations

import random
import time
from datetime import datetime, timedelta

from core.supabase_db import db, today_utc, utcnow
from outreach import gmail_client
from scheduler.warmup import get_daily_limit
from core.logger import logger


def process_email_queue() -> None:
    """
    Process approved and auto-approved email drafts with spacing delays.
    
    Adds random delays between emails (45-90 seconds) to:
    - Prevent spam detection
    - Maintain Gmail account reputation
    - Simulate natural human sending patterns
    """
    today = today_utc()
    
    # Get ALL approved drafts (no limit)
    res = (
        db.client.table("email_drafts")
        .select("*, leads!inner(id, email, internship_id)")
        .in_("status", ["approved", "auto_approved"])
        .order("approved_at", desc=False)  # Send oldest approvals first
        .execute()
    )
    drafts = res.data or []
    
    if not drafts:
        return
    
    logger.info(f"Processing {len(drafts)} approved draft(s) with spacing delays")
    
    for idx, row in enumerate(drafts):
        draft = row
        
        lead = {
            "email": row["leads"]["email"],
            "id": row["leads"].get("id"),
            "internship_id": row["leads"].get("internship_id")
        }

        try:
            gmail_client.send_email(draft, lead)
            db.bump_daily_usage(today, emails_sent=1)
            
            # Log success
            approval_type = "auto" if draft["status"] == "auto_approved" else "manual"
            logger.info(f"✓ Email sent ({approval_type}) to {lead['email']}")
            
            # Add delay between emails (except after the last one)
            if idx < len(drafts) - 1:
                # Random delay between 45-90 seconds to simulate natural sending
                delay = random.randint(45, 90)
                logger.info(f"⏳ Waiting {delay} seconds before next email (spam prevention)...")
                time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Failed to send email to {lead['email']}: {e}")
            # Continue to next email instead of stopping
            continue


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


