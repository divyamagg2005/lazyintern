"""
Unit tests for snov_client.py module.

These tests validate the Snov.io authentication and domain search functionality
using mocked HTTP responses to avoid making real API calls.

Feature: email-discovery-fallback-chain
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 6.3, 7.1, 7.2, 7.3
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.snov_client import _get_snov_access_token, search_snov_domain, EmailDiscoveryResult


class TestSnovAuthenticationSuccess(unittest.TestCase):
    """Test successful Snov.io authentication scenarios."""
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_client_id",
        "SNOV_CLIENT_SECRET": "test_client_secret"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_successful_authentication(self, mock_post):
        """Test successful authentication returns access token."""
        # Mock successful authentication response
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        token = _get_snov_access_token()
        
        assert token == "test_access_token_123"
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "client_abc",
        "SNOV_CLIENT_SECRET": "secret_xyz"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_authentication_with_different_credentials(self, mock_post):
        """Test authentication with different credential values."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "different_token_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        token = _get_snov_access_token()
        
        assert token == "different_token_456"
        
        # Verify correct credentials were sent
        call_args = mock_post.call_args
        assert call_args[1]['json']['client_id'] == "client_abc"
        assert call_args[1]['json']['client_secret'] == "secret_xyz"


class TestSnovAuthenticationFailure(unittest.TestCase):
    """Test Snov.io authentication failure scenarios."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_client_id(self):
        """Test authentication fails gracefully when SNOV_CLIENT_ID is missing."""
        token = _get_snov_access_token()
        
        assert token is None
    
    @patch.dict(os.environ, {"SNOV_CLIENT_ID": "test_id"}, clear=True)
    def test_missing_client_secret(self):
        """Test authentication fails gracefully when SNOV_CLIENT_SECRET is missing."""
        token = _get_snov_access_token()
        
        assert token is None
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_client_id",
        "SNOV_CLIENT_SECRET": "test_client_secret"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_http_401_unauthorized(self, mock_post):
        """Test authentication handles 401 Unauthorized error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.side_effect = Exception("HTTP 401")
        
        token = _get_snov_access_token()
        
        assert token is None
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_client_id",
        "SNOV_CLIENT_SECRET": "test_client_secret"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_network_timeout(self, mock_post):
        """Test authentication handles network timeout."""
        mock_post.side_effect = Exception("Connection timeout")
        
        token = _get_snov_access_token()
        
        assert token is None
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_client_id",
        "SNOV_CLIENT_SECRET": "test_client_secret"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_missing_access_token_in_response(self, mock_post):
        """Test authentication handles response without access_token field."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        token = _get_snov_access_token()
        
        assert token is None


class TestSnovDomainSearchSuccess(unittest.TestCase):
    """Test successful Snov.io domain search scenarios."""
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_successful_domain_search_single_email(self, mock_post, mock_auth):
        """Test successful domain search with single email result."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [
                {"email": "hr@example.com", "confidence": 85}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result is not None
        assert result.email == "hr@example.com"
        assert result.source == "snov"
        assert result.confidence == 85
        assert result.recruiter_name is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_successful_domain_search_multiple_emails(self, mock_post, mock_auth):
        """Test domain search selects email with highest confidence."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [
                {"email": "info@example.com", "confidence": 60},
                {"email": "hr@example.com", "confidence": 95},
                {"email": "careers@example.com", "confidence": 75}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result is not None
        assert result.email == "hr@example.com"
        assert result.confidence == 95
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_with_data_field(self, mock_post, mock_auth):
        """Test domain search handles 'data' field instead of 'emails'."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"email": "contact@company.com", "confidence": 80}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("company.com")
        
        assert result is not None
        assert result.email == "contact@company.com"
        assert result.confidence == 80
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_with_value_field(self, mock_post, mock_auth):
        """Test domain search handles 'value' field instead of 'email'."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [
                {"value": "admin@test.com", "score": 70}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("test.com")
        
        assert result is not None
        assert result.email == "admin@test.com"
        assert result.confidence == 70


class TestSnovDomainSearchFailure(unittest.TestCase):
    """Test Snov.io domain search failure scenarios."""
    
    @patch('pipeline.snov_client._get_snov_access_token')
    def test_domain_search_authentication_failure(self, mock_auth):
        """Test domain search returns None when authentication fails."""
        mock_auth.return_value = None
        
        result = search_snov_domain("example.com")
        
        assert result is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_no_results(self, mock_post, mock_auth):
        """Test domain search returns None when no emails found."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_http_error(self, mock_post, mock_auth):
        """Test domain search handles HTTP errors gracefully."""
        mock_auth.return_value = "test_token"
        mock_post.side_effect = Exception("HTTP 500")
        
        result = search_snov_domain("example.com")
        
        assert result is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_network_error(self, mock_post, mock_auth):
        """Test domain search handles network errors gracefully."""
        mock_auth.return_value = "test_token"
        mock_post.side_effect = Exception("Connection refused")
        
        result = search_snov_domain("example.com")
        
        assert result is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_invalid_email_data(self, mock_post, mock_auth):
        """Test domain search handles emails without email field."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [
                {"confidence": 80}  # Missing email field
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result is None


class TestSnovConfidenceScoreHandling(unittest.TestCase):
    """Test confidence score extraction and conversion."""
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_confidence_as_integer(self, mock_post, mock_auth):
        """Test confidence score as integer."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": 90}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.confidence == 90
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_confidence_as_string(self, mock_post, mock_auth):
        """Test confidence score as string gets converted to integer."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": "85"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.confidence == 85
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_confidence_as_float(self, mock_post, mock_auth):
        """Test confidence score as float gets converted to integer."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": 87.5}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.confidence == 87
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_missing_confidence_defaults_to_zero(self, mock_post, mock_auth):
        """Test missing confidence score defaults to 0."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.confidence == 0


class TestSnovResultMetadata(unittest.TestCase):
    """Test EmailDiscoveryResult metadata for Snov.io results."""
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_result_has_correct_source(self, mock_post, mock_auth):
        """Test result has source='snov'."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": 80}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.source == "snov"
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_result_has_no_recruiter_name(self, mock_post, mock_auth):
        """Test result has recruiter_name=None."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": 80}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert result.recruiter_name is None
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_result_is_email_discovery_result_type(self, mock_post, mock_auth):
        """Test result is EmailDiscoveryResult instance."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "emails": [{"email": "test@example.com", "confidence": 80}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = search_snov_domain("example.com")
        
        assert isinstance(result, EmailDiscoveryResult)


class TestSnovAPIEndpoints(unittest.TestCase):
    """Test that correct API endpoints are called."""
    
    @patch.dict(os.environ, {
        "SNOV_CLIENT_ID": "test_id",
        "SNOV_CLIENT_SECRET": "test_secret"
    })
    @patch('pipeline.snov_client.httpx.post')
    def test_authentication_endpoint(self, mock_post):
        """Test authentication calls correct endpoint."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        _get_snov_access_token()
        
        call_args = mock_post.call_args
        assert "https://api.snov.io/v1/oauth/access_token" in str(call_args)
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_endpoint(self, mock_post, mock_auth):
        """Test domain search calls correct endpoint."""
        mock_auth.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        search_snov_domain("example.com")
        
        call_args = mock_post.call_args
        assert "https://api.snov.io/v2/domain-emails-with-info" in str(call_args)
    
    @patch('pipeline.snov_client._get_snov_access_token')
    @patch('pipeline.snov_client.httpx.post')
    def test_domain_search_includes_authorization_header(self, mock_post, mock_auth):
        """Test domain search includes Bearer token in Authorization header."""
        mock_auth.return_value = "test_token_xyz"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"emails": []}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        search_snov_domain("example.com")
        
        call_args = mock_post.call_args
        headers = call_args[1].get('headers', {})
        assert headers.get('Authorization') == "Bearer test_token_xyz"


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSnovAuthenticationSuccess))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovAuthenticationFailure))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovDomainSearchSuccess))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovDomainSearchFailure))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovConfidenceScoreHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovResultMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestSnovAPIEndpoints))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
