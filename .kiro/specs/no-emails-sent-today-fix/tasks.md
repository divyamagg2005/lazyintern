# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - Processed Internships Incorrectly Returned
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases - database states with both processed (pre_score NOT NULL) and unprocessed (pre_score NULL) internships with status="discovered"
  - Test that `list_discovered_internships()` returns ONLY internships where pre_score IS NULL (from Fault Condition in design)
  - Create test database state: 200 internships with status="discovered" and pre_score=75, plus 42 internships with status="discovered" and pre_score=NULL
  - Call UNFIXED `list_discovered_internships(limit=200)` and assert it returns internships with pre_score NOT NULL
  - The test assertions should match the Expected Behavior Properties from design: result should contain ONLY internships with pre_score IS NULL
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found: function returns processed internships when it should return only unprocessed ones
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Pipeline Processing and Query Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (database states where all internships have pre_score=NULL)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For database states with N internships (status="discovered", pre_score=NULL), function returns all N internships up to limit
    - For database states with internships having status != "discovered", function returns empty list
    - For various limit values (1, 10, 50, 100, 200), function respects the limit parameter
    - For empty database, function returns empty list
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

- [x] 3. Fix for list_discovered_internships query bug

  - [x] 3.1 Implement the fix in backend/core/supabase_db.py
    - Add `.is_("pre_score", "null")` filter to the query chain in `list_discovered_internships()`
    - Place the filter after `.eq("status", "discovered")` and before `.limit(limit)`
    - This ensures only unprocessed internships (pre_score IS NULL) are returned
    - _Bug_Condition: isBugCondition(database_state) where EXISTS internship with status="discovered" AND pre_score IS NOT NULL that is returned by list_discovered_internships()_
    - _Expected_Behavior: list_discovered_internships() SHALL return ONLY internships where status="discovered" AND pre_score IS NULL_
    - _Preservation: All pipeline processing (pre-scoring, email extraction, Hunter API, validation, scoring, draft generation, sending) must remain unchanged; all other database queries must remain unchanged; status transitions and daily limits must remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Only Unprocessed Internships Returned
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify that `list_discovered_internships()` now returns ONLY internships with pre_score IS NULL
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Pipeline Processing and Query Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions in query behavior or pipeline processing)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
