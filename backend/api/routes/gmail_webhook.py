from __future__ import annotations

import base64
import json
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from core.logger import logger
from db.feedback.reply_classifier import classify
from db.feedback.score_updater import update_on_reply
from outreach.gmail_client import _build_service
from core.supabase_db import db

router = APIRouter(prefix="/gmail")


@router.post("/push", response_class=PlainTextResponse)
async def gmail_push_notification(request: Request) -> str:
    """
    Gmail Pub/Sub push notification handler.
    Receives real-time notifications when new emails arrive.
    """
    try:
        body = await request.json()
        
        # Pub/Sub sends message in this format
        message = body.get("message", {})
        if not message:
            logger.warning("No message in Pub/Sub payload")
            return "OK"
        
        # Decode the data
        data_b64 = message.get("data", "")
        if not data_b64:
            logger.warning("No data in Pub/Sub message")
            return "OK"
        
        data_json = base64.b64decode(data_b64).decode("utf-8")
        data = json.loads(data_json)
        
        # Extract email address and history ID
        email_address = data.get("emailAddress")
        history_id = data.get("historyId")
        
        logger.info(f"Gmail push notification received: {email_address}, historyId: {history_id}")
        
        # Process new messages
        await _process_new_messages()
        
        return "OK"
        
    except Exception as e:
        logger.error(f"Gmail push notification error: {e}")
        # Return 200 to acknowledge receipt (Pub/Sub will retry on non-200)
        return "OK"


async def _process_new_messages() -> None:
    """
    Check for new replies and process them.
    """
    try:
        service = _build_service()
        
        # Get recent messages from inbox
        response = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=10,
            q="is:unread"  # Only unread messages
        ).execute()
        
        messages = response.get("messages", [])
        
        for msg_ref in messages:
            msg_id = msg_ref["id"]
            
            # Get full message
            message = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()
            
            # Extract email details
            headers = message.get("payload", {}).get("headers", [])
            from_email = None
            subject = None
            
            for header in headers:
                if header["name"].lower() == "from":
                    from_email = header["value"]
                if header["name"].lower() == "subject":
                    subject = header["value"]
            
            # Get email body
            body = _extract_body(message.get("payload", {}))
            
            if not body or not from_email:
                continue
            
            # Classify reply
            reply_type = classify(body)
            logger.info(f"Reply classified as {reply_type} from {from_email}")
            
            # Find the lead by email
            lead_res = db.client.table("leads").select("*").eq("email", from_email).limit(1).execute()
            
            if not lead_res.data:
                logger.info(f"No lead found for {from_email}")
                continue
            
            lead = lead_res.data[0]
            lead_id = lead["id"]
            
            # Get internship to extract domain
            internship_res = db.client.table("internships").select("link").eq("id", lead["internship_id"]).limit(1).execute()
            
            if internship_res.data:
                link = internship_res.data[0].get("link", "")
                domain = link.split("//")[-1].split("/")[0] if "//" in link else link.split("/")[0]
                
                # Update company history and cancel follow-up if positive
                update_on_reply(domain, lead_id, reply_type)
            
            # Update draft status
            draft_res = db.client.table("email_drafts").select("id").eq("lead_id", lead_id).limit(1).execute()
            
            if draft_res.data:
                draft_id = draft_res.data[0]["id"]
                db.update_email_draft(draft_id, {"status": f"replied_{reply_type}"})
            
            # Mark as read
            service.users().messages().modify(
                userId="me",
                id=msg_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            
            logger.info(f"Processed reply from {from_email}: {reply_type}")
            
    except Exception as e:
        logger.error(f"Error processing new messages: {e}")


def _extract_body(payload: dict) -> str:
    """Extract email body from Gmail API payload."""
    body = ""
    
    # Check for plain text body
    if "body" in payload and "data" in payload["body"]:
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    
    # Check for multipart
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                if "data" in part.get("body", {}):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
            # Recursively check nested parts
            if "parts" in part:
                body = _extract_body(part)
                if body:
                    break
    
    return body.strip()


@router.get("/watch/setup")
async def setup_gmail_watch():
    """
    Setup Gmail push notifications.
    Call this endpoint to start receiving push notifications.
    """
    try:
        service = _build_service()
        
        # Get project ID from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        if not project_id:
            raise HTTPException(
                status_code=500, 
                detail="GOOGLE_CLOUD_PROJECT_ID not set in .env file"
            )
        
        # Topic format: projects/{project-id}/topics/{topic-name}
        request_body = {
            "labelIds": ["INBOX"],
            "topicName": f"projects/{project_id}/topics/gmail-push"
        }
        
        response = service.users().watch(userId="me", body=request_body).execute()
        
        logger.info(f"Gmail watch setup successful: {response}")
        return {"status": "success", "response": response}
        
    except Exception as e:
        logger.error(f"Gmail watch setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watch/stop")
async def stop_gmail_watch():
    """
    Stop Gmail push notifications.
    """
    try:
        service = _build_service()
        service.users().stop(userId="me").execute()
        
        logger.info("Gmail watch stopped")
        return {"status": "success", "message": "Gmail watch stopped"}
        
    except Exception as e:
        logger.error(f"Gmail watch stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
