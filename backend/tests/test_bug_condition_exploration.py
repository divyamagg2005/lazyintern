"""
Bug Condition Exploration Test for Auto-Approval Immediate Send Fix

**Validates: Requirements 2.1, 2.2**

This test is designed to FAIL on unfixed code to confirm the bug exists.
The bug: 2-hour approval delay prevents immediate email sending.

Expected behavior (after fix):
- When 5 leads are inserted, all 5 emails should be sent within one scheduler cycle
- Drafts should have status='approved' immediately (not 'generated')
- approved_at should be set to current time (not future time)

Current behavior (unfixed code - test will FAIL):
- Only 0-1 emails are sent in first cycle (not all 5)
- Drafts remain in status='generated' for 2+ hours
- approved_at is NULL or set to future time (current + 10-30 min)

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.
"""

import unittest
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from core.supabase_db import db, utcnow, today_utc
from scheduler.cycle_manager import _process_discovered_internships
from pipeline.pre_scorer import _load_resume


class TestBugConditionExploration(unittest.TestCase):
    """
    Bug Condition Exploration: Approval Delay Prevents Immediate Email Sending
    
    This test surfaces counterexamples demonstrating the 2-hour approval delay bug.
    It inserts 5 test leads and verifies only 0-1 emails are sent within one scheduler cycle.
    
    **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
    """
    
    def setUp(self):
        """Set up test data"""
        self.test_internship_ids = []
        self.test_lead_ids = []
        self.test_draft_ids = []
        
    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse order due to foreign key constraints
        for draft_id in self.test_draft_ids:
            try:
                db.client.table("email_drafts").delete().eq("id", draft_id).execute()
            except Exception:
                pass
        
        for lead_id in self.test_lead_ids:
            try:
                db.client.table("leads").delete().eq("id", lead_id).execute()
            except Exception:
                pass
        
        for internship_id in self.test_internship_ids:
            try:
                db.client.table("internships").delete().eq("id", internship_id).execute()
            except Exception:
                pass
    
    def _create_test_internship(self, index: int) -> dict[str, Any]:
        """Create a test internship with embedded email in description"""
        internship_id = str(uuid4())
        self.test_internship_ids.append(internship_id)
        
        # Use role titles that will score well (match high_priority keywords)
        roles = [
            "Software Engineer Intern - Remote India",
            "Machine Learning Intern - AI/ML",
            "Backend Developer Intern - Python",
            "Full Stack Developer Intern - Remote",
            "Data Science Intern - ML/AI"
        ]
        
        # Create internship with email in description (will be extracted by regex)
        internship_data = {
            "id": internship_id,
            "company": f"TechStartup{index}",
            "role": roles[index % len(roles)],
            "link": f"https://test-job-board.com/job/{internship_id}",
            "description": f"We are hiring for a great opportunity! "
                          f"Contact our HR team at hr{index}@techstartup{index}.com for more information. "
                          f"We are looking for talented interns to join our team in India. "
                          f"Skills: Python, Machine Learning, AI, Backend Development.",
            "location": "Remote",
            "status": "discovered",
            "pre_score": None,
            "full_score": None,
        }
        
        result = db.client.table("internships").insert(internship_data).execute()
        return result.data[0]
    
    def test_approval_delay_prevents_immediate_send(self):
        """
        Property 1: Fault Condition - Approval Delay Prevents Immediate Email Sending
        
        **Validates: Requirements 2.1, 2.2**
        
        Test that when multiple leads are inserted and drafts generated,
        emails are NOT sent immediately due to approval delays.
        
        Scoped PBT Approach: Insert 5 test leads and verify only 0-1 emails
        are sent within one scheduler cycle (not all 5).
        
        Assertions verify:
        - Drafts remain in status='generated' (not 'approved')
        - approved_at is either NULL or set to future time (current + 10-30 min)
        - Only 0-1 emails sent in first cycle
        
        **EXPECTED OUTCOME**: Test FAILS (confirms bug exists)
        
        Counterexamples to document:
        - How many emails were actually sent
        - What draft statuses were observed
        - What approved_at timestamps were set
        """
        print("\n" + "=" * 70)
        print("BUG CONDITION EXPLORATION TEST")
        print("=" * 70)
        print("\nThis test is EXPECTED TO FAIL on unfixed code.")
        print("Failure confirms the 2-hour approval delay bug exists.\n")
        
        # Create 5 test internships with embedded emails
        print("Creating 5 test internships with embedded emails...")
        for i in range(5):
            internship = self._create_test_internship(i)
            print(f"  [OK] Created internship {i+1}: {internship['company']} - {internship['role']}")
        
        # Load resume for scoring
        resume = _load_resume()
        
        # Verify internships are discoverable
        print("\nVerifying internships are discoverable...")
        discovered = db.list_discovered_internships(limit=10)
        print(f"  Found {len(discovered)} discovered internships in database")
        test_internships_found = [i for i in discovered if i["id"] in self.test_internship_ids]
        print(f"  Found {len(test_internships_found)} of our test internships")
        
        # Process the discovered internships (this should generate drafts)
        print("\nProcessing discovered internships...")
        _process_discovered_internships(resume, limit=10)
        
        # Process the email queue to send approved emails
        print("\nProcessing email queue to send approved emails...")
        from outreach.queue_manager import process_email_queue
        process_email_queue()
        
        # Check internship statuses after processing
        print("\nChecking internship statuses after processing...")
        for internship_id in self.test_internship_ids:
            internship_res = db.client.table("internships").select("*").eq("id", internship_id).execute()
            if internship_res.data:
                internship = internship_res.data[0]
                print(f"  Internship {internship_id[:8]}... status='{internship.get('status')}', "
                      f"pre_score={internship.get('pre_score')}, full_score={internship.get('full_score')}")
        
        # Collect test lead and draft IDs for cleanup
        for internship_id in self.test_internship_ids:
            # Get leads for this internship
            leads_res = db.client.table("leads").select("*").eq("internship_id", internship_id).execute()
            for lead in leads_res.data or []:
                self.test_lead_ids.append(lead["id"])
                
                # Get drafts for this lead
                drafts_res = db.client.table("email_drafts").select("*").eq("lead_id", lead["id"]).execute()
                for draft in drafts_res.data or []:
                    self.test_draft_ids.append(draft["id"])
        
        print(f"  [OK] Processed {len(self.test_internship_ids)} internships")
        print(f"  [OK] Generated {len(self.test_lead_ids)} leads")
        print(f"  [OK] Generated {len(self.test_draft_ids)} drafts")
        
        # Check draft statuses
        print("\nChecking draft statuses...")
        now = utcnow()
        generated_count = 0
        approved_count = 0
        future_approved_at_count = 0
        
        for draft_id in self.test_draft_ids:
            draft_res = db.client.table("email_drafts").select("*").eq("id", draft_id).execute()
            if draft_res.data:
                draft = draft_res.data[0]
                status = draft.get("status")
                approved_at = draft.get("approved_at")
                
                print(f"  Draft {draft_id[:8]}... status='{status}', approved_at={approved_at}")
                
                if status == "generated":
                    generated_count += 1
                elif status in ("approved", "auto_approved"):
                    approved_count += 1
                
                if approved_at:
                    approved_at_dt = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
                    if approved_at_dt > now:
                        future_approved_at_count += 1
                        delay_minutes = (approved_at_dt - now).total_seconds() / 60
                        print(f"    [!] approved_at is {delay_minutes:.0f} minutes in the future!")
        
        # Check how many emails were sent
        print("\nChecking email send status...")
        sent_count = 0
        ready_to_send_count = 0
        for draft_id in self.test_draft_ids:
            draft_res = db.client.table("email_drafts").select("*").eq("id", draft_id).execute()
            if draft_res.data:
                draft = draft_res.data[0]
                status = draft.get("status")
                approved_at = draft.get("approved_at")
                
                if status == "sent":
                    sent_count += 1
                    print(f"  [OK] Draft {draft_id[:8]}... was sent")
                elif status in ("approved", "auto_approved"):
                    # Check if approved_at <= now (ready to send)
                    if approved_at:
                        approved_at_dt = datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
                        if approved_at_dt <= now:
                            ready_to_send_count += 1
                            print(f"  [READY] Draft {draft_id[:8]}... is ready to send (status='{status}')")
        
        total_sendable = sent_count + ready_to_send_count
        
        print(f"\n[RESULTS]:")
        print(f"  - Total drafts created: {len(self.test_draft_ids)}")
        print(f"  - Drafts with status='generated': {generated_count}")
        print(f"  - Drafts with status='approved' or 'auto_approved': {approved_count}")
        print(f"  - Drafts with approved_at in future: {future_approved_at_count}")
        print(f"  - Emails sent: {sent_count}")
        print(f"  - Emails ready to send: {ready_to_send_count}")
        print(f"  - Total sendable (sent + ready): {total_sendable}")
        
        # Document counterexamples
        print("\n[COUNTEREXAMPLES FOUND]:")
        if generated_count > 0:
            print(f"  [!] {generated_count} draft(s) remain in status='generated' (not 'approved')")
        if future_approved_at_count > 0:
            print(f"  [!] {future_approved_at_count} draft(s) have approved_at set to future time")
        if total_sendable < len(self.test_draft_ids):
            print(f"  [!] Only {total_sendable}/{len(self.test_draft_ids)} emails are sendable (sent or ready to send)")
        
        # ASSERTIONS - These should FAIL on unfixed code
        print("\n[RUNNING ASSERTIONS] (EXPECTED TO FAIL ON UNFIXED CODE):")
        
        try:
            # Assert all drafts should be approved immediately (not 'generated')
            self.assertEqual(
                generated_count, 0,
                f"Expected 0 drafts with status='generated', but found {generated_count}. "
                f"Drafts should be approved immediately without 2-hour delay."
            )
            print("  [OK] All drafts are approved immediately")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        try:
            # Assert approved_at should be current time (not future)
            self.assertEqual(
                future_approved_at_count, 0,
                f"Expected 0 drafts with future approved_at, but found {future_approved_at_count}. "
                f"approved_at should be set to current time, not future time with 10-30 min delay."
            )
            print("  [OK] All approved_at timestamps are current time")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        try:
            # Assert all emails should be sent or ready to send (not blocked by approval delay)
            self.assertEqual(
                total_sendable, len(self.test_draft_ids),
                f"Expected {len(self.test_draft_ids)} emails sendable (sent or ready), but only {total_sendable} are sendable. "
                f"All emails should be ready to send immediately within one scheduler cycle (not blocked by 2-hour approval delay)."
            )
            print("  [OK] All emails sent or ready to send")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        print("\n" + "=" * 70)
        print("[PASS] TEST PASSED - Bug is FIXED!")
        print("=" * 70)
        print("\nIf you see this message, the bug has been fixed.")
        print("Emails are now sent immediately without approval delays.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
