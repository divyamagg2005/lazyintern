"""
One-time backfill script to generate email drafts for existing leads.
Queries all verified leads without drafts and generates Groq emails + sends Twilio SMS.
"""

from __future__ import annotations

import time
from typing import Any

from core.supabase_db import db
from core.logger import logger
from pipeline.groq_client import generate_draft
from pipeline.pre_scorer import _load_resume
from approval.twilio_sender import send_notification_sms


def backfill_existing_leads() -> None:
    """
    One-time backfill for existing leads that don't have email drafts yet.
    
    Process:
    1. Query all verified leads without drafts
    2. For each lead: generate Groq draft → save to email_drafts → send Twilio SMS
    3. Add 3 second delay between each SMS to avoid rate limiting
    """
    logger.info("=" * 70)
    logger.info("Starting backfill for existing leads without drafts")
    logger.info("=" * 70)
    
    try:
        # Query ALL leads (including unverified)
        leads_result = (
            db.client.table("leads")
            .select("*")
            .execute()
        )
        
        all_leads = leads_result.data or []
        
        if not all_leads:
            logger.info("No leads found. Backfill not needed.")
            return
        
        # Query all existing drafts
        drafts_result = (
            db.client.table("email_drafts")
            .select("lead_id")
            .execute()
        )
        
        existing_draft_lead_ids = set(
            draft["lead_id"] for draft in (drafts_result.data or [])
        )
        
        # Filter leads that don't have drafts
        leads_without_drafts = [
            lead for lead in all_leads
            if lead["id"] not in existing_draft_lead_ids
        ]
        
        total_leads = len(leads_without_drafts)
        
        if total_leads == 0:
            logger.info("No leads found without drafts. Backfill not needed.")
            return
        
        logger.info(f"Found {total_leads} leads without drafts. Starting backfill...")
        
        # Load resume once for all drafts
        resume = _load_resume()
        
        success_count = 0
        error_count = 0
        
        for idx, lead in enumerate(leads_without_drafts, 1):
            try:
                lead_id = lead.get("id")
                internship_id = lead.get("internship_id")
                email = lead.get("email")
                
                # Fetch internship details
                internship_result = (
                    db.client.table("internships")
                    .select("*")
                    .eq("id", internship_id)
                    .limit(1)
                    .execute()
                )
                
                if not internship_result.data:
                    logger.warning(f"[{idx}/{total_leads}] Internship not found for lead {lead_id}, skipping")
                    error_count += 1
                    continue
                
                internship = internship_result.data[0]
                company = internship.get("company", "Unknown")
                role = internship.get("role", "Unknown")
                full_score = internship.get("full_score") or 0  # Default to 0 if None
                
                logger.info(f"[{idx}/{total_leads}] Processing: {email} at {company}")
                
                # Generate Groq draft
                draft_obj = generate_draft(lead, internship, resume)
                
                # Save to email_drafts
                draft = db.insert_email_draft({
                    "lead_id": lead_id,
                    "subject": draft_obj.subject,
                    "body": draft_obj.body,
                    "followup_body": draft_obj.followup_body,
                    "status": "generated",
                })
                
                db.log_event(internship_id, "backfill_draft_generated", {
                    "draft_id": draft["id"],
                    "email": email
                })
                
                # Send Twilio SMS notification
                send_notification_sms(draft, lead, internship, full_score)
                
                logger.info(f"[{idx}/{total_leads}] ✓ Backfill draft created for {email} at {company}")
                success_count += 1
                
                # Add 3 second delay to avoid Twilio rate limiting
                if idx < total_leads:  # Don't delay after last one
                    time.sleep(3)
                
            except Exception as e:
                logger.error(f"[{idx}/{total_leads}] ✗ Error processing lead {lead.get('id')}: {e}")
                error_count += 1
                continue
        
        logger.info("=" * 70)
        logger.info(f"Backfill complete: {success_count} success, {error_count} errors")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        import traceback
        traceback.print_exc()


def should_run_backfill() -> bool:
    """
    Check if backfill should run.
    Only run if there are leads without drafts (verified or unverified).
    """
    try:
        # Get ALL leads (including unverified)
        leads_result = (
            db.client.table("leads")
            .select("id")
            .execute()
        )
        
        all_lead_ids = set(lead["id"] for lead in (leads_result.data or []))
        total_leads = len(all_lead_ids)
        
        if total_leads == 0:
            logger.info("No verified leads found. Backfill not needed.")
            return False
        
        # Get all existing drafts
        drafts_result = (
            db.client.table("email_drafts")
            .select("lead_id")
            .execute()
        )
        
        existing_draft_lead_ids = set(
            draft["lead_id"] for draft in (drafts_result.data or [])
        )
        
        # Count leads without drafts
        leads_without_drafts = all_lead_ids - existing_draft_lead_ids
        missing_count = len(leads_without_drafts)
        
        if missing_count > 0:
            logger.info(f"Backfill check: {total_leads} leads, {missing_count} without drafts. Backfill needed.")
            return True
        
        logger.info(f"Backfill check: {total_leads} leads, all have drafts. Backfill not needed.")
        return False
        
    except Exception as e:
        logger.error(f"Backfill check failed: {e}")
        return False


if __name__ == "__main__":
    # Run backfill if needed
    if should_run_backfill():
        backfill_existing_leads()
    else:
        logger.info("Backfill not needed. Exiting.")
