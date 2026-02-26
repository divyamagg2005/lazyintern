from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    text: str


DEFAULT_HEADERS = {
    "User-Agent": "LazyInternBot/1.0 (+contact: you@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _robots_allowed(url: str, user_agent: str = DEFAULT_HEADERS["User-Agent"]) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If robots.txt can't be fetched, default to allow for now (can tighten later).
        return True


def fetch(url: str, *, timeout: float = 20.0, delay_range: tuple[float, float] = (2.0, 3.0), proxy: str | None = None) -> FetchResult:
    if not _robots_allowed(url):
        return FetchResult(url=url, final_url=url, status_code=403, text="")

    time.sleep(random.uniform(*delay_range))
    proxies = proxy if proxy else None

    with httpx.Client(follow_redirects=True, timeout=timeout, headers=DEFAULT_HEADERS, proxies=proxies) as client:
        r = client.get(url)
        return FetchResult(
            url=url,
            final_url=str(r.url),
            status_code=r.status_code,
            text=r.text if r.status_code < 400 else "",
        )

