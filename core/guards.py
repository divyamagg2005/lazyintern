from __future__ import annotations

from datetime import timedelta

from core.supabase_db import db, utcnow


def process_retry_queue() -> None:
    """
    Phase 14 retry processor with full dispatcher implementation.
    Re-executes failed API calls with exponential backoff.
    """
    pending = db.list_due_retries()
    now = utcnow()

    for job in pending:
        attempts = int(job.get("attempts") or 0)
        max_attempts = int(job.get("max_attempts") or 3)
        phase = job.get("phase", "")
        payload = job.get("payload") or {}

        try:
            # Dispatch to appropriate service based on phase
            if phase == "groq":
                _retry_groq(payload)
            elif phase == "twilio":
                _retry_twilio(payload)
            elif phase == "gmail":
                _retry_gmail(payload)
            elif phase == "hunter":
                _retry_hunter(payload)
            elif phase == "firecrawl":
                _retry_firecrawl(payload)
            else:
                # Unknown phase, mark as resolved to avoid infinite loop
                db.mark_retry_resolved(job["id"])
                continue

            # Success - mark as resolved
            db.mark_retry_resolved(job["id"])

        except Exception as e:
            # Failure - bump attempts and schedule next retry
            attempts += 1
            if attempts >= max_attempts:
                db.mark_retry_resolved(job["id"])
                # Log max retry failure for manual intervention
                db.log_event(
                    payload.get("internship_id"),
                    "max_retry_failure",
                    {"phase": phase, "error": str(e), "payload": payload},
                )
                continue

            backoff_minutes = 5 * (2**attempts)
            next_retry_at = now + timedelta(minutes=backoff_minutes)
            db.bump_retry_failure(
                job["id"],
                attempts=attempts,
                last_error=str(e),
                next_retry_at=next_retry_at,
            )


def _retry_groq(payload: dict) -> None:
    """Re-execute Groq draft generation."""
    from pipeline.groq_client import generate_draft
    from pipeline.pre_scorer import _load_resume

    lead_id = payload.get("lead_id")
    internship_id = payload.get("internship_id")

    if not lead_id or not internship_id:
        raise ValueError("Missing lead_id or internship_id in payload")

    # Fetch lead and internship
    lead = db.client.table("leads").select("*").eq("id", lead_id).limit(1).execute()
    if not lead.data:
        raise ValueError(f"Lead {lead_id} not found")

    internship = (
        db.client.table("internships")
        .select("*")
        .eq("id", internship_id)
        .limit(1)
        .execute()
    )
    if not internship.data:
        raise ValueError(f"Internship {internship_id} not found")

    resume = _load_resume()
    draft_obj = generate_draft(lead.data[0], internship.data[0], resume)

    # Insert draft
    db.insert_email_draft(
        {
            "lead_id": lead_id,
            "subject": draft_obj.subject,
            "body": draft_obj.body,
            "followup_body": draft_obj.followup_body,
            "status": "generated",
        }
    )


def _retry_twilio(payload: dict) -> None:
    """Re-execute Twilio notification SMS."""
    from approval.twilio_sender import send_notification_sms

    draft_id = payload.get("draft_id")
    if not draft_id:
        raise ValueError("Missing draft_id in payload")

    # Fetch draft with related data
    result = (
        db.client.table("email_drafts")
        .select("*, leads!inner(*, internships!inner(*))")
        .eq("id", draft_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Draft {draft_id} not found")

    row = result.data[0]
    draft = row
    lead = row["leads"]
    internship = lead["internships"]
    full_score = int(internship.get("full_score") or 0)

    send_notification_sms(draft, lead, internship, full_score)


def _retry_gmail(payload: dict) -> None:
    """Re-execute Gmail email sending."""
    from outreach import gmail_client

    draft_id = payload.get("draft_id")
    if not draft_id:
        raise ValueError("Missing draft_id in payload")

    # Fetch draft with lead email
    result = (
        db.client.table("email_drafts")
        .select("*, leads!inner(email)")
        .eq("id", draft_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Draft {draft_id} not found")

    row = result.data[0]
    draft = row
    lead = {"email": row["leads"]["email"]}

    gmail_client.send_email(draft, lead)


def _retry_hunter(payload: dict) -> None:
    """Re-execute Hunter domain search."""
    from pipeline.hunter_client import search_domain_for_email

    domain = payload.get("domain")
    internship_id = payload.get("internship_id")

    if not domain:
        raise ValueError("Missing domain in payload")

    result = search_domain_for_email(domain)
    if not result:
        raise ValueError(f"Hunter returned no results for {domain}")

    # If we have internship_id, create lead
    if internship_id:
        db.insert_lead(
            {
                "internship_id": internship_id,
                "recruiter_name": result.recruiter_name,
                "email": result.email,
                "source": result.source,
                "confidence": result.confidence,
            }
        )


def _retry_firecrawl(payload: dict) -> None:
    """Re-execute Firecrawl scraping."""
    from scraper.firecrawl_fetcher import fetch_firecrawl

    url = payload.get("url")
    if not url:
        raise ValueError("Missing url in payload")

    result = fetch_firecrawl(url)
    if not result:
        raise ValueError(f"Firecrawl failed for {url}")

