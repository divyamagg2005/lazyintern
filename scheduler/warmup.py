from __future__ import annotations

from datetime import date

from core.config import settings
from core.supabase_db import db, today_utc


def get_daily_limit(account_created_date: date, today: date) -> int:
    """
    Simple warmup schedule from final_pipeline.md.
    """
    days_active = (today - account_created_date).days
    if days_active <= 3:
        return 5
    if days_active <= 7:
        return 8
    if days_active <= 11:
        return 12
    return 15


def update_daily_limit_if_needed() -> None:
    """
    Update daily_limit in daily_usage_stats based on account age.
    Reads account_created_date from environment or uses first email sent date.
    """
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)

    # Try to get account_created_date from environment
    account_created_str = settings.gmail_account_created_date
    if account_created_str:
        try:
            account_created = date.fromisoformat(account_created_str)
        except ValueError:
            # Invalid format, fall back to first email date
            account_created = _get_first_email_date()
    else:
        # Not configured, use first email date
        account_created = _get_first_email_date()

    if not account_created:
        # No emails sent yet, use today as start date
        account_created = today

    # Calculate appropriate daily limit
    new_limit = get_daily_limit(account_created, today)

    # Update if different
    if usage.daily_limit != new_limit:
        db.client.table("daily_usage_stats").update(
            {"daily_limit": new_limit}
        ).eq("date", str(today)).execute()


def _get_first_email_date() -> date | None:
    """Get the date of the first email ever sent."""
    result = (
        db.client.table("email_drafts")
        .select("sent_at")
        .eq("status", "sent")
        .order("sent_at", desc=False)
        .limit(1)
        .execute()
    )

    if result.data:
        from datetime import datetime

        sent_at = datetime.fromisoformat(
            result.data[0]["sent_at"].replace("Z", "+00:00")
        )
        return sent_at.date()

    return None

