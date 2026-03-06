"""
Bug Condition Exploration Test for No Emails Sent Today Fix

**Validates: Requirements 2.1, 2.2, 2.3**

This test is designed to FAIL on unfixed code to confirm the bug exists.
The bug: list_discovered_internships() returns already-processed internships 
(pre_score NOT NULL) instead of only unprocessed internships (pre_score IS NULL).

Expected behavior (after fix):
- list_discovered_internships() should return ONLY internships where pre_score IS NULL
- New unprocessed internships should be returned, not old processed ones
- Already-processed internships (pre_score NOT NULL) should be excluded

Current behavior (unfixed code - test will FAIL):
- list_discovered_internships() returns internships with pre_score NOT NULL
- Old processed internships fill the query limit
- New unprocessed internships are never returned

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from typing import Any
from uuid import uuid4

from core.supabase_db import db


class TestNoEmailsBugExploration(unittest.TestCase):
    """
    Bug Condition Exploration: Processed Internships Incorrectly Returned
    
    This test surfaces counterexamples demonstrating that list_discovered_internships()
    returns already-processed internships (pre_score NOT NULL) when it should return
    only unprocessed internships (pre_score IS NULL).
    
    **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
    """
    
    def setUp(self):
        """Set up test data"""
        self.test_internship_ids = []
        
    def tearDown(self):
        """Clean up test data"""
        for internship_id in self.test_internship_ids:
            try:
                db.client.table("internships").delete().eq("id", internship_id).execute()
            except Exception:
                pass
    
    def _create_test_internship(
        self, 
        index: int, 
        pre_score: int | None = None
    ) -> dict[str, Any]:
        """Create a test internship with specified pre_score"""
        internship_id = str(uuid4())
        self.test_internship_ids.append(internship_id)
        
        internship_data = {
            "id": internship_id,
            "company": f"TestCompany{index}",
            "role": f"Software Engineer Intern {index}",
            "link": f"https://test-job-board.com/job/{internship_id}",
            "description": f"Test internship description {index}",
            "location": "Remote",
            "status": "discovered",
            "pre_score": pre_score,
            "full_score": None,
        }
        
        result = db.client.table("internships").insert(internship_data).execute()
        return result.data[0]
    
    def test_processed_internships_incorrectly_returned(self):
        """
        Property 1: Fault Condition - Processed Internships Incorrectly Returned
        
        **Validates: Requirements 2.1, 2.2, 2.3**
        
        Test that list_discovered_internships() returns internships with pre_score NOT NULL
        when it should return ONLY internships with pre_score IS NULL.
        
        Scoped PBT Approach: Create database state with:
        - 200 internships with status="discovered" and pre_score=75 (already processed)
        - 42 internships with status="discovered" and pre_score=NULL (unprocessed)
        
        Call list_discovered_internships(limit=200) and verify it returns processed internships.
        
        Assertions verify:
        - Result contains internships with pre_score NOT NULL (the bug)
        - Result should contain ONLY internships with pre_score IS NULL (expected behavior)
        
        **EXPECTED OUTCOME**: Test FAILS (confirms bug exists)
        
        Counterexamples to document:
        - How many processed internships (pre_score NOT NULL) were returned
        - How many unprocessed internships (pre_score IS NULL) were returned
        - Whether new unprocessed internships were excluded from results
        """
        print("\n" + "=" * 70)
        print("BUG CONDITION EXPLORATION TEST")
        print("=" * 70)
        print("\nThis test is EXPECTED TO FAIL on unfixed code.")
        print("Failure confirms the list_discovered_internships() bug exists.\n")
        
        # Create 200 already-processed internships (pre_score=75)
        print("Creating 200 already-processed internships (pre_score=75)...")
        processed_ids = []
        for i in range(200):
            internship = self._create_test_internship(i, pre_score=75)
            processed_ids.append(internship["id"])
            if (i + 1) % 50 == 0:
                print(f"  [OK] Created {i + 1}/200 processed internships")
        
        # Create 42 new unprocessed internships (pre_score=NULL)
        print("\nCreating 42 new unprocessed internships (pre_score=NULL)...")
        unprocessed_ids = []
        for i in range(200, 242):
            internship = self._create_test_internship(i, pre_score=None)
            unprocessed_ids.append(internship["id"])
        print(f"  [OK] Created 42 unprocessed internships")
        
        # Call list_discovered_internships(limit=200)
        print("\nCalling list_discovered_internships(limit=200)...")
        result = db.list_discovered_internships(limit=200)
        print(f"  [OK] Returned {len(result)} internships")
        
        # Analyze results
        print("\nAnalyzing results...")
        result_ids = {r["id"] for r in result}
        
        processed_in_result = [r for r in result if r["pre_score"] is not None]
        unprocessed_in_result = [r for r in result if r["pre_score"] is None]
        
        processed_count = len(processed_in_result)
        unprocessed_count = len(unprocessed_in_result)
        
        # Check how many of our test internships are in the result
        our_processed_in_result = len([pid for pid in processed_ids if pid in result_ids])
        our_unprocessed_in_result = len([uid for uid in unprocessed_ids if uid in result_ids])
        
        print(f"  Total internships returned: {len(result)}")
        print(f"  Processed internships (pre_score NOT NULL): {processed_count}")
        print(f"  Unprocessed internships (pre_score IS NULL): {unprocessed_count}")
        print(f"  Our processed internships in result: {our_processed_in_result}/200")
        print(f"  Our unprocessed internships in result: {our_unprocessed_in_result}/42")
        
        # Document counterexamples
        print("\n[COUNTEREXAMPLES FOUND]:")
        if processed_count > 0:
            print(f"  [!] {processed_count} internship(s) with pre_score NOT NULL were returned")
            print(f"      (Expected: 0 - should return ONLY unprocessed internships)")
        
        if our_unprocessed_in_result < 42:
            print(f"  [!] Only {our_unprocessed_in_result}/42 new unprocessed internships were returned")
            print(f"      (Expected: 42 - all new unprocessed internships should be returned)")
        
        if our_processed_in_result > 0:
            print(f"  [!] {our_processed_in_result} already-processed internships were returned")
            print(f"      (Expected: 0 - processed internships should be excluded)")
        
        # Show sample of what was returned
        if processed_in_result:
            print("\n[SAMPLE OF PROCESSED INTERNSHIPS RETURNED]:")
            for i, internship in enumerate(processed_in_result[:3]):
                print(f"  {i+1}. ID: {internship['id'][:8]}... | "
                      f"Company: {internship['company']} | "
                      f"pre_score: {internship['pre_score']}")
        
        # ASSERTIONS - These should FAIL on unfixed code
        print("\n[RUNNING ASSERTIONS] (EXPECTED TO FAIL ON UNFIXED CODE):")
        
        try:
            # Assert NO processed internships should be returned
            self.assertEqual(
                processed_count, 0,
                f"Expected 0 internships with pre_score NOT NULL, but found {processed_count}. "
                f"list_discovered_internships() should return ONLY unprocessed internships (pre_score IS NULL)."
            )
            print("  [OK] No processed internships returned")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        try:
            # Assert ALL returned internships should have pre_score IS NULL
            self.assertEqual(
                unprocessed_count, len(result),
                f"Expected all {len(result)} internships to have pre_score IS NULL, but only {unprocessed_count} do. "
                f"list_discovered_internships() should return ONLY unprocessed internships."
            )
            print("  [OK] All returned internships have pre_score IS NULL")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        try:
            # Assert all 42 new unprocessed internships should be returned
            # (since limit=200 and we only have 42 unprocessed)
            self.assertEqual(
                our_unprocessed_in_result, 42,
                f"Expected all 42 new unprocessed internships to be returned, but only {our_unprocessed_in_result} were. "
                f"New unprocessed internships should not be excluded by old processed internships filling the limit."
            )
            print("  [OK] All 42 new unprocessed internships returned")
        except AssertionError as e:
            print(f"  [X] FAILED: {e}")
            raise
        
        print("\n" + "=" * 70)
        print("[PASS] TEST PASSED - Bug is FIXED!")
        print("=" * 70)
        print("\nIf you see this message, the bug has been fixed.")
        print("list_discovered_internships() now returns only unprocessed internships.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
