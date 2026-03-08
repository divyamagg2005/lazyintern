"""
Property-based tests for website_scraper.py module.

Feature: email-discovery-fallback-chain
"""

from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, call
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.website_scraper import scrape_domain_for_email, SCRAPE_PATHS


# Domain strategy: valid domain strings with at least one dot
domains = st.builds(
    lambda name, tld: f"{name}.{tld}",
    name=st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
        min_size=1,
        max_size=30
    ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-')),
    tld=st.text(
        alphabet=st.characters(whitelist_categories=('Ll',)),
        min_size=2,
        max_size=10
    )
)


@settings(max_examples=100)
@given(domain=domains, page_index=st.integers(min_value=0, max_value=2))
def test_property_6_website_scraping_order_and_early_exit(domain, page_index):
    """
    Feature: email-discovery-fallback-chain
    Property 6: Website Scraping Order and Early Exit
    
    **Validates: Requirements 3.1, 3.4**
    
    For any domain, the website scraper shall attempt to scrape URLs in the 
    order [/contact, /about, /careers], and shall stop scraping additional 
    pages when an email is found on any page.
    """
    # Track which URLs were called
    called_urls = []
    
    # Use a simple email that will always match the regex
    test_email = "contact@example.com"
    
    def mock_fetcher_get(url, **kwargs):
        """Mock Fetcher.get that tracks calls and returns appropriate content."""
        called_urls.append(url)
        
        # Determine which page index this is
        for i, path in enumerate(SCRAPE_PATHS):
            if url.endswith(path):
                mock_page = Mock()
                if i < page_index:
                    # Pages before page_index have no emails
                    mock_page.html_content = "No emails here"
                    return mock_page
                elif i == page_index:
                    # page_index has an email
                    mock_page.html_content = f"Contact us at {test_email}"
                    return mock_page
                else:
                    # Pages after page_index shouldn't be called - this is a test failure
                    # But we need to return something to avoid breaking the scraper
                    mock_page.html_content = "Should not reach here"
                    return mock_page
        
        # Shouldn't reach here - return empty page
        mock_page = Mock()
        mock_page.html_content = "Unexpected URL"
        return mock_page
    
    with patch('pipeline.website_scraper.Fetcher.get', side_effect=mock_fetcher_get):
        # Execute scraping
        result = scrape_domain_for_email(domain)
        
        # Verify email was found
        assert result is not None, f"Expected email to be found on page {page_index}"
        assert result.email == test_email
        assert result.source == "scraped"
        assert result.confidence == 70
        
        # Verify correct number of calls (should stop after finding email)
        expected_calls = page_index + 1
        assert len(called_urls) == expected_calls, \
            f"Expected {expected_calls} calls, got {len(called_urls)}. URLs called: {called_urls}"
        
        # Verify URLs were called in correct order
        expected_urls = [f"https://{domain}{path}" for path in SCRAPE_PATHS[:expected_calls]]
        assert called_urls == expected_urls, \
            f"Expected URLs {expected_urls}, got {called_urls}"


if __name__ == "__main__":
    # Run the property test
    test_property_6_website_scraping_order_and_early_exit()
    print("Property test passed: Website Scraping Order and Early Exit")


# Email strategy for generating valid emails that match our regex
# Pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
valid_emails = st.builds(
    lambda local, domain, tld: f"{local}@{domain}.{tld}",
    local=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-',
        min_size=1,
        max_size=20
    ).filter(lambda x: x and x[0].isalnum()),  # Must start with alphanumeric
    domain=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
        min_size=1,
        max_size=20
    ).filter(lambda x: x and x[0].isalnum() and not x.startswith('-') and not x.endswith('-')),
    tld=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        min_size=2,
        max_size=10
    )
)


@settings(max_examples=100)
@given(email=valid_emails, extra_text=st.text(min_size=10, max_size=100))
def test_property_7_email_extraction_from_html(email, extra_text):
    """
    Feature: email-discovery-fallback-chain
    Property 7: Email Extraction from HTML
    
    **Validates: Requirements 3.3, 3.5, 3.6**
    
    For any HTML content containing email addresses, the website scraper 
    shall extract emails matching the regex pattern and return the first 
    valid email with source="scraped" and confidence=70.
    """
    # Create HTML with embedded email
    html_content = f"<html><body>{extra_text} Contact: {email} {extra_text}</body></html>"
    
    # Mock the Fetcher.get to return our HTML
    mock_page = Mock()
    mock_page.html_content = html_content
    
    with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
        result = scrape_domain_for_email("example.com")
        
        # Verify email was extracted
        assert result is not None, f"Expected email to be extracted from HTML"
        assert result.email == email, f"Expected {email}, got {result.email}"
        assert result.source == "scraped"
        assert result.confidence == 70
        assert result.recruiter_name is None


@settings(max_examples=100)
@given(emails_list=st.lists(valid_emails, min_size=2, max_size=5))
def test_property_7_first_email_selected(emails_list):
    """
    Feature: email-discovery-fallback-chain
    Property 7: Email Extraction from HTML (First Email Selection)
    
    **Validates: Requirements 3.3, 3.5, 3.6**
    
    When multiple emails exist in HTML, the scraper shall return the first one.
    """
    # Create HTML with multiple emails
    html_content = "<html><body>Contacts: " + " and ".join(emails_list) + "</body></html>"
    
    # Mock the Fetcher.get to return our HTML
    mock_page = Mock()
    mock_page.html_content = html_content
    
    with patch('pipeline.website_scraper.Fetcher.get', return_value=mock_page):
        result = scrape_domain_for_email("example.com")
        
        # Verify first email was selected
        assert result is not None, f"Expected email to be extracted from HTML"
        assert result.email == emails_list[0], f"Expected first email {emails_list[0]}, got {result.email}"
        assert result.source == "scraped"
        assert result.confidence == 70


@settings(max_examples=100)
@given(
    domain=domains,
    failure_indices=st.lists(st.integers(min_value=0, max_value=2), min_size=1, max_size=2, unique=True),
    success_index=st.integers(min_value=0, max_value=2)
)
def test_property_8_scraping_resilience(domain, failure_indices, success_index):
    """
    Feature: email-discovery-fallback-chain
    Property 8: Scraping Resilience
    
    **Validates: Requirements 3.7, 3.8**
    
    For any list of URLs to scrape, if scraping fails for one URL, the 
    scraper shall log the error and continue to the next URL, returning 
    None only if all URLs fail.
    """
    # Ensure success_index is not in failure_indices
    if success_index in failure_indices:
        # Skip this test case - we need at least one success
        return
    
    # Track which URLs were called
    called_urls = []
    test_email = "contact@example.com"
    
    def mock_fetcher_get(url, **kwargs):
        """Mock Fetcher.get that simulates failures and success."""
        called_urls.append(url)
        
        # Determine which page index this is
        for i, path in enumerate(SCRAPE_PATHS):
            if url.endswith(path):
                if i in failure_indices:
                    # Simulate failure
                    raise Exception(f"Simulated failure for {path}")
                elif i == success_index:
                    # Return success
                    mock_page = Mock()
                    mock_page.html_content = f"Contact us at {test_email}"
                    return mock_page
                else:
                    # Return page with no email
                    mock_page = Mock()
                    mock_page.html_content = "No emails here"
                    return mock_page
        
        # Shouldn't reach here
        mock_page = Mock()
        mock_page.html_content = "Unexpected URL"
        return mock_page
    
    with patch('pipeline.website_scraper.Fetcher.get', side_effect=mock_fetcher_get):
        result = scrape_domain_for_email(domain)
        
        # Verify email was found (since we have at least one success)
        assert result is not None, f"Expected email to be found despite failures"
        assert result.email == test_email
        assert result.source == "scraped"
        assert result.confidence == 70
        
        # Verify scraper continued after failures
        # It should have called URLs up to and including the success_index
        expected_min_calls = success_index + 1
        assert len(called_urls) >= expected_min_calls, \
            f"Expected at least {expected_min_calls} calls, got {len(called_urls)}"


@settings(max_examples=100)
@given(domain=domains)
def test_property_8_all_urls_fail(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 8: Scraping Resilience (All Failures)
    
    **Validates: Requirements 3.7, 3.8**
    
    When all URLs fail, the scraper shall return None.
    """
    def mock_fetcher_get(url, **kwargs):
        """Mock Fetcher.get that always fails."""
        raise Exception("Simulated failure")
    
    with patch('pipeline.website_scraper.Fetcher.get', side_effect=mock_fetcher_get):
        result = scrape_domain_for_email(domain)
        
        # Verify None returned when all URLs fail
        assert result is None, f"Expected None when all URLs fail"


@settings(max_examples=100)
@given(domain=domains, timeout_index=st.integers(min_value=0, max_value=1))  # Only test first 2 indices
def test_property_16_scraping_timeout_handling(domain, timeout_index):
    """
    Feature: email-discovery-fallback-chain
    Property 16: Scraping Timeout Handling
    
    **Validates: Requirements 6.4**
    
    For any Scrapling fetch that times out, the website scraper shall log 
    the timeout and continue to the next URL without raising an exception.
    """
    # Track which URLs were called
    called_urls = []
    test_email = "contact@example.com"
    
    def mock_fetcher_get(url, **kwargs):
        """Mock Fetcher.get that simulates timeout and success."""
        called_urls.append(url)
        
        # Determine which page index this is
        for i, path in enumerate(SCRAPE_PATHS):
            if url.endswith(path):
                if i == timeout_index:
                    # Simulate timeout
                    raise TimeoutError("Request timed out")
                elif i == timeout_index + 1:
                    # Next URL after timeout has email
                    mock_page = Mock()
                    mock_page.html_content = f"Contact us at {test_email}"
                    return mock_page
                else:
                    # Other URLs have no email
                    mock_page = Mock()
                    mock_page.html_content = "No emails here"
                    return mock_page
        
        # Shouldn't reach here
        mock_page = Mock()
        mock_page.html_content = "Unexpected URL"
        return mock_page
    
    with patch('pipeline.website_scraper.Fetcher.get', side_effect=mock_fetcher_get):
        result = scrape_domain_for_email(domain)
        
        # Verify email was found despite timeout
        assert result is not None, f"Expected email to be found despite timeout"
        assert result.email == test_email
        assert result.source == "scraped"
        assert result.confidence == 70
        
        # Verify scraper continued after timeout
        # Should have called at least 2 URLs (timeout + success)
        assert len(called_urls) >= 2, \
            f"Expected at least 2 calls (timeout + success), got {len(called_urls)}"


if __name__ == "__main__":
    # Run all property tests
    test_property_6_website_scraping_order_and_early_exit()
    print("Property test passed: Website Scraping Order and Early Exit")
    
    test_property_7_email_extraction_from_html()
    print("Property test passed: Email Extraction from HTML")
    
    test_property_7_first_email_selected()
    print("Property test passed: First Email Selection")
    
    test_property_8_scraping_resilience()
    print("Property test passed: Scraping Resilience")
    
    test_property_8_all_urls_fail()
    print("Property test passed: All URLs Fail")
    
    test_property_16_scraping_timeout_handling()
    print("Property test passed: Scraping Timeout Handling")
