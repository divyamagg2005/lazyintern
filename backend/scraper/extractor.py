from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "").lower()


def _text(el: Any, selector: str) -> str:
    node = el.select_one(selector) if el else None
    return node.get_text(" ", strip=True) if node else ""


def _href(el: Any, selector: str, *, base_url: str) -> str:
    node = el.select_one(selector) if el else None
    href = node.get("href") if node else None
    return urljoin(base_url, href) if href else ""


def _extract_internshala(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    # Internshala repeating card container.
    cards = soup.select(".individual_internship")
    out: list[dict[str, Any]] = []
    for card in cards:
        company = (
            _text(card, ".company_name")
            or _text(card, ".company-name")
            or _text(card, ".company")
        )
        role = _text(card, ".profile") or _text(card, ".job-title")
        link = _href(card, "a.view_detail_button", base_url=source_url) or _href(
            card, "a[href*='/internship/'], a[href*='/internships/']", base_url=source_url
        )
        location = _text(card, ".location_link")
        if not link or not role:
            continue
        out.append(
            {
                "company": company or "Unknown Company",
                "role": role[:200],
                "link": link,
                "description": card.get_text(" ", strip=True)[:2000],
                "location": location or None,
                "posted_date": None,
                "source_url": source_url,
                "status": "discovered",
            }
        )
    return out


def _extract_wellfound(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    cards = soup.select('[data-test="StartupResult"]')
    out: list[dict[str, Any]] = []
    for card in cards:
        company = (
            _text(card, '[data-test="StartupName"]')
            or _text(card, '[data-test="company-name"]')
            or _text(card, "h2, h3")
        )
        role = (
            _text(card, '[data-test="JobTitle"]')
            or _text(card, '[data-test="job-title"]')
            or _text(card, "a")
        )
        link = _href(
            card,
            'a[href*="/jobs/"], a[href*="/job/"]',
            base_url=source_url,
        )
        location = _text(card, '[data-test="JobLocation"], [data-test="location"]')
        if not link or not role:
            continue
        out.append(
            {
                "company": company or "Unknown Company",
                "role": role[:200],
                "link": link,
                "description": card.get_text(" ", strip=True)[:2000],
                "location": location or None,
                "posted_date": None,
                "source_url": source_url,
                "status": "discovered",
            }
        )
    return out


def _extract_remoteok(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    cards = soup.select("tr.job")
    out: list[dict[str, Any]] = []
    for card in cards:
        company = _text(card, "h3") or _text(card, ".companyLink")
        role = _text(card, "h2") or _text(card, ".position")
        link = _href(card, "a.preventLink", base_url=source_url) or _href(
            card, 'a[href*="/remote-jobs/"]', base_url=source_url
        )
        location = _text(card, ".location")
        if not link or not role:
            continue
        out.append(
            {
                "company": company or "Unknown Company",
                "role": role[:200],
                "link": link,
                "description": card.get_text(" ", strip=True)[:2000],
                "location": location or None,
                "posted_date": None,
                "source_url": source_url,
                "status": "discovered",
            }
        )
    return out


def _extract_generic(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    # Fallback for unsupported domains: stricter than raw <a> scan.
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    host = _domain(source_url)
    for a in soup.select("a[href*='intern']"):
        href = a.get("href")
        text = a.get_text(" ", strip=True)
        if not href or not text:
            continue
        link = urljoin(source_url, href)
        if link.lower() in seen:
            continue
        seen.add(link.lower())
        out.append(
            {
                "company": host,
                "role": text[:200],
                "link": link,
                "description": "",
                "location": None,
                "posted_date": None,
                "source_url": source_url,
                "status": "discovered",
            }
        )
        if len(out) >= 20:
            break
    return out


def extract_internships_from_html(html: str, *, source_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    host = _domain(source_url)

    if "internshala.com" in host:
        items = _extract_internshala(soup, source_url)
    elif "wellfound.com" in host:
        items = _extract_wellfound(soup, source_url)
    elif "remoteok.com" in host:
        items = _extract_remoteok(soup, source_url)
    else:
        items = _extract_generic(soup, source_url)

    return items

