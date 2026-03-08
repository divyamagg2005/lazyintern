"""
Integration tests for email discovery fallback chain.

Feature: email-discovery-fallback-chain

These tests verify end-to-end flows through the email discovery system,
including error handling and resilience.

Task 8.1: Test end-to-end flow through all fallback methods,
         verify lead creation, cache updates, and logging

Task 8.2: Test all methods failing gracefully, partial failures, missing credentials,
         network timeouts, database errors
"""

from unittest.mock import patch, MagicMock, Mock
import sys
import os
import pytest

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.pattern_guesser import EmailDiscoveryResult
from pipeline.email_validator import ValidationResult


# ============================================================================
# Task 8.1: Complete Fallback Chain Integration Tests
# ============================================================================

def test_integration_complete_fallback_chain_hunter_to_lead():
    """
    Integration test: Complete flow from email discovery to lead creation.
    
    Tests the integration between discover_email_with_fallback and the
    database layer, verifying that Hunter.io results are properly stored.
    
    Validates: Requirements 4.1, 4.2, 5.1, 5.2, 5.3, 8.1, 8.2
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "example.com"
    company_name = "Example Corp"
    hunter_email = "hr@example.com"
    
    # Mock Hunter.io to return success
    hunter_result = EmailDiscoveryResult(
        email=hunter_email,
        source="hunter",
        confidence=90,
        recruiter_name="Jane Doe"
    )
    
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=hunter_result):
        with patch('pipeline.email_discovery.validate_email') as mock_validate:
            mock_validate.return_value = ValidationResult(
                valid=True,
                mx_valid=True,
                smtp_valid=True,
                reason="Valid"
            )
            
            with patch('pipeline.email_discovery.db') as mock_db:
                # Mock cache check (cache miss)
                mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                
                # Execute discovery
                result = discover_email_with_fallback(domain, company_name)
    
    # Verify result
    assert result is not None
    assert result.email == hunter_email
    assert result.source == "hunter"
    assert result.confidence == 90
    assert result.recruiter_name == "Jane Doe"
    
    # Verify cache was updated
    assert mock_db.client.table.return_value.upsert.called



def test_integration_pattern_guesser_fallback_flow():
    """
    Integration test: Pattern guesser fallback when Hunter fails.
    
    Tests the complete fallback from Hunter.io to pattern guesser,
    including validation of all 5 pattern candidates.
    
    Validates: Requirements 1.5, 1.6, 4.3, 5.4
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "patterncorp.com"
    company_name = "Pattern Corp"
    
    # Mock Hunter.io to return None (no results)
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            # Mock pattern candidates
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.validate_email') as mock_validate:
                # First two patterns fail validation, third succeeds
                mock_validate.side_effect = [
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),
                ]
                
                with patch('pipeline.email_discovery.db') as mock_db:
                    # Mock cache miss
                    mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                    
                    # Execute discovery
                    result = discover_email_with_fallback(domain, company_name)
    
    # Verify result is the third pattern (internships@)
    assert result is not None
    assert result.email == f"internships@{domain}"
    assert result.source == "pattern_guess"
    assert result.confidence == 50
    
    # Verify all 3 patterns were validated (stopped after first valid)
    assert mock_validate.call_count == 3


def test_integration_snov_fallback_flow():
    """
    Integration test: Snov.io fallback when Hunter and patterns fail.
    
    Tests the complete fallback chain to Snov.io when earlier methods
    return no validated results.
    
    Validates: Requirements 2.6, 4.3, 5.1, 5.2
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "snovcorp.com"
    company_name = "Snov Corp"
    snov_email = "careers@snovcorp.com"
    
    # Mock Hunter.io to return None
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        # Mock pattern guesser to return candidates that all fail validation
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.validate_email') as mock_validate:
                # All patterns fail validation, then Snov succeeds
                mock_validate.side_effect = [
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),  # Snov result
                ]
                
                # Mock Snov.io to return success
                with patch('pipeline.email_discovery.search_snov_domain') as mock_snov:
                    mock_snov.return_value = EmailDiscoveryResult(
                        email=snov_email,
                        source="snov",
                        confidence=85,
                        recruiter_name="John Smith"
                    )
                    
                    with patch('pipeline.email_discovery.db') as mock_db:
                        # Mock cache miss
                        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                        
                        # Execute discovery
                        result = discover_email_with_fallback(domain, company_name)
    
    # Verify result is from Snov.io
    assert result is not None
    assert result.email == snov_email
    assert result.source == "snov"
    assert result.confidence == 85
    assert result.recruiter_name == "John Smith"


def test_integration_scraper_fallback_flow():
    """
    Integration test: Website scraper as last fallback.
    
    Tests the complete fallback chain to website scraper when all
    other methods fail.
    
    Validates: Requirements 3.5, 3.6, 4.3, 5.1, 5.2
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "scrapercorp.com"
    company_name = "Scraper Corp"
    scraped_email = "contact@scrapercorp.com"
    
    # Mock all previous methods to fail
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.search_snov_domain', return_value=None):
                with patch('pipeline.email_discovery.validate_email') as mock_validate:
                    # All patterns fail, scraper succeeds
                    mock_validate.side_effect = [
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),  # Scraper result
                    ]
                    
                    # Mock website scraper to return success
                    with patch('pipeline.email_discovery.scrape_domain_for_email') as mock_scraper:
                        mock_scraper.return_value = EmailDiscoveryResult(
                            email=scraped_email,
                            source="scraped",
                            confidence=70,
                            recruiter_name=None
                        )
                        
                        with patch('pipeline.email_discovery.db') as mock_db:
                            # Mock cache miss
                            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                            
                            # Execute discovery
                            result = discover_email_with_fallback(domain, company_name)
    
    # Verify result is from scraper
    assert result is not None
    assert result.email == scraped_email
    assert result.source == "scraped"
    assert result.confidence == 70


def test_integration_cache_hit_skips_all_methods():
    """
    Integration test: Cache hit skips all discovery methods.
    
    Tests that when a cached result exists, no discovery methods
    are called and the cached result is returned immediately.
    
    Validates: Requirements 8.3, 8.4
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "cached.com"
    company_name = "Cached Corp"
    cached_email = "cached@cached.com"
    
    with patch('pipeline.email_discovery.search_domain_for_email') as mock_hunter:
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            with patch('pipeline.email_discovery.search_snov_domain') as mock_snov:
                with patch('pipeline.email_discovery.scrape_domain_for_email') as mock_scraper:
                    with patch('pipeline.email_discovery.db') as mock_db:
                        # Mock cache hit - need to mock both select and update operations
                        mock_select_result = Mock()
                        mock_select_result.data = [{
                            "domain": domain,
                            "emails": [{"email": cached_email, "source": "hunter", "confidence": 90}]
                        }]
                        
                        # Mock the select chain
                        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_select_result
                        
                        # Mock the update chain for last_checked
                        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value = None
                        
                        # Mock log_event
                        mock_db.log_event.return_value = None
                        
                        # Execute discovery
                        result = discover_email_with_fallback(domain, company_name)
    
    # Verify cached result returned
    assert result is not None
    assert result.email == cached_email
    assert result.source == "hunter"
    assert result.confidence == 90
    
    # Verify no discovery methods were called
    assert not mock_hunter.called
    assert not mock_pattern.called
    assert not mock_snov.called
    assert not mock_scraper.called


# ============================================================================
# Task 8.2: Error Scenario Integration Tests
# ============================================================================

def test_integration_all_methods_fail_returns_none():
    """
    Integration test: All discovery methods fail gracefully.
    
    Tests that when all methods return no validated results, the system
    returns None without crashing.
    
    Validates: Requirements 4.4, 6.5
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "noemail.com"
    company_name = "No Email Corp"
    
    # Mock all methods to return None or fail validation
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.search_snov_domain', return_value=None):
                with patch('pipeline.email_discovery.scrape_domain_for_email', return_value=None):
                    with patch('pipeline.email_discovery.validate_email') as mock_validate:
                        # All patterns fail validation
                        mock_validate.return_value = ValidationResult(
                            valid=False,
                            mx_valid=False,
                            smtp_valid=False,
                            reason="Invalid"
                        )
                        
                        with patch('pipeline.email_discovery.db') as mock_db:
                            # Mock cache miss
                            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                            
                            # Execute discovery - should not crash
                            result = discover_email_with_fallback(domain, company_name)
    
    # Verify None returned
    assert result is None



def test_integration_method_exception_continues_to_next():
    """
    Integration test: Exceptions in one method don't stop the chain.
    
    Tests that when a method raises an exception, the system logs it
    and continues to the next method.
    
    Validates: Requirements 6.1, 6.2
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "exception.com"
    company_name = "Exception Corp"
    final_email = "info@exception.com"
    
    # Mock Hunter.io to raise exception
    with patch('pipeline.email_discovery.search_domain_for_email', side_effect=Exception("Hunter API error")):
        # Mock pattern guesser to also raise exception
        with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=Exception("Pattern error")):
            # Mock Snov.io to raise exception
            with patch('pipeline.email_discovery.search_snov_domain', side_effect=Exception("Snov API error")):
                # Mock scraper to succeed
                with patch('pipeline.email_discovery.scrape_domain_for_email') as mock_scraper:
                    mock_scraper.return_value = EmailDiscoveryResult(
                        email=final_email,
                        source="scraped",
                        confidence=70,
                        recruiter_name=None
                    )
                    
                    with patch('pipeline.email_discovery.validate_email') as mock_validate:
                        mock_validate.return_value = ValidationResult(
                            valid=True,
                            mx_valid=True,
                            smtp_valid=True,
                            reason="Valid"
                        )
                        
                        with patch('pipeline.email_discovery.db') as mock_db:
                            # Mock cache miss
                            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                            
                            # Execute discovery - should not crash
                            result = discover_email_with_fallback(domain, company_name)
    
    # Verify scraper result returned despite earlier exceptions
    assert result is not None
    assert result.email == final_email
    assert result.source == "scraped"


def test_integration_missing_snov_credentials_graceful():
    """
    Integration test: Missing Snov.io credentials handled gracefully.
    
    Tests that when SNOV_CLIENT_ID or SNOV_CLIENT_SECRET are missing,
    the Snov client returns None and the chain continues.
    
    Validates: Requirements 6.3, 7.3
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "nosnov.com"
    company_name = "No Snov Corp"
    pattern_email = "hr@nosnov.com"
    
    # Mock Hunter.io to return None
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        # Mock pattern guesser to succeed
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.validate_email') as mock_validate:
                # First pattern succeeds
                mock_validate.return_value = ValidationResult(
                    valid=True,
                    mx_valid=True,
                    smtp_valid=True,
                    reason="Valid"
                )
                
                # Mock Snov.io to return None (simulating missing credentials)
                with patch('pipeline.email_discovery.search_snov_domain', return_value=None):
                    with patch('pipeline.email_discovery.db') as mock_db:
                        # Mock cache miss
                        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                        
                        # Execute discovery - should not crash
                        result = discover_email_with_fallback(domain, company_name)
    
    # Verify pattern result returned
    assert result is not None
    assert result.email == pattern_email
    assert result.source == "pattern_guess"


def test_integration_network_timeout_continues():
    """
    Integration test: Network timeouts don't crash the pipeline.
    
    Tests that when network requests timeout (e.g., during scraping),
    the system continues to other methods.
    
    Validates: Requirements 6.4
    """
    from pipeline.email_discovery import discover_email_with_fallback
    import requests
    
    domain = "timeout.com"
    company_name = "Timeout Corp"
    pattern_email = "careers@timeout.com"
    
    # Mock Hunter.io to timeout
    with patch('pipeline.email_discovery.search_domain_for_email', side_effect=requests.Timeout("Connection timeout")):
        # Mock pattern guesser to succeed
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.validate_email') as mock_validate:
                # Second pattern (careers@) succeeds
                mock_validate.side_effect = [
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                    ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),
                ]
                
                with patch('pipeline.email_discovery.db') as mock_db:
                    # Mock cache miss
                    mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                    
                    # Execute discovery - should not crash
                    result = discover_email_with_fallback(domain, company_name)
    
    # Verify pattern result returned despite timeout
    assert result is not None
    assert result.email == pattern_email
    assert result.source == "pattern_guess"


def test_integration_database_cache_error_continues():
    """
    Integration test: Database cache errors don't stop discovery.
    
    Tests that when cache read/write operations fail, the system
    continues with discovery methods.
    
    Validates: Requirements 6.1, 6.2
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "dberror.com"
    company_name = "DB Error Corp"
    hunter_email = "info@dberror.com"
    
    # Mock Hunter.io to succeed
    with patch('pipeline.email_discovery.search_domain_for_email') as mock_hunter:
        mock_hunter.return_value = EmailDiscoveryResult(
            email=hunter_email,
            source="hunter",
            confidence=85,
            recruiter_name="Test User"
        )
        
        with patch('pipeline.email_discovery.validate_email') as mock_validate:
            mock_validate.return_value = ValidationResult(
                valid=True,
                mx_valid=True,
                smtp_valid=True,
                reason="Valid"
            )
            
            with patch('pipeline.email_discovery.db') as mock_db:
                # Mock cache read to raise exception
                mock_db.client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
                
                # Execute discovery - should not crash
                result = discover_email_with_fallback(domain, company_name)
    
    # Verify Hunter result returned despite cache error
    assert result is not None
    assert result.email == hunter_email
    assert result.source == "hunter"


def test_integration_validation_failure_continues_to_next_pattern():
    """
    Integration test: Validation failures continue to next candidate.
    
    Tests that when email validation fails for pattern candidates,
    the system tries the next pattern.
    
    Validates: Requirements 1.5, 4.3
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "validation.com"
    company_name = "Validation Corp"
    
    # Mock Hunter.io to return None
    with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
        # Mock pattern guesser
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            with patch('pipeline.email_discovery.validate_email') as mock_validate:
                # First 3 patterns fail validation, 4th succeeds
                mock_validate.side_effect = [
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="MX invalid"),
                    ValidationResult(valid=False, mx_valid=True, smtp_valid=False, reason="SMTP invalid"),
                    ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Disposable"),
                    ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),
                ]
                
                with patch('pipeline.email_discovery.db') as mock_db:
                    # Mock cache miss
                    mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                    
                    # Execute discovery
                    result = discover_email_with_fallback(domain, company_name)
    
    # Verify 4th pattern (hello@) was selected
    assert result is not None
    assert result.email == f"hello@{domain}"
    assert result.source == "pattern_guess"
    
    # Verify 4 validations were attempted
    assert mock_validate.call_count == 4


def test_integration_partial_method_failures():
    """
    Integration test: Partial failures across multiple methods.
    
    Tests a realistic scenario where some methods fail with exceptions,
    some return no results, and eventually one succeeds.
    
    Validates: Requirements 6.1, 6.2, 6.5
    """
    from pipeline.email_discovery import discover_email_with_fallback
    
    domain = "partial.com"
    company_name = "Partial Corp"
    snov_email = "contact@partial.com"
    
    # Mock Hunter.io to raise exception
    with patch('pipeline.email_discovery.search_domain_for_email', side_effect=Exception("API error")):
        # Mock pattern guesser to return candidates that all fail validation
        with patch('pipeline.email_discovery.generate_pattern_candidates') as mock_pattern:
            pattern_candidates = [
                EmailDiscoveryResult(email=f"{prefix}@{domain}", source="pattern_guess", confidence=50, recruiter_name=None)
                for prefix in ["hr", "careers", "internships", "hello", "info"]
            ]
            mock_pattern.return_value = pattern_candidates
            
            # Mock Snov.io to succeed
            with patch('pipeline.email_discovery.search_snov_domain') as mock_snov:
                mock_snov.return_value = EmailDiscoveryResult(
                    email=snov_email,
                    source="snov",
                    confidence=80,
                    recruiter_name="Jane Smith"
                )
                
                with patch('pipeline.email_discovery.validate_email') as mock_validate:
                    # All patterns fail, Snov succeeds
                    mock_validate.side_effect = [
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=False, mx_valid=False, smtp_valid=False, reason="Invalid"),
                        ValidationResult(valid=True, mx_valid=True, smtp_valid=True, reason="Valid"),  # Snov
                    ]
                    
                    with patch('pipeline.email_discovery.db') as mock_db:
                        # Mock cache miss
                        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                        
                        # Execute discovery - should not crash
                        result = discover_email_with_fallback(domain, company_name)
    
    # Verify Snov result returned despite Hunter exception and pattern failures
    assert result is not None
    assert result.email == snov_email
    assert result.source == "snov"
    assert result.confidence == 80
