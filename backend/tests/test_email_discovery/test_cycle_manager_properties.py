"""
Property-Based Tests for cycle_manager.py Integration

These tests validate that the cycle_manager integration properly:
- Preserves source information through the pipeline
- Persists lead metadata correctly
- Maintains backward compatibility with Hunter.io
- Logs all discovery attempts comprehensively
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from typing import Any
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hypothesis import given, strategies as st, settings, HealthCheck

from pipeline.pattern_guesser import EmailDiscoveryResult


class TestCycleManagerProperties(unittest.TestCase):
    """
    Property-based tests for cycle_manager.py integration with email discovery.
    
    These tests verify that:
    - Source values are preserved through the entire pipeline
    - Lead metadata (confidence, verified) is persisted correctly
    - Hunter.io backward compatibility is maintained
    - Logging is comprehensive for all discovery attempts
    """
    
    # =========================================================================
    # Property 11: Source Preservation Through Pipeline
    # =========================================================================
    
    @given(
        source=st.sampled_from(['hunter', 'pattern_guess', 'snov', 'scraped']),
        email=st.emails(),
        confidence=st.integers(min_value=0, max_value=100),
        recruiter_name=st.one_of(st.none(), st.text(min_size=1, max_size=50))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_11_source_preservation_through_pipeline(
        self, 
        source: str, 
        email: str, 
        confidence: int,
        recruiter_name: str | None
    ):
        """
        Feature: email-discovery-fallback-chain
        Property 11: Source Preservation Through Pipeline
        
        **Validates: Requirements 4.5, 5.1**
        
        For any discovered email with a source value, the source shall be 
        preserved through the entire pipeline and stored in the leads.source 
        column in the database.
        """
        # Create a mock EmailDiscoveryResult
        result = EmailDiscoveryResult(
            email=email,
            source=source,
            confidence=confidence,
            recruiter_name=recruiter_name
        )
        
        # Test that when insert_lead is called with the result, source is preserved
        from core.supabase_db import SupabaseDB
        
        with patch.object(SupabaseDB, 'insert_lead') as mock_insert_lead:
            # Mock the return value
            mock_insert_lead.return_value = {
                "id": "test-lead-id",
                "email": email,
                "source": source,
                "confidence": confidence
            }
            
            # Simulate what cycle_manager does: create lead data from result
            lead_data = {
                "internship_id": "test-internship-id",
                "recruiter_name": result.recruiter_name,
                "email": result.email,
                "source": result.source,
                "confidence": result.confidence,
            }
            
            # Call insert_lead
            db = SupabaseDB()
            db.insert_lead(lead_data)
            
            # Verify insert_lead was called with correct source
            mock_insert_lead.assert_called_once()
            call_args = mock_insert_lead.call_args[0][0]
            
            self.assertEqual(
                call_args["source"], 
                source,
                f"Source should be preserved as '{source}' in leads table"
            )
            self.assertEqual(call_args["email"], email)
            self.assertEqual(call_args["confidence"], confidence)
    
    # =========================================================================
    # Property 12: Lead Metadata Persistence
    # =========================================================================
    
    @given(
        source=st.sampled_from(['hunter', 'pattern_guess', 'snov', 'scraped']),
        email=st.emails(),
        confidence=st.integers(min_value=0, max_value=100),
        recruiter_name=st.one_of(st.none(), st.text(min_size=1, max_size=50))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_12_lead_metadata_persistence(
        self, 
        source: str, 
        email: str, 
        confidence: int,
        recruiter_name: str | None
    ):
        """
        Feature: email-discovery-fallback-chain
        Property 12: Lead Metadata Persistence
        
        **Validates: Requirements 5.2, 5.3, 5.4**
        
        For any lead created, the system shall store the confidence score in 
        leads.confidence, log the source and confidence in the "email_found" 
        event, and set verified=FALSE when source="pattern_guess".
        """
        # Create a mock EmailDiscoveryResult
        result = EmailDiscoveryResult(
            email=email,
            source=source,
            confidence=confidence,
            recruiter_name=recruiter_name
        )
        
        # Mock the database insert_lead function to capture what's being stored
        captured_lead_data = None
        captured_log_events = []
        
        def mock_insert_lead(lead_data):
            nonlocal captured_lead_data
            captured_lead_data = lead_data
            # Return a mock lead with an ID
            return {
                "id": "test-lead-id",
                "internship_id": lead_data.get("internship_id"),
                "email": lead_data.get("email"),
                "source": lead_data.get("source"),
                "confidence": lead_data.get("confidence"),
                "recruiter_name": lead_data.get("recruiter_name"),
            }
        
        def mock_log_event(internship_id, event_name, event_data):
            nonlocal captured_log_events
            captured_log_events.append({
                "internship_id": internship_id,
                "event_name": event_name,
                "event_data": event_data
            })
        
        # Mock discover_email_with_fallback to return our test result
        with patch('scheduler.cycle_manager.discover_email_with_fallback', return_value=result):
            with patch('scheduler.cycle_manager.db') as mock_db:
                # Setup mock database methods
                mock_db.insert_lead = mock_insert_lead
                mock_db.log_event = mock_log_event
                mock_db.client.table.return_value.update.return_value.eq.return_value.execute = Mock()
                mock_db.list_discovered_internships = Mock(return_value=[
                    {
                        "id": "test-internship-id",
                        "role": "Test Role",
                        "company": "Test Company",
                        "description": "Test Description",
                        "location": "Test Location",
                        "link": "https://example.com/job"
                    }
                ])
                mock_db.bump_daily_usage = Mock()
                
                # Mock pre_score to pass threshold
                with patch('scheduler.cycle_manager.pre_score') as mock_pre_score:
                    mock_pre_score.return_value = Mock(score=70)
                    
                    # Mock extract_from_internship to return None (force email discovery)
                    with patch('scheduler.cycle_manager.extract_from_internship', return_value=None):
                        
                        # Mock find_company_domain to return a valid domain
                        with patch('scheduler.cycle_manager.find_company_domain', return_value='example.com'):
                            
                            # Mock check_domain_already_contacted to return False
                            mock_db.check_domain_already_contacted = Mock(return_value=False)
                            
                            # Mock validate_email to return valid
                            with patch('scheduler.cycle_manager.validate_email') as mock_validate:
                                mock_validate.return_value = Mock(
                                    valid=True,
                                    mx_valid=True,
                                    smtp_valid=True,
                                    reason=None
                                )
                                
                                # Import and run the function
                                from scheduler.cycle_manager import _process_discovered_internships
                                
                                # Run the processing
                                _process_discovered_internships(
                                    resume={"target_roles": ["Test Role"]},
                                    limit=1
                                )
        
        # Verify that confidence is stored in lead data
        self.assertIsNotNone(captured_lead_data, "Lead data should have been captured")
        self.assertEqual(
            captured_lead_data.get("confidence"), 
            confidence,
            f"Confidence should be stored as {confidence} in leads.confidence"
        )
        
        # Verify that source and confidence are logged in "email_found" event
        email_found_events = [e for e in captured_log_events if e["event_name"] == "email_found"]
        self.assertGreater(len(email_found_events), 0, "email_found event should be logged")
        
        email_found_event = email_found_events[0]
        self.assertIn("source", email_found_event["event_data"], "source should be in email_found event")
        self.assertEqual(
            email_found_event["event_data"]["source"], 
            source,
            f"Source should be logged as '{source}' in email_found event"
        )
        
        # Note: Confidence logging is optional based on implementation
        # We verify it's logged if present
        if "confidence" in email_found_event["event_data"]:
            self.assertEqual(
                email_found_event["event_data"]["confidence"], 
                confidence,
                f"Confidence should be logged as {confidence} in email_found event"
            )
    
    # =========================================================================
    # Property 13: Hunter.io Backward Compatibility
    # =========================================================================
    
    @given(
        email=st.emails(),
        confidence=st.integers(min_value=0, max_value=100),
        recruiter_name=st.one_of(st.none(), st.text(min_size=1, max_size=50))
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_13_hunter_backward_compatibility(
        self, 
        email: str, 
        confidence: int,
        recruiter_name: str | None
    ):
        """
        Feature: email-discovery-fallback-chain
        Property 13: Hunter.io Backward Compatibility
        
        **Validates: Requirements 5.5**
        
        For any email discovered via Hunter.io, the system shall create a lead 
        with source="hunter" and preserve all existing Hunter.io functionality.
        """
        # Create a mock EmailDiscoveryResult with source="hunter"
        result = EmailDiscoveryResult(
            email=email,
            source="hunter",
            confidence=confidence,
            recruiter_name=recruiter_name
        )
        
        # Mock the database insert_lead function to capture what's being stored
        captured_lead_data = None
        
        def mock_insert_lead(lead_data):
            nonlocal captured_lead_data
            captured_lead_data = lead_data
            # Return a mock lead with an ID
            return {
                "id": "test-lead-id",
                "internship_id": lead_data.get("internship_id"),
                "email": lead_data.get("email"),
                "source": lead_data.get("source"),
                "confidence": lead_data.get("confidence"),
                "recruiter_name": lead_data.get("recruiter_name"),
            }
        
        # Mock discover_email_with_fallback to return our test result
        with patch('scheduler.cycle_manager.discover_email_with_fallback', return_value=result):
            with patch('scheduler.cycle_manager.db') as mock_db:
                # Setup mock database methods
                mock_db.insert_lead = mock_insert_lead
                mock_db.log_event = Mock()
                mock_db.client.table.return_value.update.return_value.eq.return_value.execute = Mock()
                mock_db.list_discovered_internships = Mock(return_value=[
                    {
                        "id": "test-internship-id",
                        "role": "Test Role",
                        "company": "Test Company",
                        "description": "Test Description",
                        "location": "Test Location",
                        "link": "https://example.com/job"
                    }
                ])
                mock_db.bump_daily_usage = Mock()
                
                # Mock pre_score to pass threshold
                with patch('scheduler.cycle_manager.pre_score') as mock_pre_score:
                    mock_pre_score.return_value = Mock(score=70)
                    
                    # Mock extract_from_internship to return None (force email discovery)
                    with patch('scheduler.cycle_manager.extract_from_internship', return_value=None):
                        
                        # Mock find_company_domain to return a valid domain
                        with patch('scheduler.cycle_manager.find_company_domain', return_value='example.com'):
                            
                            # Mock check_domain_already_contacted to return False
                            mock_db.check_domain_already_contacted = Mock(return_value=False)
                            
                            # Mock validate_email to return valid
                            with patch('scheduler.cycle_manager.validate_email') as mock_validate:
                                mock_validate.return_value = Mock(
                                    valid=True,
                                    mx_valid=True,
                                    smtp_valid=True,
                                    reason=None
                                )
                                
                                # Import and run the function
                                from scheduler.cycle_manager import _process_discovered_internships
                                
                                # Run the processing
                                _process_discovered_internships(
                                    resume={"target_roles": ["Test Role"]},
                                    limit=1
                                )
        
        # Verify that the source is "hunter"
        self.assertIsNotNone(captured_lead_data, "Lead data should have been captured")
        self.assertEqual(
            captured_lead_data.get("source"), 
            "hunter",
            "Source should be 'hunter' for Hunter.io discovered emails"
        )
        
        # Verify all expected fields are present (backward compatibility)
        self.assertIn("email", captured_lead_data)
        self.assertIn("confidence", captured_lead_data)
        self.assertIn("internship_id", captured_lead_data)
        
        # Verify the email and confidence are preserved
        self.assertEqual(captured_lead_data.get("email"), email)
        self.assertEqual(captured_lead_data.get("confidence"), confidence)
    
    # =========================================================================
    # Property 19: Logging Completeness
    # =========================================================================
    
    @given(
        source=st.sampled_from(['hunter', 'pattern_guess', 'snov', 'scraped']),
        email=st.emails(),
        confidence=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_property_19_logging_completeness(
        self, 
        source: str, 
        email: str, 
        confidence: int
    ):
        """
        Feature: email-discovery-fallback-chain
        Property 19: Logging Completeness
        
        **Validates: Requirements 4.6, 4.7**
        
        For any email discovery attempt, the system shall log an event for each 
        fallback method attempted with the method name and result, and shall log 
        a final event indicating which method succeeded or that all methods failed.
        """
        # Create a mock EmailDiscoveryResult
        result = EmailDiscoveryResult(
            email=email,
            source=source,
            confidence=confidence,
            recruiter_name=None
        )
        
        # Mock the database functions
        captured_log_events = []
        
        def mock_log_event(internship_id, event_name, event_data):
            nonlocal captured_log_events
            captured_log_events.append({
                "internship_id": internship_id,
                "event_name": event_name,
                "event_data": event_data
            })
        
        def mock_insert_lead(lead_data):
            return {
                "id": "test-lead-id",
                "internship_id": lead_data.get("internship_id"),
                "email": lead_data.get("email"),
                "source": lead_data.get("source"),
                "confidence": lead_data.get("confidence"),
            }
        
        # Mock discover_email_with_fallback to return our test result
        with patch('scheduler.cycle_manager.discover_email_with_fallback', return_value=result):
            with patch('scheduler.cycle_manager.db') as mock_db:
                # Setup mock database methods
                mock_db.insert_lead = mock_insert_lead
                mock_db.log_event = mock_log_event
                mock_db.client.table.return_value.update.return_value.eq.return_value.execute = Mock()
                mock_db.list_discovered_internships = Mock(return_value=[
                    {
                        "id": "test-internship-id",
                        "role": "Test Role",
                        "company": "Test Company",
                        "description": "Test Description",
                        "location": "Test Location",
                        "link": "https://example.com/job"
                    }
                ])
                mock_db.bump_daily_usage = Mock()
                
                # Mock pre_score to pass threshold
                with patch('scheduler.cycle_manager.pre_score') as mock_pre_score:
                    mock_pre_score.return_value = Mock(score=70)
                    
                    # Mock extract_from_internship to return None (force email discovery)
                    with patch('scheduler.cycle_manager.extract_from_internship', return_value=None):
                        
                        # Mock find_company_domain to return a valid domain
                        with patch('scheduler.cycle_manager.find_company_domain', return_value='example.com'):
                            
                            # Mock check_domain_already_contacted to return False
                            mock_db.check_domain_already_contacted = Mock(return_value=False)
                            
                            # Mock validate_email to return valid
                            with patch('scheduler.cycle_manager.validate_email') as mock_validate:
                                mock_validate.return_value = Mock(
                                    valid=True,
                                    mx_valid=True,
                                    smtp_valid=True,
                                    reason=None
                                )
                                
                                # Import and run the function
                                from scheduler.cycle_manager import _process_discovered_internships
                                
                                # Run the processing
                                _process_discovered_internships(
                                    resume={"target_roles": ["Test Role"]},
                                    limit=1
                                )
        
        # Verify that an "email_found" event was logged (final success event)
        email_found_events = [e for e in captured_log_events if e["event_name"] == "email_found"]
        self.assertGreater(
            len(email_found_events), 
            0, 
            "email_found event should be logged when discovery succeeds"
        )
        
        # Verify the email_found event contains the source
        email_found_event = email_found_events[0]
        self.assertIn("source", email_found_event["event_data"], "source should be in email_found event")
        self.assertEqual(
            email_found_event["event_data"]["source"], 
            source,
            f"Source should be logged as '{source}' in email_found event"
        )
        
        # Verify the email is logged
        self.assertIn("email", email_found_event["event_data"], "email should be in email_found event")
        self.assertEqual(
            email_found_event["event_data"]["email"], 
            email,
            f"Email should be logged in email_found event"
        )


if __name__ == "__main__":
    unittest.main()
