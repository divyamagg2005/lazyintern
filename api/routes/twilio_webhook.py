from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator

from core.config import settings
from core.supabase_db import db, utcnow

router = APIRouter(prefix="/twilio")


def _require_twilio_config() -> None:
    missing = []
    if not settings.twilio_auth_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not settings.public_base_url:
        missing.append("PUBLIC_BASE_URL")
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Twilio webhook not configured (missing {', '.join(missing)})",
        )


async def _validate_twilio_signature(request: Request) -> None:
    _require_twilio_config()

    signature = request.headers.get("X-Twilio-Signature", "")
    url = f"{settings.public_base_url}{request.url.path}"
    form = await request.form()
    validator = RequestValidator(settings.twilio_auth_token)
    if not validator.validate(url, dict(form), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@router.post("/webhook", response_class=PlainTextResponse)
async def twilio_webhook(request: Request) -> str:
    await _validate_twilio_signature(request)

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

