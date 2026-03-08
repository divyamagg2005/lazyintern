"""
Snov.io API integration module for email discovery fallback chain.

This module provides authentication and domain search functionality for Snov.io,
which is the second fallback method after pattern guessing in the email discovery chain.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from core.logger import logger
from pipeline.pattern_guesser import EmailDiscoveryResult


def _get_snov_access_token() -> str | None:
    """
    Authenticate with Snov.io OAuth endpoint and return access token.
    
    Reads SNOV_CLIENT_ID and SNOV_CLIENT_SECRET from environment variables,
    then authenticates with Snov.io OAuth endpoint to obtain an access token.
    This token is required for all subsequent Snov.io API calls.
    
    Returns:
        Access token string if authentication succeeds, None otherwise.
        
    Environment Variables:
        SNOV_CLIENT_ID: Snov.io OAuth client ID (obtain from Snov.io dashboard)
        SNOV_CLIENT_SECRET: Snov.io OAuth client secret (obtain from Snov.io dashboard)
        
    Error Handling:
        - Missing environment variables: logs warning, returns None
        - Authentication failure: logs error, returns None
        - Network errors: logs error, returns None
        - Never raises exceptions (graceful degradation)
        
    Example:
        >>> # With valid credentials in environment
        >>> token = _get_snov_access_token()
        >>> token is not None
        True
        >>> # With missing credentials
        >>> # Returns None and logs warning
    """
    # Check for required environment variables
    # If missing, skip Snov.io gracefully (fallback chain continues)
    client_id = os.getenv("SNOV_CLIENT_ID")
    client_secret = os.getenv("SNOV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.warning(
            "[Snov.io] Missing environment variables: SNOV_CLIENT_ID or SNOV_CLIENT_SECRET not set. "
            "Skipping Snov.io authentication."
        )
        return None
    
    try:
        # Snov.io OAuth endpoint for client credentials grant
        auth_url = "https://api.snov.io/v1/oauth/access_token"
        
        # Make authentication request with client credentials
        response = httpx.post(
            auth_url,
            json={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            },
            timeout=20.0  # 20 second timeout for authentication
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract access token from response
        access_token = data.get("access_token")
        
        if not access_token:
            logger.error("[Snov.io] Authentication response missing access_token field")
            return None
        
        logger.info("[Snov.io] Successfully authenticated and obtained access token")
        return access_token
        
    except httpx.HTTPStatusError as e:
        # HTTP error (4xx, 5xx) - log and return None
        logger.error(
            f"[Snov.io] Authentication failed with HTTP {e.response.status_code}: {e.response.text}"
        )
        return None
        
    except httpx.RequestError as e:
        # Network error (timeout, connection refused, etc.) - log and return None
        logger.error(f"[Snov.io] Network error during authentication: {e}")
        return None
        
    except Exception as e:
        # Unexpected error - log and return None (never crash the pipeline)
        logger.error(f"[Snov.io] Unexpected error during authentication: {e}")
        return None


def search_snov_domain(domain: str) -> EmailDiscoveryResult | None:
    """
    Search Snov.io for emails associated with a domain.
    
    Authenticates with Snov.io, then calls the domain search endpoint to find
    emails associated with the given domain. Returns the email with the highest
    confidence score from the results. This is the third method in the fallback
    chain, executing only if Hunter.io and pattern guessing both fail.
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
        
    Returns:
        EmailDiscoveryResult with highest confidence email and source="snov",
        or None if no emails found or if any error occurs.
        
    API Endpoint:
        POST https://api.snov.io/v2/domain-emails-with-info
        
    Error Handling:
        - Authentication failure: logs error, returns None
        - API call failure: logs error, returns None
        - No results: logs info, returns None
        - Network errors: logs error, returns None
        - Never raises exceptions (graceful degradation)
        
    Example:
        >>> result = search_snov_domain("blitzenx.com")
        >>> if result:
        ...     print(f"Found: {result.email} (confidence: {result.confidence})")
        Found: contact@blitzenx.com (confidence: 85)
    """
    # First, authenticate to get access token
    # If authentication fails, this returns None and we skip Snov.io gracefully
    access_token = _get_snov_access_token()
    
    if not access_token:
        logger.warning(f"[Snov.io] Cannot search domain {domain}: authentication failed")
        return None
    
    try:
        # Snov.io domain search endpoint
        search_url = "https://api.snov.io/v2/domain-emails-with-info"
        
        # Make domain search request with Bearer token authentication
        response = httpx.post(
            search_url,
            json={
                "domain": domain
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=20.0  # 20 second timeout for API call
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract emails from response
        # Snov.io returns emails in various formats, typically in a "emails" or "data" field
        emails = data.get("emails") or data.get("data") or []
        
        if not emails:
            logger.info(f"[Snov.io] No emails found for domain: {domain}")
            return None
        
        # Select email with highest confidence score
        # This ensures we return the most reliable email from Snov.io's results
        best_email = None
        highest_confidence = -1
        
        for email_data in emails:
            # Extract email address (field name varies in Snov.io responses)
            email_address = email_data.get("email") or email_data.get("value")
            # Extract confidence score (field name varies in Snov.io responses)
            confidence = email_data.get("confidence") or email_data.get("score") or 0
            
            if not email_address:
                continue
            
            # Convert confidence to integer if it's a string or float
            try:
                confidence = int(confidence)
            except (ValueError, TypeError):
                confidence = 0
            
            # Track the email with highest confidence
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_email = email_address
        
        if not best_email:
            logger.info(f"[Snov.io] No valid emails found for domain: {domain}")
            return None
        
        logger.info(
            f"[Snov.io] Found email for domain {domain}: {best_email} "
            f"(confidence: {highest_confidence})"
        )
        
        # Return the best email with Snov.io's confidence score
        return EmailDiscoveryResult(
            email=best_email,
            source="snov",
            confidence=highest_confidence,
            recruiter_name=None
        )
        
    except httpx.HTTPStatusError as e:
        # HTTP error (4xx, 5xx) - log and return None
        logger.error(
            f"[Snov.io] Domain search failed for {domain} with HTTP {e.response.status_code}: "
            f"{e.response.text}"
        )
        return None
        
    except httpx.RequestError as e:
        # Network error (timeout, connection refused, etc.) - log and return None
        logger.error(f"[Snov.io] Network error during domain search for {domain}: {e}")
        return None
        
    except Exception as e:
        # Unexpected error - log and return None (never crash the pipeline)
        logger.error(f"[Snov.io] Unexpected error during domain search for {domain}: {e}")
        return None
