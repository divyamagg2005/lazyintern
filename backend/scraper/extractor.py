from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "").lower()


def _extract_company_from_url(url: str) -> str | None:
    """
    Extract company name from job URL patterns like:
    - "ai-ml-intern-at-blitzenx-4260593901" → "Blitzenx"
    - "machine-learning-intern-at-innovexis-4375534131" → "Innovexis"
    """
    import re
    
    # Pattern: text-at-COMPANY-numbers
    match = re.search(r'-at-([a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)-\d+', url)
    if match:
        company_slug = match.group(1)
        # Convert slug to title case (e.g., "blitzenx" → "Blitzenx")
        return company_slug.replace('-', ' ').title()
    
    # Pattern: /company/COMPANY/ or /companies/COMPANY/
    match = re.search(r'/compan(?:y|ies)/([a-zA-Z0-9-]+)', url, re.IGNORECASE)
    if match:
        company_slug = match.group(1)
        return company_slug.replace('-', ' ').title()
    
    return None


def _extract_company_from_content(soup: BeautifulSoup, card: Any = None) -> str | None:
    """
    Extract company name from page content.
    Tries multiple common selectors for company names.
    """
    target = card if card else soup
    
    # Common company name selectors
    selectors = [
        '.company-name',
        '.company_name',
        '.companyName',
        '[data-company]',
        '[class*="company"]',
        '.employer',
        '.organization',
        'span[class*="Company"]',
        'div[class*="company"]',
        'a[class*="company"]',
    ]
    
    for selector in selectors:
        elem = target.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            if text and len(text) > 2 and len(text) < 100:
                return text
    
    return None


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


def _extract_linkedin(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    """
    LinkedIn job listings extractor.
    Extracts actual company names from job cards, not "linkedin.com".
    """
    cards = soup.select('.job-search-card, .jobs-search__results-list > li, [data-job-id]')
    out: list[dict[str, Any]] = []
    
    for card in cards:
        # Company name selectors for LinkedIn
        company = (
            _text(card, '.job-search-card__subtitle')
            or _text(card, '.base-search-card__subtitle')
            or _text(card, 'h4')
            or _text(card, '[class*="company"]')
        )
        
        # Role/title selectors
        role = (
            _text(card, '.job-search-card__title')
            or _text(card, '.base-search-card__title')
            or _text(card, 'h3')
            or _text(card, '[class*="title"]')
        )
        
        # Link selectors
        link = _href(
            card,
            'a.base-card__full-link, a[href*="/jobs/view/"]',
            base_url=source_url,
        )
        
        # Location
        location = _text(card, '.job-search-card__location, [class*="location"]')
        
        # If company not found in selectors, try URL extraction
        if not company or company.lower() == 'linkedin':
            company = _extract_company_from_url(link) if link else None
        
        # If still no company, try content extraction
        if not company:
            company = _extract_company_from_content(soup, card)
        
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
    """
    Fallback for unsupported domains.
    Tries to extract company name from:
    1. Page content (company name selectors)
    2. Job URL pattern (e.g., "-at-company-name-")
    3. Falls back to domain only if nothing else works
    """
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
        
        # Try to find the parent card/container
        card = a.find_parent(['div', 'article', 'li', 'tr'])
        
        # Extract company name (priority order):
        # 1. From page content near the link
        company = _extract_company_from_content(soup, card)
        
        # 2. From URL pattern
        if not company:
            company = _extract_company_from_url(link)
        
        # 3. Fallback to domain
        if not company:
            company = host
        
        out.append(
            {
                "company": company,
                "role": text[:200],
                "link": link,
                "description": card.get_text(" ", strip=True)[:2000] if card else "",
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
    elif "linkedin.com" in host:
        items = _extract_linkedin(soup, source_url)
    else:
        items = _extract_generic(soup, source_url)

    return items

