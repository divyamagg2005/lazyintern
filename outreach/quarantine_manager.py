from __future__ import annotations

from datetime import date

from core.supabase_db import db, utcnow, today_utc
from pipeline.full_scorer import full_score
from pipeline.pre_scorer import _load_resume  # type: ignore[attr-defined]


def move_to_quarantine(lead_id: str, draft_id: str) -> None:
    today = today_utc()
    db.client.table("quarantine").insert(
        {
            "lead_id": lead_id,
            "draft_id": draft_id,
            "re_evaluate_after": str(today.replace(day=today.day + 14)),
        }
    ).execute()


def process_quarantine_re_evaluations() -> None:
    """
    Re-evaluate quarantined leads after 14 days.
    If new score >= 75, re-enter pipeline at Groq phase.
    """
    from pipeline.groq_client import generate_draft
    from approval.twilio_sender import send_approval_sms

    today = today_utc()
    res = (
        db.client.table("quarantine")
        .select("*, leads!inner(*), email_drafts!inner(*)")
        .lte("re_evaluate_after", str(today))
        .eq("re_evaluated", False)
        .execute()
    )
    rows = res.data or []
    resume = _load_resume()

    for row in rows:
        lead = row["leads"]
        internship_id = lead["internship_id"]
        intern = (
            db.client.table("internships")
            .select("*")
            .eq("id", internship_id)
            .limit(1)
            .execute()
        ).data[0]

        # Re-score with updated weights and reply history
        fs = full_score(intern, resume)
        new_score = int(fs.score)

        # Mark as re-evaluated
        db.client.table("quarantine").update(
            {
                "re_evaluated": True,
                "re_evaluation_score": new_score,
            }
        ).eq("id", row["id"]).execute()

        # If score improved to >= 75, re-enter pipeline
        if new_score >= 75:
            db.log_event(
                internship_id,
                "quarantine_re_entry",
                {"old_score": intern.get("full_score"), "new_score": new_score},
            )

            # Update internship full_score
            db.client.table("internships").update(
                {"full_score": new_score, "status": "discovered"}
            ).eq("id", internship_id).execute()

            # Generate new draft
            draft_obj = generate_draft(lead, intern, resume)
            draft = db.insert_email_draft(
                {
                    "lead_id": lead["id"],
                    "subject": draft_obj.subject,
                    "body": draft_obj.body,
                    "followup_body": draft_obj.followup_body,
                    "status": "generated",
                }
            )

            # Send for approval
            send_approval_sms(draft, lead, intern, new_score)

            db.log_event(internship_id, "quarantine_re_entered", {"draft_id": draft["id"]})

