"""
Property-based tests for snov_client.py module.

Feature: email-discovery-fallback-chain
"""

from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.snov_client import search_snov_domain


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

# Email strategy: generate valid email addresses
emails = st.emails()

# Confidence score strategy: 0-100
confidence_scores = st.integers(min_value=0, max_value=100)


@settings(max_examples=100)
@given(
    domain=domains,
    email=emails,
    confidence=confidence_scores
)
def test_property_4_snov_authentication_and_search_sequence(domain, email, confidence):
    """
    Feature: email-discovery-fallback-chain
    Property 4: Snov.io Authentication and Search Sequence
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    
    For any domain search via Snov.io, the client shall first authenticate 
    using environment variables SNOV_CLIENT_ID and SNOV_CLIENT_SECRET, then 
    call the domain search endpoint with the domain parameter, and return 
    the email with the highest confidence score marked with source="snov".
    """
    # Track the order of API calls
    call_order = []
    
    # Mock authentication function
    def mock_auth_post(*args, **kwargs):
        # Check if this is the authentication endpoint
        if "oauth/access_token" in str(args):
            call_order.append("auth")
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "test_token_123"}
            mock_response.raise_for_status = MagicMock()
            return mock_response
        # Otherwise it's the domain search endpoint
        else:
            call_order.append("search")
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "emails": [
                    {"email": email, "confidence": confidence}
                ]
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response
    
    # Patch environment variables and httpx.post
    with patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_client_id",
        "SNOV_CLIENT_SECRET": "test_client_secret"
    }):
        with patch('pipeline.snov_client.httpx.post', side_effect=mock_auth_post) as mock_post:
            # Execute domain search
            result = search_snov_domain(domain)
            
            # Verify authentication happened before search
            assert len(call_order) == 2, f"Expected 2 API calls, got {len(call_order)}"
            assert call_order[0] == "auth", "Authentication should happen first"
            assert call_order[1] == "search", "Domain search should happen second"
            
            # Verify result has correct structure
            assert result is not None, "Result should not be None"
            assert result.email == email, f"Expected email {email}, got {result.email}"
            assert result.source == "snov", f"Expected source 'snov', got {result.source}"
            assert result.confidence == confidence, f"Expected confidence {confidence}, got {result.confidence}"
            assert result.recruiter_name is None, "recruiter_name should be None"
            
            # Verify authentication endpoint was called with correct parameters
            auth_call = [call for call in mock_post.call_args_list if "oauth" in str(call)][0]
            auth_json = auth_call[1]['json']
            assert auth_json['client_id'] == "test_client_id"
            assert auth_json['client_secret'] == "test_client_secret"
            assert auth_json['grant_type'] == "client_credentials"
            
            # Verify domain search endpoint was called with correct parameters
            search_call = [call for call in mock_post.call_args_list if "domain-emails" in str(call)][0]
            search_json = search_call[1]['json']
            assert search_json['domain'] == domain
            
            # Verify Authorization header was included in search request
            search_headers = search_call[1].get('headers', {})
            assert 'Authorization' in search_headers
            assert search_headers['Authorization'] == "Bearer test_token_123"


@settings(max_examples=100)
@given(
    domain=domains,
    emails_data=st.lists(
        st.tuples(emails, confidence_scores),
        min_size=2,
        max_size=10
    )
)
def test_property_4_highest_confidence_email_selection(domain, emails_data):
    """
    Feature: email-discovery-fallback-chain
    Property 4: Snov.io Authentication and Search Sequence (Highest Confidence Selection)
    
    **Validates: Requirements 2.4, 2.5**
    
    When Snov.io returns multiple emails, the client shall select the email 
    with the highest confidence score and return it with source="snov".
    """
    # Find the email with highest confidence
    expected_email, expected_confidence = max(emails_data, key=lambda x: x[1])
    
    # Mock authentication and search responses
    def mock_post(*args, **kwargs):
        if "oauth/access_token" in str(args):
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "test_token"}
            mock_response.raise_for_status = MagicMock()
            return mock_response
        else:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "emails": [
                    {"email": email, "confidence": conf}
                    for email, conf in emails_data
                ]
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response
    
    # Execute test
    with patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_id",
        "SNOV_CLIENT_SECRET": "test_secret"
    }):
        with patch('pipeline.snov_client.httpx.post', side_effect=mock_post):
            result = search_snov_domain(domain)
            
            # Verify highest confidence email was selected
            assert result is not None
            assert result.email == expected_email, \
                f"Expected email with highest confidence {expected_email}, got {result.email}"
            assert result.confidence == expected_confidence, \
                f"Expected confidence {expected_confidence}, got {result.confidence}"
            assert result.source == "snov"


if __name__ == "__main__":
    # Run the property tests
    test_property_4_snov_authentication_and_search_sequence()
    print("✓ Property test passed: Snov.io Authentication and Search Sequence")
    
    test_property_4_highest_confidence_email_selection()
    print("✓ Property test passed: Highest Confidence Email Selection")


@settings(max_examples=100)
@given(domain=domains)
def test_property_5_snov_error_handling_auth_failure(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 5: Snov.io Error Handling (Authentication Failure)
    
    **Validates: Requirements 2.7, 2.8**
    
    For any Snov.io authentication failure, the client shall log the error 
    and return None without raising an exception.
    """
    # Mock authentication failure with HTTP error
    def mock_auth_failure(*args, **kwargs):
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        raise httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=mock_response)
    
    with patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_id",
        "SNOV_CLIENT_SECRET": "test_secret"
    }):
        with patch('pipeline.snov_client.httpx.post', side_effect=mock_auth_failure):
            # Should not raise exception
            result = search_snov_domain(domain)
            
            # Should return None
            assert result is None, "Authentication failure should return None"


@settings(max_examples=100)
@given(domain=domains)
def test_property_5_snov_error_handling_api_failure(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 5: Snov.io Error Handling (API Call Failure)
    
    **Validates: Requirements 2.7, 2.8**
    
    For any Snov.io API call failure, the client shall log the error 
    and return None without raising an exception.
    """
    call_count = [0]
    
    def mock_api_failure(*args, **kwargs):
        call_count[0] += 1
        # First call is auth (succeeds), second call is domain search (fails)
        if call_count[0] == 1:
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "test_token"}
            mock_response.raise_for_status = MagicMock()
            return mock_response
        else:
            import httpx
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            raise httpx.HTTPStatusError("500 Error", request=MagicMock(), response=mock_response)
    
    with patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_id",
        "SNOV_CLIENT_SECRET": "test_secret"
    }):
        with patch('pipeline.snov_client.httpx.post', side_effect=mock_api_failure):
            # Should not raise exception
            result = search_snov_domain(domain)
            
            # Should return None
            assert result is None, "API call failure should return None"


@settings(max_examples=100)
@given(domain=domains)
def test_property_5_snov_error_handling_network_error(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 5: Snov.io Error Handling (Network Error)
    
    **Validates: Requirements 2.7, 2.8**
    
    For any network error during Snov.io calls, the client shall log the error 
    and return None without raising an exception.
    """
    def mock_network_error(*args, **kwargs):
        import httpx
        raise httpx.RequestError("Connection timeout")
    
    with patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_id",
        "SNOV_CLIENT_SECRET": "test_secret"
    }):
        with patch('pipeline.snov_client.httpx.post', side_effect=mock_network_error):
            # Should not raise exception
            result = search_snov_domain(domain)
            
            # Should return None
            assert result is None, "Network error should return None"


@settings(max_examples=100)
@given(domain=domains)
def test_property_15_snov_graceful_degradation_missing_client_id(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 15: Snov.io Graceful Degradation (Missing Client ID)
    
    **Validates: Requirements 6.3, 7.3**
    
    For any Snov.io client call when SNOV_CLIENT_ID is missing, the client 
    shall log a warning and return None without raising an exception.
    """
    # Clear environment variables to simulate missing SNOV_CLIENT_ID
    with patch.dict(os.environ, {}, clear=True):
        # Should not raise exception
        result = search_snov_domain(domain)
        
        # Should return None
        assert result is None, "Missing SNOV_CLIENT_ID should return None"


@settings(max_examples=100)
@given(domain=domains)
def test_property_15_snov_graceful_degradation_missing_client_secret(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 15: Snov.io Graceful Degradation (Missing Client Secret)
    
    **Validates: Requirements 6.3, 7.3**
    
    For any Snov.io client call when SNOV_CLIENT_SECRET is missing, the client 
    shall log a warning and return None without raising an exception.
    """
    # Set only SNOV_CLIENT_ID, leave SNOV_CLIENT_SECRET missing
    with patch.dict(os.environ, {"SNOV_CLIENT_ID": "test_id"}, clear=True):
        # Should not raise exception
        result = search_snov_domain(domain)
        
        # Should return None
        assert result is None, "Missing SNOV_CLIENT_SECRET should return None"


@settings(max_examples=100)
@given(domain=domains)
def test_property_15_snov_graceful_degradation_both_missing(domain):
    """
    Feature: email-discovery-fallback-chain
    Property 15: Snov.io Graceful Degradation (Both Credentials Missing)
    
    **Validates: Requirements 6.3, 7.3**
    
    For any Snov.io client call when both environment variables are missing, 
    the client shall log a warning and return None without raising an exception.
    """
    # Clear all environment variables
    with patch.dict(os.environ, {}, clear=True):
        # Should not raise exception
        result = search_snov_domain(domain)
        
        # Should return None
        assert result is None, "Missing both credentials should return None"


if __name__ == "__main__":
    # Run the property tests
    test_property_4_snov_authentication_and_search_sequence()
    print("✓ Property test passed: Snov.io Authentication and Search Sequence")
    
    test_property_4_highest_confidence_email_selection()
    print("✓ Property test passed: Highest Confidence Email Selection")
    
    test_property_5_snov_error_handling_auth_failure()
    print("✓ Property test passed: Snov.io Error Handling - Auth Failure")
    
    test_property_5_snov_error_handling_api_failure()
    print("✓ Property test passed: Snov.io Error Handling - API Failure")
    
    test_property_5_snov_error_handling_network_error()
    print("✓ Property test passed: Snov.io Error Handling - Network Error")
    
    test_property_15_snov_graceful_degradation_missing_client_id()
    print("✓ Property test passed: Snov.io Graceful Degradation - Missing Client ID")
    
    test_property_15_snov_graceful_degradation_missing_client_secret()
    print("✓ Property test passed: Snov.io Graceful Degradation - Missing Client Secret")
    
    test_property_15_snov_graceful_degradation_both_missing()
    print("✓ Property test passed: Snov.io Graceful Degradation - Both Missing")
