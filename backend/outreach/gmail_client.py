from __future__ import annotations

import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any

import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.config import settings
from core.supabase_db import db, today_utc, utcnow
from core.logger import logger

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
RESUME_PATH = Path(__file__).resolve().parents[1] / "data" / "resume.pdf"


def _load_credentials() -> Credentials:
    token_path = Path(settings.gmail_token_path)
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing Gmail OAuth token")
            creds.refresh(Request())
        else:
            logger.info("Starting Gmail OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.gmail_oauth_client_path, SCOPES
            )
            creds = flow.run_local_server(port=8080)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        logger.info("Gmail OAuth token saved")

    return creds


def _build_service():
    creds = _load_credentials()
    return build("gmail", "v1", credentials=creds)


def _create_message_with_attachment(*, to: str, subject: str, body: str, attachment_path: Path | None = None) -> dict[str, Any]:
    """Create email message with optional PDF attachment."""
    message = MIMEMultipart()
    message["To"] = to
    message["Subject"] = subject
    
    # Add body
    message.attach(MIMEText(body, "plain"))
    
    # Add resume attachment if exists
    if attachment_path and attachment_path.exists():
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment_path.name}"
            )
            message.attach(part)
            logger.info(f"📎 Attached resume: {attachment_path.name}")
    else:
        logger.warning(f"⚠️  Resume not found at {attachment_path}, sending without attachment")
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(draft: dict[str, Any], lead: dict[str, Any]) -> None:
    """
    Sends a single email via Gmail API with resume attachment.
    Updates draft status and daily usage stats.
    """
    try:
        service = _build_service()
        msg = _create_message_with_attachment(
            to=lead["email"],
            subject=draft["subject"],
            body=draft["body"],
            attachment_path=RESUME_PATH if RESUME_PATH.exists() else None
        )
        
        result = service.users().messages().send(userId=settings.gmail_sender, body=msg).execute()
        
        # Update draft status
        db.update_email_draft(
            draft["id"],
            {"status": "sent", "sent_at": utcnow().isoformat()}
        )
        
        # Log event - use internship_id from lead object (already available)
        internship_id = lead.get("internship_id")
        if internship_id:
            db.log_event(internship_id, "email_sent", {
                "draft_id": draft["id"],
                "email": lead["email"],
                "message_id": result.get("id")
            })
        
        # Schedule follow-up for day 5
        followup_date = (today_utc() + timedelta(days=5)).isoformat()
        db.insert_followup({
            "draft_id": draft["id"],
            "lead_id": lead.get("id"),
            "send_after": followup_date,
            "sent": False
        })
        logger.info(f"📅 Follow-up scheduled for {followup_date}")
        
        logger.info(f"✅ Email sent successfully to {lead['email']}")
        
    except Exception as e:
        logger.error(f"❌ Gmail send failed for {lead['email']}: {e}")
        
        # Send error notification
        from core.guards import send_error_notification
        send_error_notification(
            error_type="Gmail",
            error_message=str(e),
            context={
                "draft_id": draft["id"],
                "email": lead.get("email")
            }
        )
        
        # Add to retry queue
        db.insert_retry(
            phase="gmail",
            payload={"draft_id": draft["id"], "lead_id": lead.get("id")},
            next_retry_at=utcnow() + timedelta(minutes=10),
            last_error=str(e)
        )
        raise


def send_followup(followup: dict[str, Any]) -> None:
    """Send follow-up email (no attachment needed)."""
    try:
        service = _build_service()
        
        # Simple message without attachment
        message = EmailMessage()
        message["To"] = followup["email"]
        message["Subject"] = "Following up on internship application"
        message.set_content(followup["followup_body"])
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = service.users().messages().send(
            userId=settings.gmail_sender,
            body={"raw": raw}
        ).execute()
        
        logger.info(f"Follow-up sent to {followup['email']}")
        
    except Exception as e:
        logger.error(f"Follow-up send failed: {e}")
        raise

