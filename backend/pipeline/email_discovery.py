"""
Email discovery fallback chain orchestrator with domain-level caching.

This module coordinates the sequential execution of email discovery methods:
1. Check company_domains cache (avoid redundant API calls)
2. Hunter.io (existing primary method)
3. Pattern Guesser (5 common HR/recruiting patterns)
4. Snov.io API (secondary email discovery service)
5. Website Scraper (scrape contact/about/careers pages)

Each method executes only if previous methods returned no validated results.
This "short-circuit" behavior optimizes performance and minimizes API usage.

All discovered emails are validated using email_validator before being returned.
Results are cached at the domain level in the company_domains table to avoid
redundant API calls for the same domain.

Environment Variables:
    SNOV_CLIENT_ID: Snov.io OAuth client ID (optional, for Snov.io fallback)
    SNOV_CLIENT_SECRET: Snov.io OAuth client secret (optional, for Snov.io fallback)
"""

from __future__ import annotations

from core.logger import logger
from core.supabase_db import db, utcnow
from pipeline.pattern_guesser import EmailDiscoveryResult, generate_pattern_candidates
from pipeline.hunter_client import search_domain_for_email, HunterEmail
from pipeline.snov_client import search_snov_domain
from pipeline.website_scraper import scrape_domain_for_email
from pipeline.email_validator import validate_email


def discover_email_with_fallback(
    domain: str,
    company_name: str
) -> EmailDiscoveryResult | None:
    """
    Execute email discovery fallback chain with domain-level caching.
    
    This function orchestrates the sequential execution of email discovery methods,
    stopping immediately when any method returns a validated email. It checks the
    cache first and updates the cache after successful discovery.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
        company_name: Company name for logging purposes
    
    Returns:
        EmailDiscoveryResult with validated email or None if all methods fail
    
    Execution Order:
        1. Check company_domains cache
        2. Hunter.io (via hunter_client.search_domain_for_email)
        3. Pattern Guesser (validate all 5 candidates, select first valid)
        4. Snov.io API
        5. Website Scraper
    
    Caching:
        - Cache hit: Return cached email immediately
        - Cache miss: Execute fallback chain, cache result on success
        - Update company_domains.last_checked on every call
    
    Error Handling:
        - All exceptions are caught and logged
        - Errors in one method don't prevent subsequent methods from executing
        - Database cache failures don't block discovery
        - Returns None if all methods fail
    
    Example:
        >>> result = discover_email_with_fallback("blitzenx.com", "Blitzenx")
        >>> if result:
        ...     print(f"Found: {result.email} via {result.source}")
        Found: hr@blitzenx.com via pattern_guess
    """
    logger.info(
        f"[EmailDiscovery] Starting email discovery for domain: {domain} "
        f"(company: {company_name})"
    )
    
    # Step 1: Check company_domains cache
    try:
        cached = (
            db.client.table("company_domains")
            .select("*")
            .eq("domain", domain)
            .limit(1)
            .execute()
        )
        
        if cached.data:
            row = cached.data[0]
            emails = row.get("emails")
            
            # Check if we have cached emails
            if emails and isinstance(emails, list) and len(emails) > 0:
                first_email = emails[0]
                email_address = first_email.get("email")
                source = first_email.get("source", "hunter")
                confidence = first_email.get("confidence", 80)
                
                if email_address:
                    logger.info(
                        f"[EmailDiscovery] Cache hit for domain {domain}: "
                        f"{email_address} (source: {source})"
                    )
                    db.log_event(None, "email_discovery_cache_hit", {
                        "domain": domain,
                        "company_name": company_name,
                        "email": email_address,
                        "source": source
                    })
                    
                    # Update last_checked timestamp
                    try:
                        db.client.table("company_domains").update({
                            "last_checked": utcnow().isoformat()
                        }).eq("domain", domain).execute()
                    except Exception as e:
                        logger.warning(
                            f"[EmailDiscovery] Failed to update last_checked for {domain}: {e}"
                        )
                    
                    return EmailDiscoveryResult(
                        email=email_address,
                        source=source,
                        confidence=confidence,
                        recruiter_name=first_email.get("recruiter_name")
                    )
        
        logger.info(f"[EmailDiscovery] Cache miss for domain: {domain}")
        db.log_event(None, "email_discovery_cache_miss", {
            "domain": domain,
            "company_name": company_name
        })
        
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Error checking cache for domain {domain}: {e}. "
            "Continuing with discovery."
        )
    
    # Step 2: Try Hunter.io
    logger.info(f"[EmailDiscovery] Attempting Hunter.io for domain: {domain}")
    try:
        hunter_result = search_domain_for_email(domain)
        
        if hunter_result:
            logger.info(
                f"[EmailDiscovery] Hunter.io found email for {domain}: "
                f"{hunter_result.email} (confidence: {hunter_result.confidence})"
            )
            db.log_event(None, "email_discovery_hunter_success", {
                "domain": domain,
                "company_name": company_name,
                "email": hunter_result.email,
                "confidence": hunter_result.confidence
            })
            
            # Convert HunterEmail to EmailDiscoveryResult
            result = EmailDiscoveryResult(
                email=hunter_result.email,
                source=hunter_result.source,
                confidence=hunter_result.confidence,
                recruiter_name=hunter_result.recruiter_name
            )
            
            # Update cache
            _update_cache(domain, result)
            
            return result
        else:
            logger.info(f"[EmailDiscovery] Hunter.io returned no results for {domain}")
            db.log_event(None, "email_discovery_hunter_failure", {
                "domain": domain,
                "company_name": company_name
            })
    
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Error in Hunter.io for domain {domain}: {e}. "
            "Continuing to next method."
        )
        db.log_event(None, "email_discovery_error", {
            "domain": domain,
            "company_name": company_name,
            "method": "hunter",
            "error": str(e)
        })
    
    # Step 3: Try Pattern Guesser
    logger.info(f"[EmailDiscovery] Attempting Pattern Guesser for domain: {domain}")
    try:
        candidates = generate_pattern_candidates(domain)
        logger.info(
            f"[EmailDiscovery] Pattern Guesser generated {len(candidates)} candidates "
            f"for {domain}"
        )
        db.log_event(None, "email_discovery_pattern_generated", {
            "domain": domain,
            "company_name": company_name,
            "candidates": [c.email for c in candidates]
        })
        
        # Validate all candidates and select first valid one
        for candidate in candidates:
            logger.info(
                f"[EmailDiscovery] Validating pattern candidate: {candidate.email}"
            )
            
            try:
                validation = validate_email(candidate.email, candidate.confidence)
                
                if validation.valid:
                    logger.info(
                        f"[EmailDiscovery] Pattern candidate validated successfully: "
                        f"{candidate.email}"
                    )
                    db.log_event(None, "email_discovery_pattern_success", {
                        "domain": domain,
                        "company_name": company_name,
                        "email": candidate.email,
                        "pattern": candidate.email.split("@")[0]
                    })
                    
                    # Update cache
                    _update_cache(domain, candidate)
                    
                    return candidate
                else:
                    logger.info(
                        f"[EmailDiscovery] Pattern candidate validation failed: "
                        f"{candidate.email} (reason: {validation.reason})"
                    )
            
            except Exception as e:
                logger.error(
                    f"[EmailDiscovery] Error validating pattern candidate "
                    f"{candidate.email}: {e}. Trying next candidate."
                )
        
        # All patterns failed validation
        logger.info(
            f"[EmailDiscovery] All pattern candidates failed validation for {domain}"
        )
        db.log_event(None, "email_discovery_pattern_failure", {
            "domain": domain,
            "company_name": company_name
        })
    
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Error in Pattern Guesser for domain {domain}: {e}. "
            "Continuing to next method."
        )
        db.log_event(None, "email_discovery_error", {
            "domain": domain,
            "company_name": company_name,
            "method": "pattern_guesser",
            "error": str(e)
        })
    
    # Step 4: Try Snov.io
    logger.info(f"[EmailDiscovery] Attempting Snov.io for domain: {domain}")
    try:
        snov_result = search_snov_domain(domain)
        
        if snov_result:
            logger.info(
                f"[EmailDiscovery] Snov.io found email for {domain}: "
                f"{snov_result.email} (confidence: {snov_result.confidence})"
            )
            
            # Validate the Snov.io result
            validation = validate_email(snov_result.email, snov_result.confidence)
            
            if validation.valid:
                logger.info(
                    f"[EmailDiscovery] Snov.io email validated successfully: "
                    f"{snov_result.email}"
                )
                db.log_event(None, "email_discovery_snov_success", {
                    "domain": domain,
                    "company_name": company_name,
                    "email": snov_result.email,
                    "confidence": snov_result.confidence
                })
                
                # Update cache
                _update_cache(domain, snov_result)
                
                return snov_result
            else:
                logger.info(
                    f"[EmailDiscovery] Snov.io email validation failed: "
                    f"{snov_result.email} (reason: {validation.reason})"
                )
        else:
            logger.info(f"[EmailDiscovery] Snov.io returned no results for {domain}")
        
        db.log_event(None, "email_discovery_snov_failure", {
            "domain": domain,
            "company_name": company_name
        })
    
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Error in Snov.io for domain {domain}: {e}. "
            "Continuing to next method."
        )
        db.log_event(None, "email_discovery_error", {
            "domain": domain,
            "company_name": company_name,
            "method": "snov",
            "error": str(e)
        })
    
    # Step 5: Try Website Scraper
    logger.info(f"[EmailDiscovery] Attempting Website Scraper for domain: {domain}")
    try:
        scraper_result = scrape_domain_for_email(domain)
        
        if scraper_result:
            logger.info(
                f"[EmailDiscovery] Website Scraper found email for {domain}: "
                f"{scraper_result.email}"
            )
            
            # Validate the scraped email
            validation = validate_email(scraper_result.email, scraper_result.confidence)
            
            if validation.valid:
                logger.info(
                    f"[EmailDiscovery] Scraped email validated successfully: "
                    f"{scraper_result.email}"
                )
                db.log_event(None, "email_discovery_scraper_success", {
                    "domain": domain,
                    "company_name": company_name,
                    "email": scraper_result.email
                })
                
                # Update cache
                _update_cache(domain, scraper_result)
                
                return scraper_result
            else:
                logger.info(
                    f"[EmailDiscovery] Scraped email validation failed: "
                    f"{scraper_result.email} (reason: {validation.reason})"
                )
        else:
            logger.info(f"[EmailDiscovery] Website Scraper returned no results for {domain}")
        
        db.log_event(None, "email_discovery_scraper_failure", {
            "domain": domain,
            "company_name": company_name
        })
    
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Error in Website Scraper for domain {domain}: {e}. "
            "All methods exhausted."
        )
        db.log_event(None, "email_discovery_error", {
            "domain": domain,
            "company_name": company_name,
            "method": "scraper",
            "error": str(e)
        })
    
    # All methods failed
    logger.info(
        f"[EmailDiscovery] All discovery methods failed for domain: {domain}"
    )
    db.log_event(None, "email_discovery_complete_failure", {
        "domain": domain,
        "company_name": company_name
    })
    
    # Update last_checked even on failure
    try:
        db.client.table("company_domains").upsert({
            "domain": domain,
            "last_checked": utcnow().isoformat()
        }, on_conflict="domain").execute()
    except Exception as e:
        logger.warning(
            f"[EmailDiscovery] Failed to update last_checked for {domain}: {e}"
        )
    
    return None


def _update_cache(domain: str, result: EmailDiscoveryResult) -> None:
    """
    Update company_domains cache with discovered email.
    
    Args:
        domain: Company domain
        result: EmailDiscoveryResult to cache
    
    Error Handling:
        - Logs errors but doesn't raise exceptions
        - Cache update failures don't block the discovery pipeline
    """
    try:
        # Prepare email data for JSONB storage
        email_data = {
            "email": result.email,
            "source": result.source,
            "confidence": result.confidence
        }
        
        if result.recruiter_name:
            email_data["recruiter_name"] = result.recruiter_name
        
        # Upsert into company_domains
        db.client.table("company_domains").upsert({
            "domain": domain,
            "emails": [email_data],
            "last_checked": utcnow().isoformat()
        }, on_conflict="domain").execute()
        
        logger.info(
            f"[EmailDiscovery] Cache updated for domain {domain}: "
            f"{result.email} (source: {result.source})"
        )
    
    except Exception as e:
        logger.error(
            f"[EmailDiscovery] Failed to update cache for domain {domain}: {e}. "
            "Discovery result will not be cached."
        )
