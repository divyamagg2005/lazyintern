from __future__ import annotations

import itertools
import random
import time
from pathlib import Path
from typing import Any

from core.jsonc import load_jsonc
from core.supabase_db import db
from pipeline.deduplicator import check_duplicate
from scraper.dynamic_fetcher import fetch_dynamic
from scraper.extractor import extract_internships_from_html
from scraper.firecrawl_fetcher import fetch_firecrawl
from scraper.http_fetcher import fetch, REMOTEOK_USER_AGENT

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = PROJECT_ROOT / "data" / "job_source.json"

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
    - fetches HTML (http/dynamic)
    - RemoteOK: custom User-Agent, 8-12s delay, 2 retries, NO Firecrawl fallback
    - Other sources: falls back to Firecrawl if configured
    - extracts internship-like links heuristically
    - upserts into `internships`
    """
    sources = load_sources()
    inserted = 0

    for src in sources:
        if inserted >= limit:
            break

        url = src.get("url")
        if not url:
            continue

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

    return inserted

