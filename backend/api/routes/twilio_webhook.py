from __future__ import annotations

import hashlib
import re
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse

from core.supabase_db import db, utcnow
from approval.webhook_handler import validate_twilio_request
from outreach.gmail_client import send_email
from core.logger import logger

router = APIRouter(prefix="/twilio")


def _generate_short_code(draft_id: str) -> str:
    """Generate a 6-character short code from draft ID."""
    return hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()


def _find_draft_by_short_code(short_code: str) -> dict | None:
    """Find draft by 6-character short code (computed from draft ID)."""
    try:
        result = (
            db.client.table("email_drafts")
            .select("*")
            .eq("status", "generated")
            .execute()
        )
        
        for draft in (result.data or []):
            draft_id = draft["id"]
            computed_code = _generate_short_code(draft_id)
            if computed_code == short_code.upper():
                return draft
        
        return None
    except Exception as e:
        logger.error(f"Error finding draft by short code: {e}")
        return None


def _find_most_recent_pending_draft() -> dict | None:
    """Find the most recent pending draft (fallback if no code provided)."""
    try:
        result = (
            db.client.table("email_drafts")
            .select("*")
            .eq("status", "generated")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error finding recent draft: {e}")
        return None


@router.post("/reply", response_class=PlainTextResponse)
async def twilio_reply_webhook(request: Request) -> str:
    """
    Twilio SMS webhook handler for approval replies.
    Handles YES/NO responses with optional short codes.
    
    Expected formats:
    - "YES ABC123" (with short code)
    - "YES" (matches most recent pending draft)
    - "NO ABC123" (with short code)
    - "NO" (matches most recent pending draft)
    """
    await validate_twilio_request(request)

    form = await request.form()
    body = (form.get("Body") or "").strip()
    from_number = form.get("From", "")
    
    logger.info(f"Received SMS from {from_number}: {body}")

    # Parse message for YES/NO and optional code
    body_upper = body.upper()
    
    # Extract short code (6 alphanumeric chars) or full UUID
    code_match = re.search(r'\b([A-F0-9]{6})\b', body_upper)
    uuid_match = re.search(r'\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b', body, re.IGNORECASE)
    
    draft = None
    
    # Try to find draft by UUID first (backward compatibility)
    if uuid_match:
        draft_id = uuid_match.group(1)
        draft = db.get_email_draft(draft_id)
        logger.info(f"Found draft by UUID: {draft_id}")
    
    # Try to find draft by short code
    elif code_match:
        short_code = code_match.group(1)
        draft = _find_draft_by_short_code(short_code)
        if draft:
            logger.info(f"Found draft by short code: {short_code}")
        else:
            logger.warning(f"No draft found for short code: {short_code}")
    
    # Fallback: find most recent pending draft
    else:
        draft = _find_most_recent_pending_draft()
        if draft:
            logger.info(f"Using most recent pending draft: {draft['id']}")
    
    if not draft:
        logger.warning("No draft found for SMS reply")
        return "No pending draft found. Please include the code from the approval SMS."
    
    draft_id = draft["id"]
    lead_id = draft.get("lead_id")
    
    # Get lead and internship info for response message
    lead = None
    internship = None
    if lead_id:
        lead_result = db.client.table("leads").select("*").eq("id", lead_id).limit(1).execute()
        if lead_result.data:
            lead = lead_result.data[0]
            internship_id = lead.get("internship_id")
            if internship_id:
                internship_result = db.client.table("internships").select("*").eq("id", internship_id).limit(1).execute()
                if internship_result.data:
                    internship = internship_result.data[0]
    
    # Handle YES response
    if "YES" in body_upper:
        try:
            # Update draft status
            db.update_email_draft(
                draft_id,
                {"status": "approved", "approved_at": utcnow().isoformat()},
            )
            
            # Send email immediately
            if lead:
                send_email(draft, lead)
                
                email = lead.get("email", "")
                company = internship.get("company", "Unknown") if internship else "Unknown"
                
                logger.info(f"Draft {draft_id} approved and email sent to {email}")
                
                # Bump daily usage
                from core.supabase_db import today_utc
                db.bump_daily_usage(today_utc(), emails_sent=1)
                
                return f"Email sent to {email} at {company}"
            else:
                logger.error(f"Lead not found for draft {draft_id}")
                return "Approved, but lead not found. Email not sent."
                
        except Exception as e:
            logger.error(f"Error sending email for draft {draft_id}: {e}")
            return f"Approved, but email send failed: {str(e)[:100]}"
    
    # Handle NO response
    elif "NO" in body_upper:
        try:
            # Update draft status
            db.update_email_draft(draft_id, {"status": "rejected"})
            
            company = internship.get("company", "Unknown") if internship else "Unknown"
            
            logger.info(f"Draft {draft_id} rejected")
            
            # Move to quarantine
            if lead_id:
                try:
                    from outreach.quarantine_manager import move_to_quarantine
                    move_to_quarantine(lead_id, draft_id)
                    logger.info(f"Lead {lead_id} moved to quarantine")
                except Exception as e:
                    logger.error(f"Error moving to quarantine: {e}")
            
            return f"Skipped {company}. Moved to quarantine."
            
        except Exception as e:
            logger.error(f"Error rejecting draft {draft_id}: {e}")
            return f"Error rejecting: {str(e)[:100]}"
    
    else:
        logger.warning(f"Unrecognized SMS response: {body}")
        return "Reply YES or NO (with the code from the approval SMS)"


# Keep old webhook endpoint for backward compatibility
@router.post("/webhook", response_class=PlainTextResponse)
async def twilio_webhook(request: Request) -> str:
    """Legacy webhook - redirects to /reply endpoint."""
    return await twilio_reply_webhook(request)

