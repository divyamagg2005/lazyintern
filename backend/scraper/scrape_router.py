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


def _should_scrape_source(source: dict[str, Any], tracking: dict[str, Any]) -> tuple[bool, str]:
    """
    Check if source should be scraped based on day_rotation and scrape_frequency.
    
    Rules:
    - day_rotation: 1, 2, or 3 - only scrape on matching day of 3-day cycle
    - daily: scrape every cycle (if day_rotation matches)
    - weekly: only if last_scraped_at > 7 days ago
    - monthly: only if last_scraped_at > 30 days ago
    
    Returns:
        (should_scrape: bool, skip_reason: str)
    """
    from datetime import date
    
    url = source.get("url", "")
    source_name = source.get("name", url)
    frequency = source.get("scrape_frequency", "daily").lower()
    
    # Check day rotation first (if specified)
    day_rotation = source.get("day_rotation")
    if day_rotation:
        # Calculate current day of 3-day cycle (1, 2, or 3)
        day_of_cycle = (date.today().toordinal() % 3) + 1
        if day_rotation != day_of_cycle:
            # Not this source's day
            return False, f"day_rotation={day_rotation}, today={day_of_cycle}"
    
    # Check frequency-based rules
    if frequency == "daily":
        return True, ""
    
    # Check last scraped timestamp for weekly/monthly
    source_data = tracking.get("sources", {}).get(url, {})
    last_scraped = source_data.get("last_scraped_at")
    
    if not last_scraped:
        # Never scraped before, scrape now
        return True, ""
    
    try:
        last_scraped_dt = datetime.fromisoformat(last_scraped.replace("Z", "+00:00"))
        now = utcnow()
        days_since_scrape = (now - last_scraped_dt).days
        
        if frequency == "weekly":
            should_scrape = days_since_scrape >= 7
            if not should_scrape:
                return False, f"weekly, last scraped {days_since_scrape} days ago"
            return True, ""
        
        elif frequency == "monthly":
            should_scrape = days_since_scrape >= 30
            if not should_scrape:
                return False, f"monthly, last scraped {days_since_scrape} days ago"
            return True, ""
        
        # Unknown frequency, default to daily
        return True, ""
        
    except Exception as e:
        logger.warning(f"Error checking scrape frequency for {url}: {e}")
        return True, ""  # Scrape on error to be safe


def _update_tracking(url: str, tracking: dict[str, Any]) -> None:
    """Update last_scraped_at timestamp for a source."""
    if "sources" not in tracking:
        tracking["sources"] = {}
    
    tracking["sources"][url] = {
        "last_scraped_at": utcnow().isoformat(),
        "last_scraped_success": True
    }
    _save_tracking(tracking)


def _is_linkedin_url(url: str) -> bool:
    """Check if URL is from LinkedIn"""
    return "linkedin.com" in url.lower()


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
    import threading
    from contextlib import contextmanager
    from datetime import date
    
    @contextmanager
    def timeout_context(seconds: int):
        """Cross-platform timeout context manager using threading"""
        result = {"completed": False, "exception": None, "html": None, "allow_firecrawl": False}
        
        def target(result_dict):
            try:
                # This will be replaced by the actual scraping code
                result_dict["completed"] = True
            except Exception as e:
                result_dict["exception"] = e
        
        # We'll handle timeout at the call site instead
        yield result
    
    sources = load_sources()
    tracking = _load_tracking()
    inserted = 0
    sources_scraped = 0
    sources_skipped = 0
    PER_SOURCE_TIMEOUT = 300  # Maximum 5 minutes per source
    
    # Calculate and display current day of rotation cycle
    day_of_cycle = (date.today().toordinal() % 3) + 1
    logger.info("=" * 80)
    logger.info(f"🔄 3-DAY ROTATION: Today is DAY {day_of_cycle} of the cycle")
    logger.info(f"📅 Date: {date.today()}")
    logger.info("=" * 80)
    
    # Separate LinkedIn sources for randomization
    linkedin_sources = [s for s in sources if _is_linkedin_url(s.get("url", ""))]
    other_sources = [s for s in sources if not _is_linkedin_url(s.get("url", ""))]
    
    # Randomize LinkedIn sources to avoid predictable patterns
    random.shuffle(linkedin_sources)
    
    # Combine: other sources first, then randomized LinkedIn sources
    sources = other_sources + linkedin_sources

    for src in sources:
        if inserted >= limit:
            break

        url = src.get("url")
        if not url:
            continue

        # Check if source should be scraped based on frequency and rotation
        should_scrape, skip_reason = _should_scrape_source(src, tracking)
        if not should_scrape:
            source_name = src.get('name', url)
            logger.info(f"⏭️  Skipped {source_name} ({skip_reason})")
            sources_skipped += 1
            continue

        sources_scraped += 1
        source_name = src.get('name', url)
        logger.info(f"🌐 Scraping source ({sources_scraped}): {source_name} [{src.get('scrape_frequency', 'daily')}]")
        
        # LinkedIn-specific delay: 8-15 seconds before scraping
        if _is_linkedin_url(url):
            linkedin_delay = random.uniform(8.0, 15.0)
            logger.info(f"⏳ LinkedIn delay: {linkedin_delay:.1f}s")
            time.sleep(linkedin_delay)

        try:
            # Use threading for cross-platform timeout
            import threading
            result = {"html": None, "allow_firecrawl": False, "exception": None}
            
            def scrape_with_timeout():
                try:
                    proxy = get_next_proxy()
                    typ = (src.get("type") or "http").lower()
                    html, allow_firecrawl = _fetch_with_remoteok_handling(url, typ, proxy)
                    result["html"] = html
                    result["allow_firecrawl"] = allow_firecrawl
                except Exception as e:
                    result["exception"] = e
            
            thread = threading.Thread(target=scrape_with_timeout, daemon=True)
            thread.start()
            thread.join(timeout=PER_SOURCE_TIMEOUT)
            
            if thread.is_alive():
                # Timeout occurred
                logger.warning(f"⏱️ Timeout scraping {source_name} (exceeded {PER_SOURCE_TIMEOUT}s)")
                db.log_event(None, "scrape_timeout", {"source_url": url, "source_name": source_name, "timeout_seconds": PER_SOURCE_TIMEOUT})
                continue
            
            if result["exception"]:
                raise result["exception"]
            
            html = result["html"]
            allow_firecrawl = result["allow_firecrawl"]

            # Firecrawl fallback only if allowed (not RemoteOK)
            if not html and allow_firecrawl:
                fc = fetch_firecrawl(url)
                html = fc.content if fc else ""

            if not html:
                db.log_event(None, "scrape_failed", {"source_url": url, "source_name": source_name})
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
        
        except Exception as e:
            logger.error(f"❌ Error scraping {source_name}: {e}")
            db.log_event(None, "scrape_error", {"source_url": url, "source_name": source_name, "error": str(e)})
            continue

    logger.info("=" * 80)
    logger.info(f"✅ DISCOVERY COMPLETE: {sources_scraped} sources scraped, {sources_skipped} skipped, {inserted} internships inserted")
    logger.info("=" * 80)
    return inserted

