from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import httpx
import tldextract

from core.config import settings
from core.supabase_db import db, today_utc, utcnow

HUNTER_DAILY_LIMIT = 15


@dataclass
class HunterEmail:
    email: str
    confidence: int
    source: str = "hunter"
    recruiter_name: str | None = None


def extract_domain(url: str) -> str | None:
    ext = tldextract.extract(url)
    if not ext.domain or not ext.suffix:
        return None
    return f"{ext.domain}.{ext.suffix}".lower()


def find_company_domain(company_name: str) -> str | None:
    """
    Find the company's domain from the company name.
    Uses Hunter's Company Search API or simple heuristics.
    
    Examples:
        "Blitzenx" -> "blitzenx.com"
        "Google" -> "google.com"
        "Microsoft Research" -> "microsoft.com"
    """
    if not company_name:
        return None
    
    # Clean company name
    company_clean = company_name.lower().strip()
    
    # Remove common suffixes (order matters - longer first)
    suffixes = [
        " private limited", " pvt ltd", " pvt. ltd.", " pvt. ltd",
        " inc.", " inc", " llc", " ltd.", " ltd", 
        " corporation", " corp.", " corp", " company", " co."," co"
    ]
    for suffix in suffixes:
        if company_clean.endswith(suffix):
            company_clean = company_clean[:-len(suffix)].strip()
            break  # Only remove one suffix
    
    # Remove special characters and spaces
    company_clean = "".join(c for c in company_clean if c.isalnum())
    
    if not company_clean:
        return None
    
    # Try common TLDs
    common_tlds = [".com", ".ai", ".io", ".co", ".in"]
    
    # First, check if we have this domain cached in company_domains
    for tld in common_tlds:
        potential_domain = f"{company_clean}{tld}"
        cached = (
            db.client.table("company_domains")
            .select("domain")
            .eq("domain", potential_domain)
            .limit(1)
            .execute()
        )
        if cached.data:
            return potential_domain
    
    # Default to .com
    return f"{company_clean}.com"


def _filter_emails(items: list[dict[str, Any]]) -> list[HunterEmail]:
    preferred_locals = ("hr@", "hiring@", "recruiter@", "talent@", "careers@")
    out: list[HunterEmail] = []
    for it in items:
        email = (it.get("value") or it.get("email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        conf = int(it.get("confidence") or 0)
        if conf < 80:
            continue
        out.append(HunterEmail(email=email, confidence=conf))

    out.sort(
        key=lambda e: (
            0 if any(e.email.startswith(p) for p in preferred_locals) else 1,
            -e.confidence,
        )
    )
    return out


def search_domain_for_email(domain: str) -> HunterEmail | None:
    """
    Phase 6 — Hunter credit shield:
    - cache per domain in company_domains
    - enforce daily limit via daily_usage_stats.hunter_calls
    """
    # cache check
    cached = (
        db.client.table("company_domains")
        .select("*")
        .eq("domain", domain)
        .limit(1)
        .execute()
    )
    if cached.data:
        row = cached.data[0]
        if row.get("hunter_called") and row.get("emails"):
            emails = row["emails"]
            if isinstance(emails, list) and emails:
                return HunterEmail(
                    email=str(emails[0].get("email") or emails[0].get("value")),
                    confidence=int(emails[0].get("confidence") or 80),
                )

    # daily guard
    usage = db.get_or_create_daily_usage(today_utc())
    if usage.hunter_calls >= HUNTER_DAILY_LIMIT:
        return None

    if not settings.hunter_api_key:
        return None

    try:
        url = "https://api.hunter.io/v2/domain-search"
        resp = httpx.get(
            url,
            params={"domain": domain, "api_key": settings.hunter_api_key},
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        items = (data.get("data") or {}).get("emails") or []
        filtered = _filter_emails(items)

        # cache result
        db.client.table("company_domains").upsert(
            {
                "domain": domain,
                "emails": [e.__dict__ for e in filtered],
                "hunter_called": True,
                "last_checked": utcnow().isoformat(),
            },
            on_conflict="domain",
        ).execute()

        db.bump_daily_usage(today_utc(), hunter_calls=1)
        return filtered[0] if filtered else None
    except Exception as e:
        # Send error notification
        from core.guards import send_error_notification
        send_error_notification(
            error_type="Hunter API",
            error_message=str(e),
            context={"domain": domain}
        )
        
        db.insert_retry(
            phase="hunter",
            payload={"domain": domain},
            next_retry_at=utcnow() + timedelta(minutes=15),
            last_error=str(e),
        )
        return None

