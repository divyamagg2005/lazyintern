"""
Unit tests for pattern_guesser.py module.

These tests complement the property tests by validating specific examples
and edge cases for the pattern generation function.

Feature: email-discovery-fallback-chain
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import sys
import os
import unittest

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.pattern_guesser import generate_pattern_candidates, EmailDiscoveryResult


class TestPatternGuesserCommonDomains(unittest.TestCase):
    """Test pattern generation with common, well-known domains."""
    
    def test_google_domain(self):
        """Test pattern generation for google.com."""
        candidates = generate_pattern_candidates("google.com")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@google.com"
        assert candidates[1].email == "careers@google.com"
        assert candidates[2].email == "internships@google.com"
        assert candidates[3].email == "hello@google.com"
        assert candidates[4].email == "info@google.com"
        
        # Verify metadata
        for candidate in candidates:
            assert candidate.source == "pattern_guess"
            assert candidate.confidence == 50
            assert candidate.recruiter_name is None
    
    def test_microsoft_domain(self):
        """Test pattern generation for microsoft.com."""
        candidates = generate_pattern_candidates("microsoft.com")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@microsoft.com"
        assert candidates[1].email == "careers@microsoft.com"
        assert candidates[2].email == "internships@microsoft.com"
        assert candidates[3].email == "hello@microsoft.com"
        assert candidates[4].email == "info@microsoft.com"
        
        # Verify all have correct metadata
        assert all(c.source == "pattern_guess" for c in candidates)
        assert all(c.confidence == 50 for c in candidates)


class TestPatternGuesserEdgeCaseDomains(unittest.TestCase):
    """Test pattern generation with edge case domains."""
    
    def test_single_letter_domain(self):
        """Test pattern generation for single-letter.io."""
        candidates = generate_pattern_candidates("single-letter.io")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@single-letter.io"
        assert candidates[1].email == "careers@single-letter.io"
        assert candidates[2].email == "internships@single-letter.io"
        assert candidates[3].email == "hello@single-letter.io"
        assert candidates[4].email == "info@single-letter.io"
    
    def test_very_long_domain_name(self):
        """Test pattern generation for very-long-domain-name.com."""
        domain = "very-long-domain-name.com"
        candidates = generate_pattern_candidates(domain)
        
        assert len(candidates) == 5
        assert all(c.email.endswith(f"@{domain}") for c in candidates)
        assert candidates[0].email == f"hr@{domain}"
        assert candidates[4].email == f"info@{domain}"
    
    def test_domain_with_numbers(self):
        """Test pattern generation for domain with numbers like tech123.com."""
        candidates = generate_pattern_candidates("tech123.com")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@tech123.com"
        assert candidates[1].email == "careers@tech123.com"
    
    def test_domain_with_hyphens(self):
        """Test pattern generation for domain with hyphens like my-company.com."""
        candidates = generate_pattern_candidates("my-company.com")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@my-company.com"
        assert candidates[2].email == "internships@my-company.com"
    
    def test_subdomain(self):
        """Test pattern generation for subdomain like careers.company.com."""
        candidates = generate_pattern_candidates("careers.company.com")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@careers.company.com"
        assert candidates[1].email == "careers@careers.company.com"


class TestPatternGuesserInternationalDomains(unittest.TestCase):
    """Test pattern generation with international domain extensions."""
    
    def test_uk_domain(self):
        """Test pattern generation for .co.uk domain."""
        candidates = generate_pattern_candidates("company.co.uk")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@company.co.uk"
        assert candidates[1].email == "careers@company.co.uk"
        assert candidates[2].email == "internships@company.co.uk"
        assert candidates[3].email == "hello@company.co.uk"
        assert candidates[4].email == "info@company.co.uk"
    
    def test_australian_domain(self):
        """Test pattern generation for .com.au domain."""
        candidates = generate_pattern_candidates("company.com.au")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@company.com.au"
        assert candidates[1].email == "careers@company.com.au"
        assert candidates[2].email == "internships@company.com.au"
        assert candidates[3].email == "hello@company.com.au"
        assert candidates[4].email == "info@company.com.au"
    
    def test_german_domain(self):
        """Test pattern generation for .de domain."""
        candidates = generate_pattern_candidates("firma.de")
        
        assert len(candidates) == 5
        assert all(c.email.endswith("@firma.de") for c in candidates)
    
    def test_japanese_domain(self):
        """Test pattern generation for .jp domain."""
        candidates = generate_pattern_candidates("company.co.jp")
        
        assert len(candidates) == 5
        assert all(c.email.endswith("@company.co.jp") for c in candidates)
    
    def test_canadian_domain(self):
        """Test pattern generation for .ca domain."""
        candidates = generate_pattern_candidates("company.ca")
        
        assert len(candidates) == 5
        assert candidates[0].email == "hr@company.ca"
        assert candidates[4].email == "info@company.ca"


class TestPatternGuesserOrderAndMetadata(unittest.TestCase):
    """Test that pattern order and metadata are always correct."""
    
    def test_pattern_order_is_consistent(self):
        """Verify pattern order is always the same regardless of domain."""
        domains = [
            "example.com",
            "test.org",
            "company.io",
            "startup.ai",
            "business.net"
        ]
        
        expected_prefixes = ['hr', 'careers', 'internships', 'hello', 'info']
        
        for domain in domains:
            candidates = generate_pattern_candidates(domain)
            actual_prefixes = [c.email.split('@')[0] for c in candidates]
            assert actual_prefixes == expected_prefixes, \
                f"Pattern order incorrect for {domain}"
    
    def test_all_candidates_have_correct_source(self):
        """Verify all candidates have source='pattern_guess'."""
        candidates = generate_pattern_candidates("example.com")
        
        for candidate in candidates:
            assert candidate.source == "pattern_guess"
    
    def test_all_candidates_have_correct_confidence(self):
        """Verify all candidates have confidence=50."""
        candidates = generate_pattern_candidates("example.com")
        
        for candidate in candidates:
            assert candidate.confidence == 50
    
    def test_all_candidates_have_no_recruiter_name(self):
        """Verify all candidates have recruiter_name=None."""
        candidates = generate_pattern_candidates("example.com")
        
        for candidate in candidates:
            assert candidate.recruiter_name is None
    
    def test_result_type_is_email_discovery_result(self):
        """Verify all results are EmailDiscoveryResult instances."""
        candidates = generate_pattern_candidates("example.com")
        
        for candidate in candidates:
            assert isinstance(candidate, EmailDiscoveryResult)


class TestPatternGuesserReturnValue(unittest.TestCase):
    """Test the return value structure and type."""
    
    def test_returns_list(self):
        """Verify function returns a list."""
        result = generate_pattern_candidates("example.com")
        assert isinstance(result, list)
    
    def test_returns_exactly_five_items(self):
        """Verify function always returns exactly 5 items."""
        test_domains = [
            "a.com",
            "example.com",
            "very-long-company-name-here.co.uk",
            "x.io",
            "test123.org"
        ]
        
        for domain in test_domains:
            candidates = generate_pattern_candidates(domain)
            assert len(candidates) == 5, \
                f"Expected 5 candidates for {domain}, got {len(candidates)}"
    
    def test_list_items_are_email_discovery_results(self):
        """Verify all list items are EmailDiscoveryResult objects."""
        candidates = generate_pattern_candidates("example.com")
        
        assert all(isinstance(c, EmailDiscoveryResult) for c in candidates)


class TestPatternGuesserEmailFormat(unittest.TestCase):
    """Test that generated emails have correct format."""
    
    def test_emails_contain_at_symbol(self):
        """Verify all generated emails contain @ symbol."""
        candidates = generate_pattern_candidates("example.com")
        
        for candidate in candidates:
            assert '@' in candidate.email
    
    def test_emails_have_correct_domain_suffix(self):
        """Verify all emails end with @domain."""
        domain = "testcompany.com"
        candidates = generate_pattern_candidates(domain)
        
        for candidate in candidates:
            assert candidate.email.endswith(f"@{domain}")
    
    def test_email_format_is_pattern_at_domain(self):
        """Verify email format is pattern@domain."""
        candidates = generate_pattern_candidates("example.com")
        
        expected_emails = [
            "hr@example.com",
            "careers@example.com",
            "internships@example.com",
            "hello@example.com",
            "info@example.com"
        ]
        
        actual_emails = [c.email for c in candidates]
        assert actual_emails == expected_emails


if __name__ == "__main__":
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserCommonDomains))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserEdgeCaseDomains))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserInternationalDomains))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserOrderAndMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserReturnValue))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternGuesserEmailFormat))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
