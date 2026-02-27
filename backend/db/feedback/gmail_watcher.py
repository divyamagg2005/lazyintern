from __future__ import annotations

"""
Phase 13 placeholder.

Full Gmail push notifications require Pub/Sub setup and a public HTTPS endpoint.
This module provides a minimal polling helper so you can test the reply classifier
and feedback loop without Pub/Sub.
"""

from typing import Any

from outreach.gmail_client import _build_service  # noqa: SLF001


def list_recent_messages(max_results: int = 10) -> list[dict[str, Any]]:
    service = _build_service()
    resp = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=max_results).execute()
    return list(resp.get("messages") or [])

