"""
Global domain-based rate limiter to prevent 403 errors from rapid same-domain requests.
Tracks last request timestamp per domain and enforces minimum gap between requests.
"""
from __future__ import annotations

import random
import time
from threading import Lock
from urllib.parse import urlparse

# Global state: domain -> last request timestamp
_domain_timestamps: dict[str, float] = {}
_lock = Lock()

# Minimum gap between same-domain requests (seconds)
MIN_DOMAIN_GAP = (6.0, 8.0)


def extract_domain(url: str) -> str:
    """Extract domain from URL (e.g., 'wellfound.com' from 'https://wellfound.com/jobs')"""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def wait_for_domain(url: str) -> None:
    """
    Check if enough time has passed since last request to this domain.
    If not, sleep until minimum gap has passed.
    """
    domain = extract_domain(url)
    if not domain:
        return

    with _lock:
        last_time = _domain_timestamps.get(domain, 0.0)
        now = time.time()
        gap = random.uniform(*MIN_DOMAIN_GAP)
        elapsed = now - last_time

        if elapsed < gap:
            sleep_time = gap - elapsed
            time.sleep(sleep_time)

        # Update timestamp after waiting
        _domain_timestamps[domain] = time.time()
