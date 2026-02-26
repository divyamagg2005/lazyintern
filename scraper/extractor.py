from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def _infer_company_from_url(url: str) -> str:
    host = urlparse(url).netloc
    host = host.replace("www.", "")
    return host.split(":")[0]


def extract_internships_from_html(html: str, *, source_url: str) -> list[dict[str, Any]]:
    """
    Heuristic extractor that works "okay" across many sites:
    - finds <a> tags whose href/text mention intern/internship
    - uses anchor text as role, host as company

    This is not perfect, but it's enough to test Phase 1 → DB insert end-to-end.
    """
    soup = BeautifulSoup(html, "lxml")
    company_guess = _infer_company_from_url(source_url)

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for a in soup.find_all("a"):
        href = a.get("href")
        text = (a.get_text(" ", strip=True) or "").strip()
        if not href:
            continue
        abs_url = urljoin(source_url, href)
        key = abs_url.lower()
        if key in seen:
            continue

        hay = f"{text} {href}".lower()
        if "intern" not in hay:
            continue

        seen.add(key)
        out.append(
            {
                "company": company_guess,
                "role": text[:200] if text else "Internship",
                "link": abs_url,
                "description": "",
                "location": None,
                "posted_date": None,
                "source_url": source_url,
                "status": "discovered",
            }
        )

        if len(out) >= 25:
            break

    return out

