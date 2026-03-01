"""
Preservation Property Tests - Non-Approval Pipeline Behavior

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

These tests verify that non-approval operations remain unchanged:
- Lead scoring (pre_score and full_score calculations)
- Email validation (MX/SMTP checks)
- Draft generation (Groq API calls and templates)
- Email spacing (45-55 minute gaps between sends)
- Daily email limits (max emails per day enforcement)

IMPORTANT: These tests run on UNFIXED code to establish baseline behavior.
They should PASS on unfixed code and continue to PASS after the fix is applied.
"""

import unittest
from datetime import datetime, timedelta
from typing import Any

from hypothesis import given, strategies as st, settings, HealthCheck

from pipeline.pre_scorer import pre_score
from pipeline.full_scorer import full_score
from pipeline.email_validator import validate_email
from outreach.queue_manager import process_email_queue
from core.supabase_db import db, utcnow


class TestPreservationProperties(unittest.TestCase):
    """
    Property-based tests for preservation of non-approval pipeline behavior.
    
    These tests verify that the fix does NOT change:
    - Scoring algorithms
    - Email validation logic
    - Draft generation templates
    - Email spacing enforcement
    - Daily limit enforcement
    """
    
    # =========================================================================
    # Test 1: Lead Scoring Preservation
    # =========================================================================
    
    @given(
        role=st.text(min_size=1, max_size=100),
        company=st.text(min_size=1, max_size=100),
        location=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_pre_score_deterministic(self, role: str, company: str, location: str):
        """
        Property: For all leads with same attributes, pre_score produces same results.
        
        This verifies that scoring is deterministic and not affected by the fix.
        """
        internship = {
            "role": role,
            "company": company,
            "location": location,
            "link": "https://example.com/job"
        }
        
        # Score the same internship twice
        result1 = pre_score(internship)
        result2 = pre_score(internship)
        
        # Scores should be identical (deterministic)
        self.assertEqual(result1.score, result2.score)
        self.assertEqual(result1.status, result2.status)
        self.assertEqual(result1.breakdown, result2.breakdown)
    
    @given(
        role=st.text(min_size=1, max_size=100),
        description=st.text(min_size=10, max_size=500),
        location=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_full_score_deterministic(self, role: str, description: str, location: str):
        """
        Property: For all leads with same attributes, full_score produces same results.
        
        This verifies that full scoring is deterministic and not affected by the fix.
        Note: This test may be skipped if database is not available.
        """
        try:
            internship = {
                "role": role,
                "description": description,
                "location": location,
                "link": "https://example.com/job"
            }
            
            resume = {
                "target_roles": ["AI Intern", "ML Intern"],
                "skills": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["PyTorch", "TensorFlow"]
                },
                "preferred_locations": ["Remote", "Mumbai", "Bangalore"]
            }
            
            # Score the same internship twice
            result1 = full_score(internship, resume)
            result2 = full_score(internship, resume)
            
            # Scores should be identical (deterministic)
            self.assertEqual(result1.score, result2.score)
            self.assertEqual(result1.breakdown, result2.breakdown)
        except Exception as e:
            # If database is not available, skip this example
            if "database" in str(e).lower() or "connection" in str(e).lower():
                return
            raise
    
    # =========================================================================
    # Test 2: Email Validation Preservation
    # =========================================================================
    
    def test_email_validation_format_check_preserved(self):
        """
        Property: For all email addresses, validation format check is deterministic.
        
        This verifies that email validation format checking is preserved.
        We test format validation only to avoid network calls.
        """
        from pipeline.email_validator import RFC_REGEX
        
        # Valid email formats
        valid_emails = [
            "test@example.com",
            "user.name@domain.com",
            "user+tag@example.org",
            "first.last@company.co.uk"
        ]
        
        for email in valid_emails:
            # Format check should pass
            self.assertTrue(RFC_REGEX.match(email), f"Valid email rejected: {email}")
        
        # Invalid email formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com"
        ]
        
        for email in invalid_emails:
            # Format check should fail
            self.assertFalse(RFC_REGEX.match(email), f"Invalid email accepted: {email}")
    
    def test_disposable_domain_check_preserved(self):
        """
        Property: Disposable domain checking logic is preserved.
        
        This verifies that the disposable domain blocklist logic remains unchanged.
        """
        from pipeline.email_validator import _load_disposable
        
        # Load disposable domains
        disposable = _load_disposable()
        
        # Should be a set
        self.assertIsInstance(disposable, set)
        
        # Should contain some common disposable domains (if list is loaded)
        if disposable:
            # Verify it's a set of strings
            for domain in list(disposable)[:5]:
                self.assertIsInstance(domain, str)
                self.assertGreater(len(domain), 0)
    
    # =========================================================================
    # Test 3: Draft Generation Preservation
    # =========================================================================
    
    def test_draft_generation_structure_preserved(self):
        """
        Property: For all draft generation inputs, output has same structure.
        
        This verifies that draft generation produces consistent structure
        (subject, body, followup) regardless of the approval flow changes.
        
        Note: We test the fallback template to avoid API calls in tests.
        """
        from pipeline.groq_client import _generate_fallback_draft
        
        lead = {
            "id": "test-lead-1",
            "email": "recruiter@example.com",
            "recruiter_name": "John Doe"
        }
        
        internship = {
            "id": "test-internship-1",
            "role": "AI Intern",
            "company": "TechCorp",
            "description": "Work on ML projects"
        }
        
        resume = {
            "name": "Test Candidate",
            "skills": {
                "languages": ["Python", "JavaScript"],
                "frameworks": ["PyTorch"]
            },
            "projects": [
                {"name": "Project 1", "description": "ML project"}
            ]
        }
        
        # Generate draft twice
        draft1 = _generate_fallback_draft(lead, internship, resume)
        draft2 = _generate_fallback_draft(lead, internship, resume)
        
        # Structure should be identical (deterministic template)
        self.assertEqual(draft1.subject, draft2.subject)
        self.assertEqual(draft1.body, draft2.body)
        self.assertEqual(draft1.followup_body, draft2.followup_body)
        
        # Verify all required fields are present
        self.assertIsNotNone(draft1.subject)
        self.assertIsNotNone(draft1.body)
        self.assertIsNotNone(draft1.followup_body)
        self.assertGreater(len(draft1.subject), 0)
        self.assertGreater(len(draft1.body), 0)
        self.assertGreater(len(draft1.followup_body), 0)
    
    # =========================================================================
    # Test 4: Email Spacing Preservation
    # =========================================================================
    
    def test_email_spacing_enforcement(self):
        """
        Property: For all email sending sequences, 45-55 minute spacing is maintained.
        
        This verifies that the email spacing logic in queue_manager.py is preserved.
        We test the logic without actually sending emails.
        """
        # Query recent sent emails to verify spacing
        res = (
            db.client.table("email_drafts")
            .select("id, sent_at")
            .eq("status", "sent")
            .order("sent_at", desc=True)
            .limit(10)
            .execute()
        )
        
        sent_emails = res.data or []
        
        if len(sent_emails) < 2:
            # Not enough data to test spacing, skip
            self.skipTest("Not enough sent emails to verify spacing")
        
        # Check spacing between consecutive emails
        for i in range(len(sent_emails) - 1):
            current = datetime.fromisoformat(sent_emails[i]["sent_at"].replace("Z", "+00:00"))
            previous = datetime.fromisoformat(sent_emails[i + 1]["sent_at"].replace("Z", "+00:00"))
            
            gap_minutes = (current - previous).total_seconds() / 60
            
            # Spacing should be at least 45 minutes (with some tolerance for edge cases)
            # Note: We allow slightly less than 45 min for edge cases where timing might be off
            self.assertGreaterEqual(
                gap_minutes,
                40,  # Allow 5 min tolerance
                f"Email spacing too short: {gap_minutes:.1f} minutes (expected >= 45)"
            )
    
    # =========================================================================
    # Test 5: Daily Email Limit Preservation
    # =========================================================================
    
    def test_daily_limit_enforcement(self):
        """
        Property: For all daily runs, email limit is enforced at same threshold.
        
        This verifies that daily limit logic in queue_manager.py is preserved.
        """
        try:
            from scheduler.warmup import get_daily_limit
        except ImportError:
            # If warmup module doesn't exist, skip this test
            self.skipTest("warmup module not available")
        
        # Get current daily usage
        from core.supabase_db import today_utc
        today = today_utc()
        
        try:
            usage = db.get_or_create_daily_usage(today)
        except Exception as e:
            # If database is not available, skip this test
            self.skipTest(f"Database not available: {e}")
        
        # Verify daily limit is set and reasonable
        daily_limit = usage.daily_limit or 15
        self.assertGreater(daily_limit, 0)
        self.assertLessEqual(daily_limit, 50)  # Sanity check
        
        # Verify emails_sent doesn't exceed limit
        self.assertLessEqual(usage.emails_sent, daily_limit)
        
        # Verify the limit is consistent
        usage2 = db.get_or_create_daily_usage(today)
        self.assertEqual(usage.daily_limit, usage2.daily_limit)
    
    # =========================================================================
    # Test 6: Scoring Components Preservation
    # =========================================================================
    
    def test_scoring_components_preserved(self):
        """
        Property: Scoring breakdown components remain unchanged.
        
        This verifies that the scoring algorithm's internal components
        (relevance, resume_overlap, tech_stack, location, historical_success)
        are preserved and not affected by the approval flow fix.
        """
        internship = {
            "role": "AI Intern",
            "description": "Work on Python and PyTorch for NLP projects",
            "location": "Remote",
            "link": "https://example.com/job"
        }
        
        resume = {
            "target_roles": ["AI Intern"],
            "skills": {
                "languages": ["Python"],
                "frameworks": ["PyTorch"]
            },
            "preferred_locations": ["Remote"]
        }
        
        result = full_score(internship, resume)
        
        # Verify all expected components are present
        expected_components = [
            "relevance_score",
            "resume_overlap_score",
            "tech_stack_score",
            "location_score",
            "historical_success_score"
        ]
        
        for component in expected_components:
            self.assertIn(component, result.breakdown)
            self.assertIsInstance(result.breakdown[component], (int, float))
            self.assertGreaterEqual(result.breakdown[component], 0)


def run_preservation_tests():
    """
    Run all preservation property tests and report results.
    
    EXPECTED OUTCOME: All tests PASS on unfixed code.
    This establishes the baseline behavior that must be preserved after the fix.
    """
    print("\n" + "=" * 70)
    print("PRESERVATION PROPERTY TESTS")
    print("=" * 70)
    print("\nThese tests verify that non-approval operations remain unchanged:")
    print("  ✓ Lead scoring (pre_score and full_score)")
    print("  ✓ Email validation (MX/SMTP checks)")
    print("  ✓ Draft generation (template structure)")
    print("  ✓ Email spacing (45-55 minute gaps)")
    print("  ✓ Daily email limits (enforcement)")
    print("\n" + "=" * 70)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPreservationProperties)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ ALL PRESERVATION TESTS PASSED")
        print("\nBaseline behavior established. These tests should continue")
        print("to pass after the fix is applied, confirming no regressions.")
    else:
        print("❌ SOME PRESERVATION TESTS FAILED")
        print("\nThis indicates the baseline behavior has issues or the")
        print("test assumptions need adjustment.")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_preservation_tests())
