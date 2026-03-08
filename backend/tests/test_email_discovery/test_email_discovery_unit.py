"""
Unit tests for email_discovery.py orchestrator module.

Feature: email-discovery-fallback-chain

These tests verify specific scenarios and edge cases for the email discovery
fallback chain orchestrator.
"""

from unittest.mock import patch, MagicMock
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.email_discovery import discover_email_with_fallback
from pipeline.pattern_guesser import EmailDiscoveryResult
from pipeline.email_validator import ValidationResult


def test_cache_hit_scenario():
    """
    Test that when cache contains a result, no discovery methods are called.
    
    Validates: Requirements 8.3, 8.4
    """
    domain = "example.com"
    company_name = "Example Corp"
    cached_email = "hr@example.com"
    
    # Track method calls
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache hit
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{
            'domain': domain,
            'emails': [{
                'email': cached_email,
                'source': 'hunter',
                'confidence': 85
            }]
        }]
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            result = discover_email_with_fallback(domain, company_name)
            
            assert result is not None
            assert result.email == cached_email
            assert len(methods_called) == 0, "No methods should be called on cache hit"
    
    print("✓ Unit test passed: Cache hit scenario")


def test_hunter_success_no_fallback():
    """
    Test that when Hunter.io succeeds, no fallback methods are called.
    
    Validates: Requirements 4.2
    """
    domain = "example.com"
    company_name = "Example Corp"
    hunter_email = "contact@example.com"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return EmailDiscoveryResult(hunter_email, "hunter", 90, "John Doe")
    
    def mock_pattern(d):
        methods_called.append('pattern')
        return []
    
    def mock_snov(d):
        methods_called.append('snov')
        return None
    
    def mock_scraper(d):
        methods_called.append('scraper')
        return None
    
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                        result = discover_email_with_fallback(domain, company_name)
                        
                        assert result is not None
                        assert result.email == hunter_email
                        assert result.source == "hunter"
                        assert 'hunter' in methods_called
                        assert 'pattern' not in methods_called, "Pattern should not be called"
                        assert 'snov' not in methods_called, "Snov should not be called"
                        assert 'scraper' not in methods_called, "Scraper should not be called"
    
    print("✓ Unit test passed: Hunter success no fallback")


def test_hunter_fail_pattern_success():
    """
    Test that when Hunter.io fails, Pattern Guesser is tried and succeeds.
    
    Validates: Requirements 4.1, 4.3
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    def mock_pattern(d):
        methods_called.append('pattern')
        return [
            EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"careers@{d}", "pattern_guess", 50, None),
        ]
    
    def mock_validate(email, confidence):
        # Only hr@ passes validation
        if 'hr@' in email:
            return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
        return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
    
    def mock_snov(d):
        methods_called.append('snov')
        return None
    
    def mock_scraper(d):
        methods_called.append('scraper')
        return None
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            result = discover_email_with_fallback(domain, company_name)
                            
                            assert result is not None
                            assert result.email == f"hr@{domain}"
                            assert result.source == "pattern_guess"
                            assert 'hunter' in methods_called
                            assert 'pattern' in methods_called
                            assert 'snov' not in methods_called, "Snov should not be called"
                            assert 'scraper' not in methods_called, "Scraper should not be called"
    
    print("✓ Unit test passed: Hunter fail, pattern success")


def test_hunter_pattern_fail_snov_success():
    """
    Test fallback chain: Hunter fails, Pattern fails, Snov succeeds.
    
    Validates: Requirements 4.1, 4.3
    """
    domain = "example.com"
    company_name = "Example Corp"
    snov_email = "info@example.com"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    def mock_pattern(d):
        methods_called.append('pattern')
        return [EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None)]
    
    def mock_validate(email, confidence):
        # Pattern fails, Snov succeeds
        if 'hr@' in email:
            return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
        return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    def mock_snov(d):
        methods_called.append('snov')
        return EmailDiscoveryResult(snov_email, "snov", 85, None)
    
    def mock_scraper(d):
        methods_called.append('scraper')
        return None
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            result = discover_email_with_fallback(domain, company_name)
                            
                            assert result is not None
                            assert result.email == snov_email
                            assert result.source == "snov"
                            assert 'hunter' in methods_called
                            assert 'pattern' in methods_called
                            assert 'snov' in methods_called
                            assert 'scraper' not in methods_called, "Scraper should not be called"
    
    print("✓ Unit test passed: Hunter and pattern fail, Snov success")


def test_all_methods_fail_scraper_success():
    """
    Test fallback chain: All methods fail except scraper.
    
    Validates: Requirements 4.1, 4.3
    """
    domain = "example.com"
    company_name = "Example Corp"
    scraped_email = "contact@example.com"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    def mock_pattern(d):
        methods_called.append('pattern')
        return []
    
    def mock_snov(d):
        methods_called.append('snov')
        return None
    
    def mock_scraper(d):
        methods_called.append('scraper')
        return EmailDiscoveryResult(scraped_email, "scraped", 70, None)
    
    def mock_validate(email, confidence):
        return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            result = discover_email_with_fallback(domain, company_name)
                            
                            assert result is not None
                            assert result.email == scraped_email
                            assert result.source == "scraped"
                            assert 'hunter' in methods_called
                            assert 'pattern' in methods_called
                            assert 'snov' in methods_called
                            assert 'scraper' in methods_called
    
    print("✓ Unit test passed: All methods fail except scraper")


def test_all_methods_fail_return_none():
    """
    Test that when all methods fail, None is returned.
    
    Validates: Requirements 4.4
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    def mock_hunter(d):
        return None
    
    def mock_pattern(d):
        return []
    
    def mock_snov(d):
        return None
    
    def mock_scraper(d):
        return None
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                        result = discover_email_with_fallback(domain, company_name)
                        
                        assert result is None
    
    print("✓ Unit test passed: All methods fail return None")


def test_validation_failure_continues_to_next_method():
    """
    Test that when validation fails, the system continues to next method.
    
    Validates: Requirements 4.3
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    def mock_pattern(d):
        methods_called.append('pattern')
        # Return patterns that will fail validation
        return [
            EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"careers@{d}", "pattern_guess", 50, None),
        ]
    
    def mock_validate(email, confidence):
        # All patterns fail validation (hr@ and careers@)
        if 'hr@' in email or 'careers@' in email:
            return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
        # Snov succeeds (info@)
        return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    def mock_snov(d):
        methods_called.append('snov')
        return EmailDiscoveryResult(f"info@{d}", "snov", 80, None)
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        result = discover_email_with_fallback(domain, company_name)
                        
                        assert result is not None
                        assert result.source == "snov"
                        assert 'hunter' in methods_called
                        assert 'pattern' in methods_called
                        assert 'snov' in methods_called
    
    print("✓ Unit test passed: Validation failure continues to next method")


def test_exception_in_method_continues_chain():
    """
    Test that exceptions in one method don't crash the pipeline.
    
    Validates: Requirements 6.1, 6.2
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    methods_called = []
    
    def mock_hunter(d):
        methods_called.append('hunter')
        raise Exception("Hunter API error")
    
    def mock_pattern(d):
        methods_called.append('pattern')
        return [EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None)]
    
    def mock_validate(email, confidence):
        return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    with patch('pipeline.email_discovery.db') as mock_db:
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate):
                    # Should not raise exception
                    result = discover_email_with_fallback(domain, company_name)
                    
                    assert result is not None
                    assert result.source == "pattern_guess"
                    assert 'hunter' in methods_called
                    assert 'pattern' in methods_called
    
    print("✓ Unit test passed: Exception in method continues chain")


def test_database_cache_read_failure():
    """
    Test that database cache read failures don't block discovery.
    
    Validates: Requirements 6.1, 6.2
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    def mock_hunter(d):
        return EmailDiscoveryResult(f"contact@{d}", "hunter", 85, None)
    
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache read failure
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("Database error")
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            # Should not raise exception
            result = discover_email_with_fallback(domain, company_name)
            
            assert result is not None
            assert result.source == "hunter"
    
    print("✓ Unit test passed: Database cache read failure")


def test_database_cache_write_failure():
    """
    Test that database cache write failures don't block discovery.
    
    Validates: Requirements 6.1, 6.2
    """
    domain = "example.com"
    company_name = "Example Corp"
    
    def mock_hunter(d):
        return EmailDiscoveryResult(f"contact@{d}", "hunter", 85, None)
    
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        # Mock cache write failure
        mock_db.client.table.return_value.upsert.side_effect = Exception("Database write error")
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            # Should not raise exception
            result = discover_email_with_fallback(domain, company_name)
            
            assert result is not None
            assert result.source == "hunter"
    
    print("✓ Unit test passed: Database cache write failure")


if __name__ == "__main__":
    test_cache_hit_scenario()
    test_hunter_success_no_fallback()
    test_hunter_fail_pattern_success()
    test_hunter_pattern_fail_snov_success()
    test_all_methods_fail_scraper_success()
    test_all_methods_fail_return_none()
    test_validation_failure_continues_to_next_method()
    test_exception_in_method_continues_chain()
    test_database_cache_read_failure()
    test_database_cache_write_failure()
    print("\n✅ All unit tests passed!")