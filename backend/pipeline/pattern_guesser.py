"""
Pattern-based email guessing module for the email discovery fallback chain.

This module generates common HR/recruiting email patterns for a domain without
making any external API calls. It's the first fallback method after Hunter.io.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmailDiscoveryResult:
    """
    Represents an email discovered through any discovery method.
    
    This dataclass is used throughout the email discovery fallback chain to
    standardize the format of discovered emails regardless of which method
    found them. The source field enables tracking and analysis of discovery
    method effectiveness.
    
    Attributes:
        email: The discovered email address (e.g., "hr@company.com")
        source: Discovery method that found this email. Valid values:
            - "hunter": Found via Hunter.io API
            - "pattern_guess": Generated using common email patterns
            - "snov": Found via Snov.io API
            - "scraped": Extracted from company website
        confidence: Reliability score from 0-100. Higher scores indicate
            greater confidence in the email's validity. Typical values:
            - Hunter.io: 80-100 (verified emails)
            - Pattern guess: 50 (unverified, common patterns)
            - Snov.io: varies based on their scoring
            - Scraped: 70 (found on website but unverified)
        recruiter_name: Optional recruiter name if available from the discovery
            method (typically only provided by Hunter.io)
    """
    email: str
    source: str
    confidence: int
    recruiter_name: str | None = None


def generate_pattern_candidates(domain: str) -> list[EmailDiscoveryResult]:
    """
    Generate 5 common email patterns for the domain.
    
    This function creates email candidates using standard HR/recruiting patterns
    without making any external API calls. All candidates are marked with
    source="pattern_guess" and confidence=50 (medium confidence since they're
    unverified guesses).
    
    The patterns are ordered by likelihood of being valid HR/recruiting contacts:
    1. hr@ - Most common HR department email
    2. careers@ - Common for recruiting/careers departments
    3. internships@ - Specific to internship programs
    4. hello@ - Generic contact email
    5. info@ - Generic information email
    
    Args:
        domain: Company domain (e.g., "blitzenx.com")
    
    Returns:
        List of 5 EmailDiscoveryResult objects in order:
        hr@, careers@, internships@, hello@, info@
        
        All candidates have:
        - source="pattern_guess"
        - confidence=50
        - recruiter_name=None
    
    Example:
        >>> candidates = generate_pattern_candidates("blitzenx.com")
        >>> len(candidates)
        5
        >>> candidates[0].email
        'hr@blitzenx.com'
        >>> candidates[0].source
        'pattern_guess'
        >>> candidates[0].confidence
        50
    """
    # Define patterns in priority order (most likely to least likely)
    patterns = ["hr", "careers", "internships", "hello", "info"]
    
    # Generate EmailDiscoveryResult for each pattern
    # All patterns get confidence=50 (medium) since they're unverified guesses
    return [
        EmailDiscoveryResult(
            email=f"{pattern}@{domain}",
            source="pattern_guess",
            confidence=50,
            recruiter_name=None
        )
        for pattern in patterns
    ]
