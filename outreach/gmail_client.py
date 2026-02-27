from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _load_credentials() -> Credentials:
    token_path = Path(settings.gmail_token_path)
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.gmail_oauth_client_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def _build_service():
    creds = _load_credentials()
    return build("gmail", "v1", credentials=creds)


def _create_message(*, to: str, subject: str, body: str, in_reply_to: str | None = None, references: str | None = None) -> dict[str, Any]:
    import base64
    from email.message import EmailMessage

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    
    # Add threading headers for follow-ups
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(draft: dict[str, Any], lead: dict[str, Any]) -> None:
    """
    Sends a single email via Gmail API.
    Stores message ID for threading follow-ups.
    """
    service = _build_service()
    msg = _create_message(
        to=lead["email"],
        subject=draft["subject"],
        body=draft["body"],
    )
    result = service.users().messages().send(userId=settings.gmail_sender, body=msg).execute()
    
    # Store message ID for threading
    message_id = result.get("id")
    if message_id:
        from core.supabase_db import db
        db.client.table("email_drafts").update(
            {"status": "sent", "sent_at": datetime.now().isoformat()}
        ).eq("id", draft["id"]).execute()
        
        # Store message ID in metadata for follow-up threading
        db.log_event(
            draft.get("internship_id"),
            "email_sent",
            {"draft_id": draft["id"], "message_id": message_id}
        )


def send_followup(followup: dict[str, Any]) -> None:
    """
    Sends follow-up email with threading headers.
    """
    from core.supabase_db import db
    
    service = _build_service()
    
    # Get original message ID for threading
    draft_id = followup.get("draft_id")
    original_message_id = None
    
    if draft_id:
        events = (
            db.client.table("pipeline_events")
            .select("metadata")
            .eq("event", "email_sent")
            .contains("metadata", {"draft_id": draft_id})
            .limit(1)
            .execute()
        )
        if events.data:
            original_message_id = events.data[0].get("metadata", {}).get("message_id")
    
    msg = _create_message(
        to=followup["email"],
        subject=f"Re: Following up on your internship application",
        body=followup["followup_body"],
        in_reply_to=f"<{original_message_id}>" if original_message_id else None,
        references=f"<{original_message_id}>" if original_message_id else None,
    )
    service.users().messages().send(userId=settings.gmail_sender, body=msg).execute()

