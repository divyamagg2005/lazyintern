from __future__ import annotations

from scrapling.fetchers import DynamicFetcher

from scraper.http_fetcher import FetchResult
from scraper.domain_rate_limiter import wait_for_domain


def fetch_dynamic(url: str, *, proxy: str | None = None) -> FetchResult:
    """
    Tier 2 — Scrapling DynamicFetcher (Playwright).
    Uses headless browser for JS-rendered pages.
    Includes global domain rate limiting to prevent 403 errors.
    """
    # Global domain rate limiting (6-8 second gap between same-domain requests)
    wait_for_domain(url)

    try:
        page = DynamicFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
        )
        html = getattr(page, "html_content", None)
        if html is None:
            body = getattr(page, "body", b"")
            html = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
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
