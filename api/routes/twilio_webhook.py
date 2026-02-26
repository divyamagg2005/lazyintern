from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from core.supabase_db import db, utcnow
from approval.webhook_handler import validate_twilio_request

router = APIRouter(prefix="/twilio")


@router.post("/webhook", response_class=PlainTextResponse)
async def twilio_webhook(request: Request) -> str:
    await validate_twilio_request(request)

    form = await request.form()
    body = (form.get("Body") or "").strip().upper()

    # We encode draft_id in the SMS as: "DRAFT:<uuid>"
    raw = (form.get("SmsSid") or "").strip()
    _ = raw  # SmsSid is not used currently but can be logged later

    # Twilio doesn't send custom metadata back reliably; simplest is "DRAFT:<id>" in message.
    # If absent, we do nothing.
    incoming = (form.get("Body") or "").strip()
    draft_id = None
    for token in incoming.split():
        if token.startswith("DRAFT:"):
            draft_id = token.replace("DRAFT:", "").strip()
            break

    if not draft_id:
        return "Missing DRAFT:<id> token. Reply with YES/NO/PREVIEW and include DRAFT:<id>."

    draft = db.get_email_draft(draft_id)
    if not draft:
        return "Draft not found."

    if body.startswith("YES"):
        db.update_email_draft(
            draft_id,
            {"status": "approved", "approved_at": utcnow().isoformat()},
        )
        return "Approved. It will be queued for sending."

    if body.startswith("NO"):
        db.update_email_draft(draft_id, {"status": "rejected"})
        return "Rejected. Moved to quarantine."

    if "PREVIEW" in body:
        preview = f"Subject: {draft.get('subject')}\n\n{draft.get('body')}"
        return preview[:1500]

    return "Unrecognized reply. Use YES / NO / PREVIEW (and include DRAFT:<id>)."

