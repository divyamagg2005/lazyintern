"""
Website scraping module for email discovery fallback chain.

This module scrapes company websites for contact emails when all other
discovery methods (Hunter.io, pattern guessing, Snov.io) fail. It scrapes
specific pages in order and stops after finding the first valid email.

Environment Variables:
    None required - uses existing Scrapling library configuration
"""

from __future__ import annotations

import re
from scrapling.fetchers import Fetcher

from core.logger import logger
from pipeline.pattern_guesser import EmailDiscoveryResult


# Email regex pattern as specified in requirements
# Matches standard email format: localpart@domain.tld
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Pages to scrape in order of likelihood to contain contact emails
# /contact - Most likely to have contact information
# /about - Often contains company contact details
# /careers - May have recruiting contact information
SCRAPE_PATHS = ["/contact", "/about", "/careers"]


def scrape_domain_for_email(domain: str) -> EmailDiscoveryResult | None:
    """
    Scrape company website pages for email addresses.
    
    This function attempts to scrape URLs in order: /contact, /about, /careers.
    It stops scraping after finding the first valid email address. If a URL
    fails to load, it continues to the next URL without raising an exception.
    This is the final method in the fallback chain, executing only if all
    other methods (Hunter.io, pattern guessing, Snov.io) fail.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
    
    Returns:
        EmailDiscoveryResult with first valid email found (source="scraped",
        confidence=70) or None if no emails found on any page.
        
    Error Handling:
        - Page load failures: logs error, continues to next URL
        - Timeout errors: logs error, continues to next URL
        - Malformed HTML: handled gracefully, continues to next URL
        - Never raises exceptions (graceful degradation)
    
    Example:
        >>> result = scrape_domain_for_email("blitzenx.com")
        >>> if result:
        ...     print(f"Found: {result.email} from {result.source}")
        Found: contact@blitzenx.com from scraped
    """
    logger.info(f"[WebsiteScraper] Starting scrape for domain: {domain}")
    
    # Try each page in order until we find an email
    for path in SCRAPE_PATHS:
        url = f"https://{domain}{path}"
        logger.info(f"[WebsiteScraper] Attempting to scrape: {url}")
        
        try:
            # Use Scrapling's Fetcher.get() for HTTP requests
            # impersonate="chrome" helps avoid bot detection
            # timeout=10 prevents hanging on slow/unresponsive sites
            page = Fetcher.get(url, impersonate="chrome", timeout=10)
            
            # Extract HTML content from the page object
            # Different Scrapling versions may use different attributes
            html = getattr(page, "html_content", None)
            if html is None:
                body = getattr(page, "body", b"")
                html = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            
            # Convert to string if needed (handle different Scrapling response types)
            text = html.get() if hasattr(html, "get") and callable(html.get) else str(html)
            
            # Extract emails using regex
            # This finds all email-like patterns in the HTML
            emails = EMAIL_REGEX.findall(text)
            
            if emails:
                # Return the first email found (early exit optimization)
                first_email = emails[0]
                logger.info(
                    f"[WebsiteScraper] Found email on {url}: {first_email}"
                )
                return EmailDiscoveryResult(
                    email=first_email,
                    source="scraped",
                    confidence=70,  # Medium-high confidence (found on website but unverified)
                    recruiter_name=None
                )
            else:
                logger.info(f"[WebsiteScraper] No emails found on {url}")
        
        except Exception as e:
            # Log error and continue to next URL
            # This ensures one page failure doesn't prevent trying other pages
            logger.error(
                f"[WebsiteScraper] Error scraping {url}: {e.__class__.__name__}: {str(e)}"
            )
            continue
    
    # All URLs failed or returned no emails
    logger.info(f"[WebsiteScraper] No emails found for domain: {domain}")
    return None
