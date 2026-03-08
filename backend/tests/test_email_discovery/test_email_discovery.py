"""
Property-based tests for email_discovery.py orchestrator module.

Feature: email-discovery-fallback-chain
"""

from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.email_discovery import discover_email_with_fallback
from pipeline.pattern_guesser import EmailDiscoveryResult
from pipeline.email_validator import ValidationResult


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

# Email strategy
emails = st.emails()

# Company name strategy
company_names = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters=' -'),
    min_size=1,
    max_size=30
)


@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names,
    valid_index=st.integers(min_value=0, max_value=4)
)
def test_property_2_pattern_validation_and_selection(domain, company_name, valid_index):
    """
    Feature: email-discovery-fallback-chain
    Property 2: Pattern Validation and Selection
    
    **Validates: Requirements 1.5**
    
    For any list of pattern candidates with varying validation results, 
    the email discovery system shall validate all candidates and return 
    the first one that passes validation, or None if all fail validation.
    """
    # Create mock validation results where only one candidate is valid
    # The valid candidate is at position valid_index
    def mock_validate_email(email, confidence):
        # Extract pattern from email
        pattern = email.split('@')[0]
        patterns = ['hr', 'careers', 'internships', 'hello', 'info']
        
        # Only the pattern at valid_index should be valid
        if pattern == patterns[valid_index]:
            return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
        else:
            return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
            with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate_email) as mock_validator:
                with patch('pipeline.email_discovery.search_snov_domain', return_value=None):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', return_value=None):
                        # Execute discovery
                        result = discover_email_with_fallback(domain, company_name)
                        
                        # Verify result is the first valid candidate
                        assert result is not None, "Should return the valid candidate"
                        
                        # Verify it's the correct pattern
                        patterns = ['hr', 'careers', 'internships', 'hello', 'info']
                        expected_email = f"{patterns[valid_index]}@{domain}"
                        assert result.email == expected_email, \
                            f"Expected {expected_email}, got {result.email}"
                        
                        # Verify source and confidence
                        assert result.source == "pattern_guess"
                        assert result.confidence == 50
                        
                        # Verify all candidates up to and including valid_index were validated
                        # validate_email is called for each pattern until one is valid
                        assert mock_validator.call_count >= valid_index + 1, \
                            f"Should validate at least {valid_index + 1} candidates"
                        
                        # Verify the valid candidate was validated
                        validated_emails = [call_args[0][0] for call_args in mock_validator.call_args_list]
                        assert expected_email in validated_emails, \
                            f"Expected email {expected_email} should have been validated"


@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names
)
def test_property_2_pattern_validation_all_fail(domain, company_name):
    """
    Feature: email-discovery-fallback-chain
    Property 2: Pattern Validation and Selection (All Fail)
    
    **Validates: Requirements 1.5**
    
    When all pattern candidates fail validation, the system shall continue 
    to the next fallback method (Snov.io).
    """
    # Mock Snov.io returning a valid result
    snov_result = EmailDiscoveryResult(
        email=f"contact@{domain}",
        source="snov",
        confidence=85,
        recruiter_name=None
    )
    
    # Track validation calls
    validation_calls = []
    
    # Mock validation: patterns fail, snov succeeds
    def mock_validate_email(email, confidence):
        validation_calls.append(email)
        # Pattern emails fail
        if any(pattern in email for pattern in ['hr@', 'careers@', 'internships@', 'hello@', 'info@']):
            return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
        # Snov email succeeds
        else:
            return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', return_value=None):
            with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate_email) as mock_validator:
                with patch('pipeline.email_discovery.search_snov_domain', return_value=snov_result) as mock_snov:
                    with patch('pipeline.email_discovery.scrape_domain_for_email', return_value=None):
                        # Execute discovery
                        result = discover_email_with_fallback(domain, company_name)
                        
                        # Verify all 5 pattern candidates were validated
                        pattern_validations = [e for e in validation_calls if any(p in e for p in ['hr@', 'careers@', 'internships@', 'hello@', 'info@'])]
                        assert len(pattern_validations) == 5, \
                            f"All 5 pattern candidates should be validated, got {len(pattern_validations)}"
                        
                        # Verify Snov.io was called (fallback continued)
                        assert mock_snov.called, "Snov.io should be called when all patterns fail"
                        
                        # Verify result is from Snov.io
                        assert result is not None, "Should return Snov.io result"
                        assert result.source == "snov"
                        assert result.email == snov_result.email


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")



@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names,
    success_method=st.sampled_from(['hunter', 'pattern', 'snov', 'scraper'])
)
def test_property_3_fallback_chain_short_circuit(domain, company_name, success_method):
    """
    Feature: email-discovery-fallback-chain
    Property 3: Fallback Chain Short-Circuit
    
    **Validates: Requirements 1.6, 2.6, 4.2**
    
    For any email discovery attempt, when any method (Hunter, Pattern, Snov, 
    Scraper) returns a validated email, all subsequent methods in the chain 
    shall not be executed.
    """
    # Track which methods were called
    methods_called = []
    
    # Create a valid result for the success method
    success_result = EmailDiscoveryResult(
        email=f"test@{domain}",
        source=success_method,
        confidence=80,
        recruiter_name=None
    )
    
    # Mock validation: only success method's email passes
    def mock_validate_email(email, confidence):
        if email == success_result.email:
            return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
        else:
            return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
    
    # Mock Hunter.io
    def mock_hunter(d):
        methods_called.append('hunter')
        if success_method == 'hunter':
            return success_result
        return None
    
    # Mock Pattern Guesser - need to mock generate_pattern_candidates
    def mock_pattern_gen(d):
        methods_called.append('pattern')
        if success_method == 'pattern':
            # Return one valid candidate
            return [success_result]
        # Return candidates that will fail validation
        return [
            EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"careers@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"internships@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"hello@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"info@{d}", "pattern_guess", 50, None)
        ]
    
    # Mock Snov.io
    def mock_snov(d):
        methods_called.append('snov')
        if success_method == 'snov':
            return success_result
        return None
    
    # Mock Scraper
    def mock_scraper(d):
        methods_called.append('scraper')
        if success_method == 'scraper':
            return success_result
        return None
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate_email):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            # Execute discovery
                            result = discover_email_with_fallback(domain, company_name)
                            
                            # Verify result is from the success method
                            assert result is not None, f"Should return result from {success_method}"
                            assert result.email == success_result.email
                            
                            # Verify short-circuit: methods after success_method should not be called
                            method_order = ['hunter', 'pattern', 'snov', 'scraper']
                            success_index = method_order.index(success_method)
                            
                            # All methods up to and including success_method should be called
                            for i in range(success_index + 1):
                                assert method_order[i] in methods_called, \
                                    f"Method {method_order[i]} should be called"
                            
                            # All methods after success_method should NOT be called
                            for i in range(success_index + 1, len(method_order)):
                                assert method_order[i] not in methods_called, \
                                    f"Method {method_order[i]} should NOT be called (short-circuit)"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")



@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names
)
def test_property_9_fallback_chain_execution_order(domain, company_name):
    """
    Feature: email-discovery-fallback-chain
    Property 9: Fallback Chain Execution Order
    
    **Validates: Requirements 4.1, 4.3**
    
    For any email discovery attempt, the system shall execute methods in the 
    order [Hunter, Pattern Guesser, Snov, Website Scraper], where each method 
    only executes if all previous methods returned no validated results.
    """
    # Track execution order
    execution_order = []
    
    # Mock all methods to return None (no results)
    def mock_hunter(d):
        execution_order.append('hunter')
        return None
    
    def mock_pattern_gen(d):
        execution_order.append('pattern')
        # Return candidates that will fail validation
        return [
            EmailDiscoveryResult(f"hr@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"careers@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"internships@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"hello@{d}", "pattern_guess", 50, None),
            EmailDiscoveryResult(f"info@{d}", "pattern_guess", 50, None)
        ]
    
    def mock_snov(d):
        execution_order.append('snov')
        return None
    
    def mock_scraper(d):
        execution_order.append('scraper')
        return None
    
    # Mock validation to always fail
    def mock_validate_email(email, confidence):
        return ValidationResult(valid=False, reason="smtp_failure", mx_valid=True, smtp_valid=False)
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate_email):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            # Execute discovery
                            result = discover_email_with_fallback(domain, company_name)
                            
                            # Verify all methods were called
                            assert len(execution_order) == 4, \
                                f"All 4 methods should be called, got {len(execution_order)}"
                            
                            # Verify correct execution order
                            expected_order = ['hunter', 'pattern', 'snov', 'scraper']
                            assert execution_order == expected_order, \
                                f"Expected order {expected_order}, got {execution_order}"
                            
                            # Verify result is None (all methods failed)
                            assert result is None, "Should return None when all methods fail"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")
    
    test_property_9_fallback_chain_execution_order()
    print("✓ Property test passed: Fallback Chain Execution Order")



@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names
)
def test_property_10_complete_failure_handling(domain, company_name):
    """
    Feature: email-discovery-fallback-chain
    Property 10: Complete Failure Handling
    
    **Validates: Requirements 4.4, 6.5**
    
    For any email discovery attempt where all methods return no results, 
    the system shall return None without raising an exception.
    """
    # Mock all methods to return None or fail validation
    def mock_hunter(d):
        return None
    
    def mock_pattern_gen(d):
        # Return empty list (no candidates)
        return []
    
    def mock_snov(d):
        return None
    
    def mock_scraper(d):
        return None
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                        # Execute discovery - should not raise exception
                        try:
                            result = discover_email_with_fallback(domain, company_name)
                            
                            # Verify result is None
                            assert result is None, "Should return None when all methods fail"
                            
                            # Verify complete_failure event was logged
                            log_calls = [call for call in mock_db.log_event.call_args_list 
                                       if len(call[0]) > 1 and call[0][1] == "email_discovery_complete_failure"]
                            assert len(log_calls) > 0, "Should log complete_failure event"
                            
                        except Exception as e:
                            # Should not raise any exception
                            assert False, f"Should not raise exception, but got: {e}"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")
    
    test_property_9_fallback_chain_execution_order()
    print("✓ Property test passed: Fallback Chain Execution Order")
    
    test_property_10_complete_failure_handling()
    print("✓ Property test passed: Complete Failure Handling")



@settings(max_examples=50)
@given(
    domain=domains,
    company_name=company_names,
    error_method=st.sampled_from(['hunter', 'pattern', 'snov', 'scraper'])
)
def test_property_14_fallback_method_error_resilience(domain, company_name, error_method):
    """
    Feature: email-discovery-fallback-chain
    Property 14: Fallback Method Error Resilience
    
    **Validates: Requirements 6.1, 6.2**
    
    For any fallback method that raises an exception, the system shall log 
    the error with method name and error details, then continue to the next 
    fallback method without crashing the pipeline.
    """
    # Track which methods were called
    methods_called = []
    
    # Create a test exception
    test_exception = Exception(f"Test error in {error_method}")
    
    # Mock methods - one raises exception, others return None
    def mock_hunter(d):
        methods_called.append('hunter')
        if error_method == 'hunter':
            raise test_exception
        return None
    
    def mock_pattern_gen(d):
        methods_called.append('pattern')
        if error_method == 'pattern':
            raise test_exception
        # Return empty list
        return []
    
    def mock_snov(d):
        methods_called.append('snov')
        if error_method == 'snov':
            raise test_exception
        return None
    
    def mock_scraper(d):
        methods_called.append('scraper')
        if error_method == 'scraper':
            raise test_exception
        return None
    
    # Mock all external dependencies
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                        # Execute discovery - should not raise exception
                        try:
                            result = discover_email_with_fallback(domain, company_name)
                            
                            # Verify all methods were attempted
                            assert len(methods_called) == 4, \
                                f"All 4 methods should be attempted, got {len(methods_called)}"
                            
                            # Verify error was logged
                            error_logs = [call for call in mock_db.log_event.call_args_list 
                                        if len(call[0]) > 1 and call[0][1] == "email_discovery_error"]
                            assert len(error_logs) > 0, "Should log error event"
                            
                            # Verify error log contains method name
                            error_log_data = error_logs[0][0][2]  # Third argument is the data dict
                            assert 'method' in error_log_data, "Error log should contain method name"
                            
                            # Verify result is None (all methods failed)
                            assert result is None, "Should return None when all methods fail"
                            
                        except Exception as e:
                            # Should not raise exception - errors should be caught
                            assert False, f"Should not raise exception, but got: {e}"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")
    
    test_property_9_fallback_chain_execution_order()
    print("✓ Property test passed: Fallback Chain Execution Order")
    
    test_property_10_complete_failure_handling()
    print("✓ Property test passed: Complete Failure Handling")
    
    test_property_14_fallback_method_error_resilience()
    print("✓ Property test passed: Fallback Method Error Resilience")



@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names,
    success_method=st.sampled_from(['hunter', 'pattern', 'snov', 'scraper']),
    email=emails,
    confidence=st.integers(min_value=50, max_value=100)
)
def test_property_17_domain_level_cache_update(domain, company_name, success_method, email, confidence):
    """
    Feature: email-discovery-fallback-chain
    Property 17: Domain-Level Cache Update
    
    **Validates: Requirements 8.1, 8.2**
    
    For any email discovery method that successfully finds an email for a domain, 
    the system shall update company_domains.emails with the discovered email and 
    source, and update company_domains.last_checked with the current timestamp.
    """
    # Create a valid result
    success_result = EmailDiscoveryResult(
        email=email,
        source=success_method,
        confidence=confidence,
        recruiter_name=None
    )
    
    # Mock validation to succeed
    def mock_validate_email(e, c):
        return ValidationResult(valid=True, reason=None, mx_valid=True, smtp_valid=True)
    
    # Mock the success method
    def mock_hunter(d):
        return success_result if success_method == 'hunter' else None
    
    def mock_pattern_gen(d):
        if success_method == 'pattern':
            return [success_result]
        return []
    
    def mock_snov(d):
        return success_result if success_method == 'snov' else None
    
    def mock_scraper(d):
        return success_result if success_method == 'scraper' else None
    
    # Track cache updates
    cache_updates = []
    
    # Mock database
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache miss
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_db.log_event = MagicMock()
        
        # Mock upsert to track cache updates
        def mock_upsert(data, on_conflict=None):
            cache_updates.append(data)
            mock_result = MagicMock()
            mock_result.execute.return_value = MagicMock()
            return mock_result
        
        mock_db.client.table.return_value.upsert = mock_upsert
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.validate_email', side_effect=mock_validate_email):
                    with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                        with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                            # Execute discovery
                            result = discover_email_with_fallback(domain, company_name)
                            
                            # Verify result
                            assert result is not None, "Should return result"
                            assert result.email == email
                            assert result.source == success_method
                            
                            # Verify cache was updated
                            assert len(cache_updates) > 0, "Cache should be updated"
                            
                            # Find the cache update with emails field
                            email_updates = [u for u in cache_updates if 'emails' in u]
                            assert len(email_updates) > 0, "Should have email cache update"
                            
                            cache_data = email_updates[0]
                            
                            # Verify domain is correct
                            assert cache_data['domain'] == domain, \
                                f"Expected domain {domain}, got {cache_data['domain']}"
                            
                            # Verify emails field contains the discovered email
                            assert 'emails' in cache_data, "Cache should have emails field"
                            assert isinstance(cache_data['emails'], list), "Emails should be a list"
                            assert len(cache_data['emails']) > 0, "Emails list should not be empty"
                            
                            cached_email = cache_data['emails'][0]
                            assert cached_email['email'] == email, \
                                f"Expected email {email}, got {cached_email['email']}"
                            assert cached_email['source'] == success_method, \
                                f"Expected source {success_method}, got {cached_email['source']}"
                            assert cached_email['confidence'] == confidence, \
                                f"Expected confidence {confidence}, got {cached_email['confidence']}"
                            
                            # Verify last_checked was updated
                            assert 'last_checked' in cache_data, "Cache should have last_checked field"
                            assert cache_data['last_checked'] is not None, "last_checked should not be None"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")
    
    test_property_9_fallback_chain_execution_order()
    print("✓ Property test passed: Fallback Chain Execution Order")
    
    test_property_10_complete_failure_handling()
    print("✓ Property test passed: Complete Failure Handling")
    
    test_property_14_fallback_method_error_resilience()
    print("✓ Property test passed: Fallback Method Error Resilience")
    
    test_property_17_domain_level_cache_update()
    print("✓ Property test passed: Domain-Level Cache Update")



@settings(max_examples=100)
@given(
    domain=domains,
    company_name=company_names,
    cached_email=emails,
    cached_source=st.sampled_from(['hunter', 'pattern_guess', 'snov', 'scraped']),
    cached_confidence=st.integers(min_value=50, max_value=100)
)
def test_property_18_cache_first_discovery(domain, company_name, cached_email, cached_source, cached_confidence):
    """
    Feature: email-discovery-fallback-chain
    Property 18: Cache-First Discovery
    
    **Validates: Requirements 8.3, 8.4**
    
    For any email discovery attempt for a domain, the system shall check 
    company_domains.emails before executing any fallback methods, and if a 
    cached result exists, shall return the cached email without calling any 
    discovery methods.
    """
    # Track which methods were called
    methods_called = []
    
    # Mock methods to track calls
    def mock_hunter(d):
        methods_called.append('hunter')
        return None
    
    def mock_pattern_gen(d):
        methods_called.append('pattern')
        return []
    
    def mock_snov(d):
        methods_called.append('snov')
        return None
    
    def mock_scraper(d):
        methods_called.append('scraper')
        return None
    
    # Mock database with cached result
    with patch('pipeline.email_discovery.db') as mock_db:
        # Mock cache hit with cached email
        mock_db.client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{
            'domain': domain,
            'emails': [{
                'email': cached_email,
                'source': cached_source,
                'confidence': cached_confidence,
                'recruiter_name': None
            }],
            'last_checked': '2024-01-01T00:00:00Z'
        }]
        mock_db.log_event = MagicMock()
        
        with patch('pipeline.email_discovery.search_domain_for_email', side_effect=mock_hunter):
            with patch('pipeline.email_discovery.generate_pattern_candidates', side_effect=mock_pattern_gen):
                with patch('pipeline.email_discovery.search_snov_domain', side_effect=mock_snov):
                    with patch('pipeline.email_discovery.scrape_domain_for_email', side_effect=mock_scraper):
                        # Execute discovery
                        result = discover_email_with_fallback(domain, company_name)
                        
                        # Verify result is from cache
                        assert result is not None, "Should return cached result"
                        assert result.email == cached_email, \
                            f"Expected cached email {cached_email}, got {result.email}"
                        assert result.source == cached_source, \
                            f"Expected cached source {cached_source}, got {result.source}"
                        assert result.confidence == cached_confidence, \
                            f"Expected cached confidence {cached_confidence}, got {result.confidence}"
                        
                        # Verify NO discovery methods were called
                        assert len(methods_called) == 0, \
                            f"No discovery methods should be called with cache hit, but {methods_called} were called"
                        
                        # Verify cache_hit event was logged
                        cache_hit_logs = [call for call in mock_db.log_event.call_args_list 
                                        if len(call[0]) > 1 and call[0][1] == "email_discovery_cache_hit"]
                        assert len(cache_hit_logs) > 0, "Should log cache_hit event"


if __name__ == "__main__":
    # Run the property tests
    test_property_2_pattern_validation_and_selection()
    print("✓ Property test passed: Pattern Validation and Selection")
    
    test_property_2_pattern_validation_all_fail()
    print("✓ Property test passed: Pattern Validation All Fail")
    
    test_property_3_fallback_chain_short_circuit()
    print("✓ Property test passed: Fallback Chain Short-Circuit")
    
    test_property_9_fallback_chain_execution_order()
    print("✓ Property test passed: Fallback Chain Execution Order")
    
    test_property_10_complete_failure_handling()
    print("✓ Property test passed: Complete Failure Handling")
    
    test_property_14_fallback_method_error_resilience()
    print("✓ Property test passed: Fallback Method Error Resilience")
    
    test_property_17_domain_level_cache_update()
    print("✓ Property test passed: Domain-Level Cache Update")
    
    test_property_18_cache_first_discovery()
    print("✓ Property test passed: Cache-First Discovery")
