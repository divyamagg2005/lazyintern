from __future__ import annotations

from datetime import timedelta

from core.supabase_db import db, utcnow


def process_retry_queue() -> None:
    """
    Minimal implementation of Phase 14 retry processor.
    It only marks jobs as resolved or bumps attempts; concrete
    re-dispatch to external services will be added gradually.
    """
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

