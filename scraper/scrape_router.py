from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

from core.jsonc import load_jsonc
from core.supabase_db import db
from pipeline.deduplicator import check_duplicate
from scraper.dynamic_fetcher import fetch_dynamic
from scraper.extractor import extract_internships_from_html
from scraper.firecrawl_fetcher import fetch_firecrawl
from scraper.http_fetcher import fetch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = PROJECT_ROOT / "data" / "job_source.json"

SCRAPE_BATCH_LIMIT = 50

# Import proxy pool from config
try:
    from scraper.proxy_config import PROXY_POOL
except ImportError:
    PROXY_POOL: list[str] = []

_proxy_cycle = itertools.cycle(PROXY_POOL) if PROXY_POOL else None


def get_next_proxy() -> str | None:
    if not PROXY_POOL or not _proxy_cycle:
        return None
    return next(_proxy_cycle)


def load_sources() -> list[dict[str, Any]]:
    data = load_jsonc(SOURCES_PATH)
    return list(data.get("sources") or [])


def discover_and_store(*, limit: int = SCRAPE_BATCH_LIMIT) -> int:
    """
    Phase 1 — discovery:
    - loads `data/job_source.json`
    - fetches HTML (http/dynamic)
    - falls back to Firecrawl if configured
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

        if typ == "dynamic":
            res = fetch_dynamic(url, proxy=proxy)
            tier = "tier2"
        else:
            res = fetch(url, proxy=proxy)
            tier = "tier1"

        html = res.text
        if not html:
            # Tier 3 fallback
            fc = fetch_firecrawl(url)
            html = fc.content if fc else ""
            tier = "tier3" if html else tier

        if not html:
            db.log_event(None, "scrape_failed", {"source_url": url, "tier": tier})
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
                db.log_event(row["id"], "discovered", {"source_url": url, "tier": tier})
                inserted += 1

    return inserted

