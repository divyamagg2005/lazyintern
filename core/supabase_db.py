from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from supabase import Client, create_client

from core.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def today_utc() -> date:
    return utcnow().date()


@dataclass(frozen=True)
class DailyUsage:
    date: date
    emails_sent: int
    daily_limit: int
    hunter_calls: int
    firecrawl_calls: int
    groq_calls: int
    groq_tokens_used: int
    pre_score_kills: int
    validation_fails: int
    auto_approvals: int


class SupabaseDB:
    def __init__(self) -> None:
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )

    # -------------------------
    # Usage stats / guards
    # -------------------------
    def get_or_create_daily_usage(self, d: date | None = None) -> DailyUsage:
        d = d or today_utc()
        res = (
            self.client.table("daily_usage_stats")
            .select("*")
            .eq("date", str(d))
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            return DailyUsage(
                date=d,
                emails_sent=int(row.get("emails_sent") or 0),
                daily_limit=int(row.get("daily_limit") or 0),
                hunter_calls=int(row.get("hunter_calls") or 0),
                firecrawl_calls=int(row.get("firecrawl_calls") or 0),
                groq_calls=int(row.get("groq_calls") or 0),
                groq_tokens_used=int(row.get("groq_tokens_used") or 0),
                pre_score_kills=int(row.get("pre_score_kills") or 0),
                validation_fails=int(row.get("validation_fails") or 0),
                auto_approvals=int(row.get("auto_approvals") or 0),
            )

        ins = self.client.table("daily_usage_stats").insert({"date": str(d)}).execute()
        row = ins.data[0]
        return DailyUsage(
            date=d,
            emails_sent=int(row.get("emails_sent") or 0),
            daily_limit=int(row.get("daily_limit") or 0),
            hunter_calls=int(row.get("hunter_calls") or 0),
            firecrawl_calls=int(row.get("firecrawl_calls") or 0),
            groq_calls=int(row.get("groq_calls") or 0),
            groq_tokens_used=int(row.get("groq_tokens_used") or 0),
            pre_score_kills=int(row.get("pre_score_kills") or 0),
            validation_fails=int(row.get("validation_fails") or 0),
            auto_approvals=int(row.get("auto_approvals") or 0),
        )

    def bump_daily_usage(self, d: date, **increments: int) -> None:
        usage = self.get_or_create_daily_usage(d)
        payload: dict[str, Any] = {"date": str(d)}
        for key, inc in increments.items():
            current = getattr(usage, key)
            payload[key] = int(current) + int(inc)
        self.client.table("daily_usage_stats").update(payload).eq("date", str(d)).execute()

    # -------------------------
    # Event log
    # -------------------------
    def log_event(self, internship_id: str | None, event: str, metadata: dict[str, Any] | None = None) -> None:
        self.client.table("pipeline_events").insert(
            {
                "internship_id": internship_id,
                "event": event,
                "metadata": metadata or {},
            }
        ).execute()

    # -------------------------
    # Internships / leads / drafts
    # -------------------------
    def upsert_internship(self, internship: dict[str, Any]) -> dict[str, Any] | None:
        # link is UNIQUE, so we can rely on upsert with on_conflict
        res = (
            self.client.table("internships")
            .upsert(internship, on_conflict="link")
            .select("*")
            .execute()
        )
        return res.data[0] if res.data else None

    def get_internship_by_link(self, link: str) -> dict[str, Any] | None:
        res = (
            self.client.table("internships")
            .select("*")
            .eq("link", link)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def insert_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        res = self.client.table("leads").insert(lead).select("*").execute()
        return res.data[0]

    def insert_email_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        res = self.client.table("email_drafts").insert(draft).select("*").execute()
        return res.data[0]

    def insert_followup(self, followup: dict[str, Any]) -> dict[str, Any]:
        res = self.client.table("followup_queue").insert(followup).select("*").execute()
        return res.data[0]

    def update_email_draft(self, draft_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        res = (
            self.client.table("email_drafts")
            .update(patch)
            .eq("id", draft_id)
            .select("*")
            .execute()
        )
        return res.data[0]

    def get_email_draft(self, draft_id: str) -> dict[str, Any] | None:
        res = (
            self.client.table("email_drafts")
            .select("*")
            .eq("id", draft_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def list_generated_drafts_pending_approval(self) -> list[dict[str, Any]]:
        res = (
            self.client.table("email_drafts")
            .select("*")
            .eq("status", "generated")
            .execute()
        )
        return list(res.data or [])

    # -------------------------
    # Retry queue
    # -------------------------
    def list_due_retries(self, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or utcnow()
        res = (
            self.client.table("retry_queue")
            .select("*")
            .eq("resolved", False)
            .lte("next_retry_at", now.isoformat())
            .execute()
        )
        return list(res.data or [])

    def insert_retry(self, phase: str, payload: dict[str, Any], *, next_retry_at: datetime, max_attempts: int = 3, last_error: str | None = None) -> None:
        self.client.table("retry_queue").insert(
            {
                "phase": phase,
                "payload": payload,
                "attempts": 0,
                "max_attempts": max_attempts,
                "next_retry_at": next_retry_at.isoformat(),
                "last_error": last_error,
                "resolved": False,
            }
        ).execute()

    def mark_retry_resolved(self, retry_id: str) -> None:
        self.client.table("retry_queue").update({"resolved": True}).eq("id", retry_id).execute()

    def bump_retry_failure(self, retry_id: str, *, attempts: int, last_error: str, next_retry_at: datetime) -> None:
        self.client.table("retry_queue").update(
            {
                "attempts": attempts,
                "last_error": last_error,
                "next_retry_at": next_retry_at.isoformat(),
            }
        ).eq("id", retry_id).execute()

    # -------------------------
    # Scoring config
    # -------------------------
    def get_scoring_weights(self) -> dict[str, float]:
        res = self.client.table("scoring_config").select("key,weight").execute()
        weights: dict[str, float] = {}
        for row in (res.data or []):
            weights[str(row["key"])] = float(row["weight"])
        return weights


db = SupabaseDB()

