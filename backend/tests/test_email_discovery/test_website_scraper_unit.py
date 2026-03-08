"""
Unit tests for website_scraper.py module.

Tests the website scraping functionality for email discovery.

Feature: email-discovery-fallback-chain
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.website_scraper import scrape_domain_for_email, EmailDiscoveryResult


class TestWebsiteScraperUnit(unittest.TestCase):
    """Unit tests for website scraper module."""
    
    def test_scrape_finds_email_on_contact_page(self):
        """Test that scraper finds email on /contact page and stops."""
        mock_page = Mock()
        mock_page.html_content = "Contact us at hr@example.com for inquiries"
        
        with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
            result = scrape_domain_for_email("example.com")
        
        assert result is not None
        assert result.email == "hr@example.com"
        assert result.source == "scraped"
        assert result.confidence == 70
        assert result.recruiter_name is None
    
    def test_scrape_tries_multiple_pages(self):
        """Test that scraper tries /about after /contact fails."""
        mock_page_no_email = Mock()
        mock_page_no_email.html_content = "Welcome to our company"
        
        mock_page_with_email = Mock()
        mock_page_with_email.html_content = "About us: contact@example.com"
        
        with patch('pipeline.website_scraper.Fetcher.get') as mock_get:
            # First call (/contact) returns no email, second call (/about) has email
            mock_get.side_effect = [mock_page_no_email, mock_page_with_email]
            result = scrape_domain_for_email("example.com")
        
        assert result is not None
        assert result.email == "contact@example.com"
        assert mock_get.call_count == 2
    
    def test_scrape_returns_none_when_no_emails_found(self):
        """Test that scraper returns None when no emails found on any page."""
        mock_page = Mock()
        mock_page.html_content = "No emails here"
        
        with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
            result = scrape_domain_for_email("example.com")
        
        assert result is None
    
    def test_scrape_continues_on_error(self):
        """Test that scraper continues to next URL when one fails."""
        mock_page_with_email = Mock()
        mock_page_with_email.html_content = "Careers: jobs@example.com"
        
        with patch('pipeline.website_scraper.Fetcher.get') as mock_get:
            # First two calls raise exceptions, third succeeds
            mock_get.side_effect = [
                Exception("Timeout"),
                Exception("404 Not Found"),
                mock_page_with_email
            ]
            result = scrape_domain_for_email("example.com")
        
        assert result is not None
        assert result.email == "jobs@example.com"
        assert mock_get.call_count == 3
    
    def test_scrape_returns_first_email_found(self):
        """Test that scraper returns first email when multiple emails exist."""
        mock_page = Mock()
        mock_page.html_content = "Contact: first@example.com or second@example.com"
        
        with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
            result = scrape_domain_for_email("example.com")
        
        assert result is not None
        assert result.email == "first@example.com"
    
    def test_scrape_handles_bytes_body(self):
        """Test that scraper handles page.body as bytes."""
        mock_page = Mock()
        mock_page.html_content = None
        mock_page.body = b"Contact: info@example.com"
        
        with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
            result = scrape_domain_for_email("example.com")
        
        assert result is not None
        assert result.email == "info@example.com"
    
    def test_scrape_extracts_valid_email_formats(self):
        """Test that scraper extracts various valid email formats."""
        test_cases = [
            ("simple@example.com", "simple@example.com"),
            ("first.last@example.com", "first.last@example.com"),
            ("user+tag@example.co.uk", "user+tag@example.co.uk"),
            ("123@example.io", "123@example.io"),
        ]
        
        for html_email, expected_email in test_cases:
            mock_page = Mock()
            mock_page.html_content = f"Contact: {html_email}"
            
            with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
                result = scrape_domain_for_email("example.com")
            
            assert result is not None
            assert result.email == expected_email
    
    def test_scrape_logs_errors_without_raising(self):
        """Test that scraper logs errors but doesn't raise exceptions."""
        with patch('pipeline.website_scraper.Fetcher.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Should not raise exception
            result = scrape_domain_for_email("example.com")
            
            assert result is None
            assert mock_get.call_count == 3  # Tries all 3 URLs


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWebsiteScraperUnit))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
