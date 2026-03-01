from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
import tldextract

from core.config import settings
from core.supabase_db import db, today_utc, utcnow

FIRECRAWL_DAILY_LIMIT = 10
FIRECRAWL_PER_DOMAIN_WEEK = 2


@dataclass
class FirecrawlResult:
    url: str
    content: str


def _domain(url: str) -> str | None:
    ext = tldextract.extract(url)
    if not ext.domain or not ext.suffix:
        return None
    return f"{ext.domain}.{ext.suffix}".lower()


def _week_start(d: date) -> date:
    return d.replace(day=d.day - (d.weekday()))  # Monday


def fetch_firecrawl(url: str) -> FirecrawlResult | None:
    """
    Tier 3 fallback. Enforces:
    - daily limit via daily_usage_stats.firecrawl_calls
    - per-domain weekly limit via company_domains.firecrawl_calls_this_week
    """
    if not settings.firecrawl_api_key:
        return None

    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    if usage.firecrawl_calls >= FIRECRAWL_DAILY_LIMIT:
        return None

    domain = _domain(url)
    if domain:
        week = _week_start(today)
        rec = (
            db.client.table("company_domains")
            .select("*")
            .eq("domain", domain)
            .limit(1)
            .execute()
        )
        calls = 0
        if rec.data:
            row = rec.data[0]
            if str(row.get("week_start") or "") == str(week):
                calls = int(row.get("firecrawl_calls_this_week") or 0)
        if calls >= FIRECRAWL_PER_DOMAIN_WEEK:
            return None

    try:
        # Minimal Firecrawl call (API may vary by plan; treat as best-effort)
        resp = httpx.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"url": url, "formats": ["html", "markdown"]},
            timeout=45.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        content = (
            payload.get("data", {}).get("html")
            or payload.get("data", {}).get("markdown")
            or ""
        )

        db.bump_daily_usage(today, firecrawl_calls=1)
        if domain:
            week = _week_start(today)
            db.client.table("company_domains").upsert(
                {
                    "domain": domain,
                    "week_start": str(week),
                    "firecrawl_calls_this_week": (calls + 1),
                    "last_checked": utcnow().isoformat(),
                },
                on_conflict="domain",
            ).execute()

        return FirecrawlResult(url=url, content=content)
    except Exception as e:
        # Send error notification
        from core.guards import send_error_notification
        send_error_notification(
            error_type="Firecrawl API",
            error_message=str(e),
            context={"url": url}
        )
        
        db.insert_retry(
            phase="firecrawl",
            payload={"url": url},
            next_retry_at=utcnow(),
            last_error=str(e),
        )
        return None

