from __future__ import annotations

import argparse
import logging
from datetime import timedelta

from approval.twilio_sender import send_notification_sms
from core.guards import process_retry_queue
from core.supabase_db import db, today_utc, utcnow
from outreach.queue_manager import process_email_queue, process_followups
from outreach.quarantine_manager import process_quarantine_re_evaluations
from pipeline.email_extractor import extract_from_internship
from pipeline.email_validator import validate_email
from pipeline.full_scorer import full_score
from pipeline.groq_client import generate_draft
from pipeline.pre_scorer import _load_resume, pre_score  # type: ignore[attr-defined]
from pipeline.hunter_client import extract_domain, find_company_domain, search_domain_for_email
from scraper.scrape_router import discover_and_store

logger = logging.getLogger("lazyintern")

PRE_SCORE_THRESHOLD_REGEX = 40
PRE_SCORE_THRESHOLD_HUNTER = 60

# Job board domains that should never be searched via Hunter
JOB_BOARD_DOMAINS = {
    "linkedin.com",
    "internshala.com",
    "wellfound.com",
    "angellist.com",  # Old name for Wellfound
    "unstop.com",
    "workatastartup.com",
    "remoteok.com",
    "indeed.com",
    "glassdoor.com",
    "naukri.com",
    "monster.com",
    "dice.com",
}


def _process_discovered_internships(resume: dict[str, object], *, limit: int = 200) -> None:
    today = today_utc()
    internships = db.list_discovered_internships(limit=limit)
    
    if not internships:
        logger.info("📭 No new internships to process")
        return
    
    logger.info("=" * 80)
    logger.info(f"🔍 PROCESSING {len(internships)} DISCOVERED INTERNSHIPS")
    logger.info("=" * 80)

    for internship in internships:
        iid = internship["id"]

        # Phase 3 — pre-score
        ps = pre_score(internship)
        db.client.table("internships").update(
            {"pre_score": ps.score}
        ).eq("id", iid).execute()
        db.log_event(iid, "pre_scored", {"pre_score": ps.score})

        if ps.score < PRE_SCORE_THRESHOLD_REGEX:
            db.bump_daily_usage(today, pre_score_kills=1)
            db.client.table("internships").update(
                {"status": "low_priority"}
            ).eq("id", iid).execute()
            continue

        # Phase 4 — regex extraction
        extracted = extract_from_internship(internship)
        if not extracted:
            db.log_event(iid, "no_email_found", {})

            # Phase 6 — Hunter (only if pre_score >= 60)
            if ps.score < PRE_SCORE_THRESHOLD_HUNTER:
                db.log_event(iid, "no_email_low_score", {"pre_score": ps.score})
                continue

            # Extract company domain from company name, NOT from job board URL
            company_name = internship.get("company") or ""
            domain = find_company_domain(company_name)
            if not domain:
                db.log_event(iid, "no_company_domain", {"company": company_name})
                continue
            
            # CRITICAL: Never call Hunter for job board domains
            if domain in JOB_BOARD_DOMAINS:
                db.log_event(iid, "hunter_blocked_job_board", {
                    "domain": domain, 
                    "company": company_name,
                    "reason": "Company domain is a job board platform"
                })
                db.client.table("internships").update(
                    {"status": "no_email"}
                ).eq("id", iid).execute()
                continue
            
            # EMAIL-LEVEL DEDUPLICATION: Check if domain was already contacted
            # This saves Hunter API calls for domains we've already emailed
            if db.check_domain_already_contacted(domain):
                db.log_event(iid, "hunter_skipped_domain_contacted", {
                    "domain": domain,
                    "company": company_name,
                    "reason": "Domain already contacted (email-level deduplication)"
                })
                db.client.table("internships").update(
                    {"status": "no_email"}
                ).eq("id", iid).execute()
                continue
            
            hunter = search_domain_for_email(domain)
            if not hunter:
                db.log_event(iid, "hunter_no_results", {"domain": domain, "company": company_name})
                continue

            lead = db.insert_lead(
                {
                    "internship_id": iid,
                    "recruiter_name": hunter.recruiter_name,
                    "email": hunter.email,
                    "source": hunter.source,
                    "confidence": hunter.confidence,
                }
            )
            
            # If lead is None, it means a duplicate was skipped
            if not lead:
                db.log_event(iid, "lead_duplicate_skipped", {
                    "email": hunter.email, 
                    "source": "hunter",
                    "reason": "Email already contacted or internship duplicate"
                })
                continue
            
            logger.info(f"✉️  EMAIL FOUND (Hunter): {hunter.email}")
            logger.info(f"🎯 LEAD CREATED & INSERTED IN SUPABASE")
            db.log_event(iid, "email_found_hunter", {"email": hunter.email, "domain": domain, "company": company_name})
        else:
            lead = db.insert_lead(
                {
                    "internship_id": iid,
                    "recruiter_name": extracted.recruiter_name,
                    "email": extracted.email,
                    "source": extracted.source,
                    "confidence": extracted.confidence,
                }
            )
            
            # If lead is None, it means a duplicate was skipped
            if not lead:
                db.log_event(iid, "lead_duplicate_skipped", {
                    "email": extracted.email,
                    "source": "regex",
                    "reason": "Email already contacted or internship duplicate"
                })
                continue
            
            logger.info(f"✉️  EMAIL FOUND (regex): {extracted.email}")
            logger.info(f"🎯 LEAD CREATED & INSERTED IN SUPABASE")
            db.log_event(iid, "email_found_regex", {"email": extracted.email})

        # Phase 5 — validation
        v = validate_email(lead["email"], int(lead.get("confidence") or 0))
        if not v.valid:
            db.bump_daily_usage(today, validation_fails=1)
            db.client.table("leads").update(
                {"verified": False, "mx_valid": v.mx_valid, "smtp_valid": v.smtp_valid}
            ).eq("id", lead["id"]).execute()
            logger.warning(f"⚠️  Email validation failed: {v.reason}")
            db.log_event(iid, "email_invalid", {"reason": v.reason})
            
            # NOTE: Don't change internship status here - let it continue to scoring
            # The lead is marked as unverified, but we still want to score and generate drafts
            # Status will be updated after scoring (low_priority if score < 60, or after draft generation)

        else:
            db.client.table("leads").update(
                {"verified": True, "mx_valid": v.mx_valid, "smtp_valid": v.smtp_valid}
            ).eq("id", lead["id"]).execute()
            logger.info(f"✅ Email validated successfully")
            db.log_event(iid, "email_valid", {})

        # Phase 7 — full scoring
        fs = full_score(internship, resume)
        db.client.table("internships").update(
            {"full_score": int(fs.score)}
        ).eq("id", iid).execute()
        logger.info(f"📊 FULL SCORE: {int(fs.score)}% - {internship.get('company')} - {internship.get('role')[:50]}")
        db.log_event(iid, "full_scored", {"score": fs.score, "breakdown": fs.breakdown})

        # Generate drafts for all scored internships (no minimum threshold)
        # User wants to reach out to all opportunities

        # Phase 8 — Groq personalization
        logger.info(f"🤖 Generating personalized email draft...")
        draft_obj = generate_draft(lead, internship, resume)
        draft = db.insert_email_draft(
            {
                "lead_id": lead["id"],
                "subject": draft_obj.subject,
                "body": draft_obj.body,
                "followup_body": draft_obj.followup_body,
                "status": "approved",
                "approved_at": utcnow().isoformat(),
            }
        )
        logger.info(f"✅ DRAFT GENERATED: '{draft_obj.subject}'")
        db.log_event(iid, "draft_generated", {"draft_id": draft["id"]})

        # Phase 9 — Immediate sending (no approval delay)
        # Send email IMMEDIATELY after draft generation
        logger.info(f"📧 Sending email to {lead['email']}...")
        try:
            from outreach import gmail_client
            gmail_client.send_email(draft, lead)
            db.bump_daily_usage(today, emails_sent=1)
            db.log_event(iid, "email_sent_immediately", {"draft_id": draft["id"]})
            logger.info(f"✅ EMAIL SENT to {lead['email']}")
        except Exception as e:
            logger.error(f"❌ Failed to send email immediately: {e}")
            # Email will be retried in next cycle via process_email_queue
        
        # Mark internship as processed
        db.client.table("internships").update(
            {"status": "email_sent"}
        ).eq("id", iid).execute()
        
        # Send notification SMS to inform user that email was sent
        logger.info(f"📱 Sending SMS notification...")
        send_notification_sms(draft, lead, internship, int(fs.score))
        logger.info(f"✅ SMS NOTIFICATION SENT")
        logger.info("=" * 80)


def run_cycle() -> None:
    """
    One complete cycle:
    0) Recovery: Process any pending approved drafts from previous interrupted runs
    1) Seed scoring_config if empty
    2) process existing discovered internships first
    3) run new discovery
    4) process newly discovered internships
    """
    from datetime import date
    
    # Print cycle start banner
    logger.info("\n" + "=" * 80)
    logger.info("🚀 LAZYINTERN CYCLE STARTED")
    logger.info("=" * 80)
    
    # Calculate and display rotation day
    day_of_cycle = (date.today().toordinal() % 3) + 1
    logger.info(f"📅 Date: {date.today()}")
    logger.info(f"🔄 3-Day Rotation: DAY {day_of_cycle} of 3")
    logger.info("=" * 80)
    
    # Ensure scoring_config is seeded before any scoring happens
    db.seed_scoring_config_if_empty()

    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    
    # Display current usage stats
    logger.info(f"📊 Today's Stats:")
    logger.info(f"   📧 Emails sent: {usage.emails_sent}/{usage.daily_limit or 15}")
    logger.info(f"   📱 SMS sent: {usage.twilio_sms_sent}/15")
    logger.info(f"   🤖 Groq calls: {usage.groq_calls}")
    logger.info("=" * 80 + "\n")

    # RECOVERY PHASE: Check for pending approved drafts before starting new discovery
    # This ensures continuity if the program was terminated mid-cycle
    logger.info("=" * 80)
    logger.info("🔄 RECOVERY PHASE: Checking for pending approved drafts...")
    logger.info("=" * 80)

    # Count pending approved drafts
    pending_drafts = (
        db.client.table("email_drafts")
        .select("id", count="exact")
        .in_("status", ["approved", "auto_approved"])
        .execute()
    )
    pending_count = pending_drafts.count or 0

    if pending_count > 0:
        logger.info(f"📬 Found {pending_count} pending approved draft(s) from previous run")
        logger.info("🔄 Processing pending drafts before starting new discovery...")

        # Process all pending drafts (respecting daily limits and spacing)
        drafts_sent = 0
        while True:
            # Check if we've hit daily limit
            usage = db.get_or_create_daily_usage(today)
            daily_limit = usage.daily_limit or 15

            if usage.emails_sent >= daily_limit:
                logger.info(f"⚠️  Daily email limit reached ({usage.emails_sent}/{daily_limit})")
                break

            # Try to send one email
            initial_count = usage.emails_sent
            process_email_queue()

            # Check if an email was sent
            usage = db.get_or_create_daily_usage(today)
            if usage.emails_sent > initial_count:
                drafts_sent += 1
                logger.info(f"✅ Sent pending email {drafts_sent} [{usage.emails_sent}/{daily_limit}]")
            else:
                # No email sent (likely due to spacing constraint)
                logger.info("⏸️  Spacing constraint active - will resume in next cycle")
                break

        if drafts_sent > 0:
            logger.info(f"✅ Recovery complete: {drafts_sent} pending email(s) sent")
        else:
            logger.info("⏸️  No emails sent (spacing constraint or daily limit)")
    else:
        logger.info("✅ No pending drafts found - starting fresh cycle")

    logger.info("=" * 80 + "\n")

    process_retry_queue()
    # process_followups()  # DISABLED: No follow-ups for now
    process_quarantine_re_evaluations()
    # run_auto_approver() removed - immediate approval in _process_discovered_internships makes this obsolete

    resume = _load_resume()
    _process_discovered_internships(resume, limit=200)

    # Phase 1 — discovery (best-effort)
    discover_and_store(limit=50)
    _process_discovered_internships(resume, limit=200)

    # Phase 11 / 12 — email queue + follow-ups
    process_email_queue()
    
    # Print cycle completion summary
    final_usage = db.get_or_create_daily_usage(today)
    logger.info("\n" + "=" * 80)
    logger.info("🏁 CYCLE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"📊 Final Stats:")
    logger.info(f"   📧 Emails sent today: {final_usage.emails_sent}/{final_usage.daily_limit or 15}")
    logger.info(f"   📱 SMS sent today: {final_usage.twilio_sms_sent}/15")
    logger.info(f"   🤖 Groq calls today: {final_usage.groq_calls}")
    logger.info(f"   🔍 Pre-score kills: {final_usage.pre_score_kills}")
    logger.info(f"   ❌ Validation fails: {final_usage.validation_fails}")
    logger.info("=" * 80 + "\n")




def main() -> None:
    parser = argparse.ArgumentParser(description="Run one LazyIntern scheduler cycle")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = parser.parse_args()

    run_cycle()


if __name__ == "__main__":
    main()

