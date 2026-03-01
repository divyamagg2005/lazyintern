from __future__ import annotations

from datetime import timedelta
from typing import Any

from core.supabase_db import db, utcnow
from core.config import settings
from core.logger import logger


def send_error_notification(error_type: str, error_message: str, context: dict[str, Any] | None = None) -> None:
    """
    Send error notification SMS to approver when critical failures occur.
    
    Args:
        error_type: Type of error (e.g., "Groq API", "Hunter API", "Gmail", "Twilio", "Database")
        error_message: Detailed error message
        context: Optional context dict with additional info (lead_id, internship_id, etc.)
    """
    try:
        # Check if Twilio is configured
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            logger.warning("Twilio not configured, skipping error notification")
            return
        
        if not settings.twilio_from_number or not settings.approver_to_number:
            logger.warning("Twilio phone numbers not configured, skipping error notification")
            return
        
        # Import here to avoid circular dependency
        from twilio.rest import Client
        
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        
        # Format message (SMS has 160 char limit, keep concise)
        # Truncate error_message if too long
        max_error_len = 100
        if len(error_message) > max_error_len:
            error_message = error_message[:max_error_len] + "..."
        
        body = f"LazyIntern ERROR: {error_type} - {error_message}"
        
        # Add context if provided
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in list(context.items())[:2]])
            if context_str:
                body += f" ({context_str})"
        
        # Remove whatsapp: prefix if present (use regular SMS)
        from_number = settings.twilio_from_number
        to_number = settings.approver_to_number
        
        if from_number.startswith("whatsapp:"):
            from_number = from_number.replace("whatsapp:", "")
        if to_number.startswith("whatsapp:"):
            to_number = to_number.replace("whatsapp:", "")
        
        # Send SMS
        client.messages.create(
            from_=from_number,
            to=to_number,
            body=body
        )
        
        logger.info(f"Error notification sent: {error_type}")
        
    except Exception as e:
        # Don't let error notification failures crash the system
        logger.error(f"Failed to send error notification: {e}")


def process_retry_queue() -> None:
    """
    Minimal implementation of Phase 14 retry processor.
    It only marks jobs as resolved or bumps attempts; concrete
    re-dispatch to external services will be added gradually.
    """
    try:
        pending = db.list_due_retries()
        now = utcnow()

        for job in pending:
            attempts = int(job.get("attempts") or 0)
            max_attempts = int(job.get("max_attempts") or 3)

            # For now, just simulate a permanent failure so we don't loop forever.
            attempts += 1
            if attempts >= max_attempts:
                db.mark_retry_resolved(job["id"])
                continue

            backoff_minutes = 5 * (2**attempts)
            next_retry_at = now + timedelta(minutes=backoff_minutes)
            db.bump_retry_failure(
                job["id"],
                attempts=attempts,
                last_error="Deferred (dispatcher not implemented yet)",
                next_retry_at=next_retry_at,
            )
    except Exception as e:
        logger.error(f"Database error in retry queue processing: {e}")
        send_error_notification(
            error_type="Database",
            error_message=f"Retry queue processing failed: {str(e)}",
            context={"function": "process_retry_queue"}
        )

