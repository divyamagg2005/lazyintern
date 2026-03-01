from __future__ import annotations

import argparse
from datetime import timedelta

from core.guards import process_retry_queue
from core.supabase_db import db, today_utc, utcnow
from outreach.queue_manager import process_email_queue, process_followups
from outreach.quarantine_manager import process_quarantine_re_evaluations
from approval.auto_approver import run_auto_approver
from pipeline.email_extractor import extract_from_internship
from pipeline.email_validator import validate_email
from pipeline.full_scorer import full_score
from pipeline.groq_client import generate_draft
from pipeline.pre_scorer import _load_resume, pre_score  # type: ignore[attr-defined]
from approval.twilio_sender import send_approval_sms
from pipeline.hunter_client import extract_domain, find_company_domain, search_domain_for_email
from scraper.scrape_router import discover_and_store

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
                    "reason": "Lead already exists for this internship_id"
                })
                continue
            
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
                    "reason": "Lead already exists for this internship_id"
                })
                continue
            
            db.log_event(iid, "email_found_regex", {"email": extracted.email})

        # Phase 5 — validation
        v = validate_email(lead["email"], int(lead.get("confidence") or 0))
        if not v.valid:
            db.bump_daily_usage(today, validation_fails=1)
            db.client.table("leads").update(
                {"verified": False, "mx_valid": v.mx_valid, "smtp_valid": v.smtp_valid}
            ).eq("id", lead["id"]).execute()
            db.log_event(iid, "email_invalid", {"reason": v.reason})
            
            # NOTE: Don't change internship status here - let it continue to scoring
            # The lead is marked as unverified, but we still want to score and generate drafts
            # Status will be updated after scoring (low_priority if score < 60, or after draft generation)

        else:
            db.client.table("leads").update(
                {"verified": True, "mx_valid": v.mx_valid, "smtp_valid": v.smtp_valid}
            ).eq("id", lead["id"]).execute()
            db.log_event(iid, "email_valid", {})

        # Phase 7 — full scoring
        fs = full_score(internship, resume)
        db.client.table("internships").update(
            {"full_score": int(fs.score)}
        ).eq("id", iid).execute()
        db.log_event(iid, "full_scored", {"score": fs.score, "breakdown": fs.breakdown})

        # Generate drafts for all scored internships (no minimum threshold)
        # User wants to reach out to all opportunities

        # Phase 8 — Groq personalization
        draft_obj = generate_draft(lead, internship, resume)
        draft = db.insert_email_draft(
            {
                "lead_id": lead["id"],
                "subject": draft_obj.subject,
                "body": draft_obj.body,
                "followup_body": draft_obj.followup_body,
                "status": "generated",
            }
        )
        db.log_event(iid, "draft_generated", {"draft_id": draft["id"]})

        # Phase 9 — Twilio human approval (send SMS immediately after draft generation)
        send_approval_sms(draft, lead, internship, int(fs.score))
        
        # Mark internship as processed to prevent duplicate processing in next cycle
        db.client.table("internships").update(
            {"status": "pending_approval"}
        ).eq("id", iid).execute()
        db.log_event(iid, "approval_sent", {"draft_id": draft["id"]})


def run_cycle() -> None:
    """
    One complete cycle:
    1) Seed scoring_config if empty
    2) process existing discovered internships first
    3) run new discovery
    4) process newly discovered internships
    """
    # Ensure scoring_config is seeded before any scoring happens
    db.seed_scoring_config_if_empty()
    
    today = today_utc()
    db.get_or_create_daily_usage(today)

    process_retry_queue()
    process_followups()
    process_quarantine_re_evaluations()
    run_auto_approver()  # Auto-approve drafts after 2h timeout if score >= 90

    resume = _load_resume()
    _process_discovered_internships(resume, limit=200)

    # Phase 1 — discovery (best-effort)
    discover_and_store(limit=50)
    _process_discovered_internships(resume, limit=200)

    # Phase 11 / 12 — email queue + follow-ups
    process_email_queue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one LazyIntern scheduler cycle")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = parser.parse_args()

    run_cycle()


if __name__ == "__main__":
    main()

