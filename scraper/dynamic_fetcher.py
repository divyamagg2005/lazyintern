from __future__ import annotations

from scraper.http_fetcher import FetchResult, fetch


def fetch_dynamic(url: str, *, proxy: str | None = None) -> FetchResult:
    """
    Placeholder for Playwright/Scrapling dynamic fetch.
    For now we fall back to plain HTTP fetch so the pipeline is runnable.
    """
    return fetch(url, proxy=proxy)

