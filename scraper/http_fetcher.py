from __future__ import annotations

import random
import time
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from scrapling.fetchers import Fetcher


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    text: str


DEFAULT_USER_AGENT = "LazyInternBot/1.0 (+contact: you@example.com)"


def _robots_allowed(url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True


def fetch(
    url: str,
    *,
    timeout: float = 20.0,
    delay_range: tuple[float, float] = (2.0, 3.0),
    proxy: str | None = None,
) -> FetchResult:
    """
    Tier 1 — Scrapling HTTP fetch.
    Uses Fetcher.get with Chrome impersonation.
    """
    if not _robots_allowed(url):
        return FetchResult(url=url, final_url=url, status_code=403, text="")

    time.sleep(random.uniform(*delay_range))

    try:
        page = Fetcher.get(url, impersonate="chrome", timeout=timeout)
        # Scrapling returns Selector/Response; html_content = full HTML, body = bytes
        html = getattr(page, "html_content", None)
        if html is None:
            body = getattr(page, "body", b"")
            html = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        # TextHandler has .get(); plain str does not
        text = html.get() if hasattr(html, "get") and callable(html.get) else str(html)

        status = getattr(page, "status_code", 200) or 200
        final_url = getattr(page, "url", None) or url

        return FetchResult(
            url=url,
            final_url=str(final_url),
            status_code=int(status),
            text=text if int(status) < 400 else "",
        )
    except Exception:
        return FetchResult(url=url, final_url=url, status_code=0, text="")
