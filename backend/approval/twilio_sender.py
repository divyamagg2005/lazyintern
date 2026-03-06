from __future__ import annotations

import hashlib
from typing import Any

from twilio.rest import Client

from core.config import settings
from core.supabase_db import db, today_utc, utcnow
from core.logger import logger


def _generate_short_code(draft_id: str) -> str:
    """Generate a 6-character short code from draft ID."""
    # Use first 6 chars of MD5 hash for consistency
    return hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()


def _twilio_client() -> Client | None:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return None
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_notification_sms(draft: dict[str, Any], lead: dict[str, Any], internship: dict[str, Any], full_score: int) -> None:
    """
    Send notification SMS when email is queued for sending.
    Enforces daily SMS limit of 50 messages.
    If Twilio is not configured, we just log an event and skip.
    """
    client = _twilio_client()
    if not client or not settings.twilio_from_number or not settings.approver_to_number:
        logger.warning("⚠️  Twilio not configured, skipping notification SMS")
        db.log_event(internship.get("id"), "notification_skipped_no_twilio", {})
        return

    # Check daily SMS limit
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    SMS_DAILY_LIMIT = 50

    if usage.twilio_sms_sent >= SMS_DAILY_LIMIT:
        logger.warning(f"⚠️  SMS daily limit reached ({usage.twilio_sms_sent}/{SMS_DAILY_LIMIT}), skipping notification SMS")
        db.log_event(internship.get("id"), "notification_skipped_sms_limit", {
            "sms_sent_today": usage.twilio_sms_sent,
            "limit": SMS_DAILY_LIMIT
        })
        return

    score_pct = f"{full_score}%"
    draft_id = draft.get("id", "")

    # SMS message (160 chars limit, keep it concise)
    company = internship.get('company', 'Unknown')[:30]
    role = internship.get('role', 'Unknown')[:40]
    email = lead.get('email', '')[:40]

    body = (
        f"LazyIntern: Email SENT to {role} at {company} ({email}). "
        f"Score: {score_pct}"
    )

    try:
        # Send via regular SMS (no whatsapp: prefix)
        from_number = settings.twilio_from_number
        to_number = settings.approver_to_number

        # Remove whatsapp: prefix if present (use regular SMS)
        if from_number.startswith("whatsapp:"):
            from_number = from_number.replace("whatsapp:", "")
        if to_number.startswith("whatsapp:"):
            to_number = to_number.replace("whatsapp:", "")

        client.messages.create(
            from_=from_number,
            to=to_number,
            body=body,
        )

        # Increment SMS counter
        db.bump_daily_usage(today, twilio_sms_sent=1)

        db.log_event(internship.get("id"), "notification_sent", {
            "draft_id": draft_id,
            "sms_count_today": usage.twilio_sms_sent + 1
        })
        logger.info(f"✅ SMS notification sent for draft {draft_id} [{usage.twilio_sms_sent + 1}/{SMS_DAILY_LIMIT}]")

    except Exception as e:
        logger.error(f"❌ Twilio SMS send failed: {e}")
        
        # Send error notification (avoid recursion - only notify for non-error-notification failures)
        from core.guards import send_error_notification
        send_error_notification(
            error_type="Twilio",
            error_message=str(e),
            context={"draft_id": draft_id}
        )
        
        # On failure, log to retry_queue
        db.insert_retry(
            phase="twilio",
            payload={"draft_id": draft_id},
            next_retry_at=utcnow(),
            last_error=str(e),
        )


