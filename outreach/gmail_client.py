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


def _create_message(*, to: str, subject: str, body: str) -> dict[str, Any]:
    import base64
    from email.message import EmailMessage

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(draft: dict[str, Any], lead: dict[str, Any]) -> None:
    """
    Sends a single email via Gmail API.
    """
    service = _build_service()
    msg = _create_message(
        to=lead["email"],
        subject=draft["subject"],
        body=draft["body"],
    )
    service.users().messages().send(userId=settings.gmail_sender, body=msg).execute()


def send_followup(followup: dict[str, Any]) -> None:
    service = _build_service()
    msg = _create_message(
        to=followup["email"],
        subject=f"Following up on your internship application",
        body=followup["followup_body"],
    )
    service.users().messages().send(userId=settings.gmail_sender, body=msg).execute()

