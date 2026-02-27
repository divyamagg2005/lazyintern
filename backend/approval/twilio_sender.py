from __future__ import annotations

from typing import Any

from twilio.rest import Client

from core.config import settings
from core.supabase_db import db, utcnow
from core.logger import logger


def _twilio_client() -> Client | None:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return None
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_approval_sms(draft: dict[str, Any], lead: dict[str, Any], internship: dict[str, Any], full_score: int) -> None:
    """
    Phase 9 — send human approval via Twilio WhatsApp.
    If Twilio is not configured, we just log an event and skip.
    """
    client = _twilio_client()
    if not client or not settings.twilio_from_number or not settings.approver_to_number:
        logger.warning("Twilio not configured, skipping approval SMS")
        db.log_event(internship.get("id"), "approval_skipped_no_twilio", {})
        return

    score_pct = f"{full_score}%"
    
    # WhatsApp-formatted message with emojis
    body = (
        "🎯 *LazyIntern - New Lead*\n\n"
        f"*Company:* {internship.get('company')}\n"
        f"*Role:* {internship.get('role')}\n"
        f"*Score:* {score_pct}\n"
        f"*Email:* {lead.get('email')}\n"
        f"*Source:* {lead.get('source')}\n\n"
        "*Reply:*\n"
        "✅ YES - Approve & send\n"
        "❌ NO - Reject & quarantine\n"
        "👁️ PREVIEW - See full email\n\n"
        f"DRAFT:{draft.get('id')}"
    )

    try:
        # Send via WhatsApp (format: whatsapp:+1234567890)
        from_number = settings.twilio_from_number
        to_number = settings.approver_to_number
        
        # Ensure WhatsApp format
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        client.messages.create(
            from_=from_number,
            to=to_number,
            body=body,
        )
        
        db.client.table("email_drafts").update(
            {"approval_sent_at": utcnow().isoformat()}
        ).eq("id", draft["id"]).execute()
        
        db.log_event(internship.get("id"), "approval_sent", {"draft_id": draft["id"]})
        logger.info(f"WhatsApp approval sent for draft {draft['id']}")
        
    except Exception as e:
        logger.error(f"Twilio WhatsApp send failed: {e}")
        # On failure, log to retry_queue
        db.insert_retry(
            phase="twilio",
            payload={"draft_id": draft["id"]},
            next_retry_at=utcnow(),
            last_error=str(e),
        )

