from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from core.supabase_db import db, utcnow
from approval.webhook_handler import validate_twilio_request
from core.logger import logger

router = APIRouter(prefix="/twilio")


@router.post("/webhook", response_class=PlainTextResponse)
async def twilio_webhook(request: Request) -> str:
    """
    Twilio WhatsApp webhook handler.
    Processes YES/NO/PREVIEW responses for email draft approval.
    """
    await validate_twilio_request(request)

    form = await request.form()
    body = (form.get("Body") or "").strip().upper()
    
    logger.info(f"Received WhatsApp message: {body}")

    # Extract DRAFT:<id> from message
    incoming = (form.get("Body") or "").strip()
    draft_id = None
    for token in incoming.split():
        if token.upper().startswith("DRAFT:"):
            draft_id = token.upper().replace("DRAFT:", "").strip()
            break

    if not draft_id:
        logger.warning("Missing DRAFT:<id> in WhatsApp response")
        return "⚠️ Missing DRAFT:<id> token. Reply with YES/NO/PREVIEW and include DRAFT:<id>."

    draft = db.get_email_draft(draft_id)
    if not draft:
        logger.warning(f"Draft not found: {draft_id}")
        return "❌ Draft not found. It may have been already processed."

    # Handle YES response
    if "YES" in body:
        db.update_email_draft(
            draft_id,
            {"status": "approved", "approved_at": utcnow().isoformat()},
        )
        logger.info(f"Draft {draft_id} approved via WhatsApp")
        return "✅ *Approved!* Your email will be queued for sending."

    # Handle NO response
    if "NO" in body:
        db.update_email_draft(draft_id, {"status": "rejected"})
        logger.info(f"Draft {draft_id} rejected via WhatsApp")
        
        # Move to quarantine
        lead_id = draft.get("lead_id")
        if lead_id:
            from outreach.quarantine_manager import move_to_quarantine
            move_to_quarantine(lead_id, draft_id)
        
        return "❌ *Rejected.* Moved to quarantine for re-evaluation in 14 days."

    # Handle PREVIEW response
    if "PREVIEW" in body:
        subject = draft.get("subject", "")
        email_body = draft.get("body", "")
        preview = f"📧 *Email Preview*\n\n*Subject:* {subject}\n\n{email_body}"
        logger.info(f"Preview requested for draft {draft_id}")
        return preview[:1500]  # WhatsApp message limit

    logger.warning(f"Unrecognized WhatsApp response: {body}")
    return "❓ Unrecognized reply. Use:\n✅ YES\n❌ NO\n👁️ PREVIEW\n\n(Include DRAFT:<id> in your message)"

