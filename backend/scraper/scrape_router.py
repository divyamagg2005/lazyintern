from __future__ import annotations

import itertools
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from core.jsonc import load_jsonc
from core.supabase_db import db, utcnow
from pipeline.deduplicator import check_duplicate
from scraper.dynamic_fetcher import fetch_dynamic
from scraper.extractor import extract_internships_from_html
from scraper.firecrawl_fetcher import fetch_firecrawl
from scraper.http_fetcher import fetch, REMOTEOK_USER_AGENT
from core.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = PROJECT_ROOT / "data" / "job_source.json"
TRACKING_PATH = PROJECT_ROOT / "data" / "source_tracking.json"

SCRAPE_BATCH_LIMIT = 50

PROXY_POOL: list[str] = []
_proxy_cycle = itertools.cycle(PROXY_POOL)

# RemoteOK-specific settings
REMOTEOK_DELAY_RANGE = (8.0, 12.0)
REMOTEOK_MAX_RETRIES = 2


def get_next_proxy() -> str | None:
    if not PROXY_POOL:
        return None
    return next(_proxy_cycle)


def load_sources() -> list[dict[str, Any]]:
    data = load_jsonc(SOURCES_PATH)
    return list(data.get("sources") or [])


def _load_tracking() -> dict[str, Any]:
    """Load source tracking data (last scraped timestamps)."""
    if not TRACKING_PATH.exists():
        return {"sources": {}}
    try:
        return json.loads(TRACKING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"sources": {}}


def _save_tracking(tracking: dict[str, Any]) -> None:
    """Save source tracking data."""
    try:
        TRACKING_PATH.write_text(json.dumps(tracking, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to save source tracking: {e}")


def _should_scrape_source(source: dict[str, Any], tracking: dict[str, Any]) -> bool:
    """
    Check if source should be scraped based on scrape_frequency.
    
    Rules:
    - daily: scrape every cycle
    - weekly: only if last_scraped_at > 7 days ago
    - monthly: only if last_scraped_at > 30 days ago
    """
    url = source.get("url", "")
    frequency = source.get("scrape_frequency", "daily").lower()
    
    # Daily sources always scrape
    if frequency == "daily":
        return True
    
    # Check last scraped timestamp
    source_data = tracking.get("sources", {}).get(url, {})
    last_scraped = source_data.get("last_scraped_at")
    
    if not last_scraped:
        # Never scraped before, scrape now
        return True
    
    try:
        last_scraped_dt = datetime.fromisoformat(last_scraped.replace("Z", "+00:00"))
        now = utcnow()
        days_since_scrape = (now - last_scraped_dt).days
        
        if frequency == "weekly":
            should_scrape = days_since_scrape >= 7
            if not should_scrape:
                logger.info(f"Skipping weekly source (scraped {days_since_scrape} days ago): {source.get('name')}")
            return should_scrape
        
        elif frequency == "monthly":
            should_scrape = days_since_scrape >= 30
            if not should_scrape:
                logger.info(f"Skipping monthly source (scraped {days_since_scrape} days ago): {source.get('name')}")
            return should_scrape
        
        # Unknown frequency, default to daily
        return True
        
    except Exception as e:
        logger.warning(f"Error checking scrape frequency for {url}: {e}")
        return True  # Scrape on error to be safe


def _update_tracking(url: str, tracking: dict[str, Any]) -> None:
    """Update last_scraped_at timestamp for a source."""
    if "sources" not in tracking:
        tracking["sources"] = {}
    
    tracking["sources"][url] = {
        "last_scraped_at": utcnow().isoformat(),
        "last_scraped_success": True
    }
    _save_tracking(tracking)


def _is_remoteok_url(url: str) -> bool:
    """Check if URL is from RemoteOK"""
    return "remoteok.com" in url.lower() or "remoteok.io" in url.lower()


def _fetch_with_remoteok_handling(url: str, typ: str, proxy: str | None) -> tuple[str, bool]:
    """
    Fetch URL with RemoteOK-specific handling.
    Returns (html, should_use_firecrawl_fallback)
    """
    is_remoteok = _is_remoteok_url(url)

    if is_remoteok:
        # RemoteOK: custom User-Agent, 8-12 second delay, max 2 retries, NO Firecrawl fallback
        for attempt in range(REMOTEOK_MAX_RETRIES):
            if attempt > 0:
                # Additional delay between retries
                time.sleep(random.uniform(*REMOTEOK_DELAY_RANGE))

            res = fetch(
                url,
                proxy=proxy,
                delay_range=REMOTEOK_DELAY_RANGE,
                user_agent=REMOTEOK_USER_AGENT,
            )

            if res.text:
                return res.text, False

        # After max retries, return empty and NO Firecrawl fallback
        return "", False

    else:
        # Normal handling for non-RemoteOK URLs
        if typ == "dynamic":
            res = fetch_dynamic(url, proxy=proxy)
        else:
            res = fetch(url, proxy=proxy)

        # Allow Firecrawl fallback for non-RemoteOK URLs
        return res.text, True


def discover_and_store(*, limit: int = SCRAPE_BATCH_LIMIT) -> int:
    """
    Phase 1 — discovery:
    - loads `data/job_source.json`
    - respects scrape_frequency (daily/weekly/monthly)
    - fetches HTML (http/dynamic)
    - RemoteOK: custom User-Agent, 8-12s delay, 2 retries, NO Firecrawl fallback
    - Other sources: falls back to Firecrawl if configured
    - extracts internship-like links heuristically
    - upserts into `internships`
    """
    sources = load_sources()
    tracking = _load_tracking()
    inserted = 0
    sources_scraped = 0

    for src in sources:
        if inserted >= limit:
            break

        url = src.get("url")
        if not url:
            continue

        # Check if source should be scraped based on frequency
        if not _should_scrape_source(src, tracking):
            continue

        sources_scraped += 1
        logger.info(f"Scraping source ({sources_scraped}): {src.get('name')} [{src.get('scrape_frequency', 'daily')}]")

        proxy = get_next_proxy()
        typ = (src.get("type") or "http").lower()

        # Fetch with RemoteOK-specific handling
        html, allow_firecrawl = _fetch_with_remoteok_handling(url, typ, proxy)

        # Firecrawl fallback only if allowed (not RemoteOK)
        if not html and allow_firecrawl:
            fc = fetch_firecrawl(url)
            html = fc.content if fc else ""

        if not html:
            db.log_event(None, "scrape_failed", {"source_url": url})
            continue

        # Update tracking after successful fetch
        _update_tracking(url, tracking)

        items = extract_internships_from_html(html, source_url=url)
        for it in items:
            if inserted >= limit:
                break

            dup = check_duplicate(it)
            if dup.is_duplicate:
                continue

            row = db.upsert_internship(it)
            if row:
                db.log_event(row["id"], "discovered", {"source_url": url})
                inserted += 1

    logger.info(f"Discovery complete: {sources_scraped} sources scraped, {inserted} internships inserted")
    return inserted

