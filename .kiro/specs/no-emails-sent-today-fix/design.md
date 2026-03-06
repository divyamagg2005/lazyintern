# No Emails Sent Today Bugfix Design

## Overview

The email outreach system is running without crashes and successfully scraping internships, but no emails are being sent because the `list_discovered_internships()` function has a logic bug. The function queries for internships with status="discovered" but does NOT filter out internships that have already been pre-scored. This causes it to return the same 200 already-processed internships on every cycle, while newly discovered internships with NULL pre_score are never returned and therefore never processed.

The fix is minimal and surgical: add a single `.is_("pre_score", "null")` filter to the query in `list_discovered_internships()`. This ensures only unprocessed internships (those with NULL pre_score) are returned, allowing new internships to enter the processing pipeline.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `list_discovered_internships()` is called and there exist internships with status="discovered" AND pre_score IS NOT NULL
- **Property (P)**: The desired behavior - `list_discovered_internships()` should return ONLY internships where status="discovered" AND pre_score IS NULL
- **Preservation**: All existing pipeline behavior (pre-scoring, email extraction, Hunter API logic, validation, scoring, draft generation, sending) must remain unchanged
- **list_discovered_internships()**: The function in `backend/core/supabase_db.py` that queries the internships table to find unprocessed internships
- **pre_score**: A numeric field (0-100) that indicates an internship has been processed through the pre-scoring phase; NULL means unprocessed
- **status**: A string field that tracks internship lifecycle; "discovered" means scraped and ready for processing

## Bug Details

### Fault Condition

The bug manifests when `list_discovered_internships()` is called and the database contains internships with status="discovered" that have already been pre-scored (pre_score IS NOT NULL). The function queries only by status="discovered" without checking if pre_score IS NULL, causing it to return already-processed internships instead of new ones.

**Formal Specification:**
```
FUNCTION isBugCondition(database_state)
  INPUT: database_state containing internships table
  OUTPUT: boolean
  
  RETURN EXISTS internship IN database_state.internships WHERE
         internship.status == "discovered"
         AND internship.pre_score IS NOT NULL
         AND internship IS IN list_discovered_internships().result
END FUNCTION
```

### Examples

- **Example 1**: Database has 200 internships with status="discovered" and pre_score=75 (already processed). New scrape adds 42 internships with status="discovered" and pre_score=NULL. `list_discovered_internships(limit=200)` returns the 200 old internships, not the 42 new ones. Expected: Should return the 42 new internships.

- **Example 2**: Database has 50 internships with status="discovered" and pre_score=NULL. `list_discovered_internships(limit=200)` returns all 50 internships. Expected: Correct behavior - returns unprocessed internships.

- **Example 3**: Database has 100 internships with status="discovered" and pre_score=NULL, plus 150 internships with status="discovered" and pre_score=80. `list_discovered_internships(limit=200)` returns a mix of both processed and unprocessed internships (200 total). Expected: Should return only the 100 unprocessed internships.

- **Edge Case**: Database has 0 internships with status="discovered" and pre_score=NULL. `list_discovered_internships()` returns empty list. Expected: Correct behavior - no unprocessed internships to return.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Recovery phase processing of pending approved drafts must continue to work
- Pre-scoring logic and thresholds (< 40 = low_priority, 40-59 = regex only, >= 60 = Hunter API) must remain unchanged
- Email extraction (regex and Hunter API) must continue to work exactly as before
- Hunter API blocking for job board domains must remain unchanged
- Email-level deduplication (domain already contacted) must remain unchanged
- Lead insertion and duplicate detection must remain unchanged
- Email validation logic must remain unchanged
- Full scoring logic must remain unchanged
- Draft generation and immediate sending must remain unchanged
- Daily email limits must continue to be respected
- SMS notifications must continue to work
- Status transitions (low_priority, no_email, email_sent) must remain unchanged

**Scope:**
All inputs and behaviors that do NOT involve the `list_discovered_internships()` query should be completely unaffected by this fix. This includes:
- All other database queries (list_pending_drafts, check_domain_already_contacted, etc.)
- All pipeline processing logic after internships are retrieved
- All email sending and notification logic
- All status updates and event logging

## Hypothesized Root Cause

Based on the bug description and code analysis, the root cause is clear:

1. **Missing Query Filter**: The `list_discovered_internships()` function in `backend/core/supabase_db.py` queries for internships WHERE status='discovered' but does NOT include a filter for pre_score IS NULL. This is the direct cause of the bug.

2. **Status Not Updated After Pre-Scoring**: When internships are pre-scored in `_process_discovered_internships()`, their status remains "discovered" (only changed to "low_priority" if score < 40). This means processed internships with pre_score values still match the query.

3. **Query Limit Filled by Old Records**: The query has a limit parameter (default 200). When there are more than 200 internships with status="discovered", the limit is filled by old processed internships, preventing new unprocessed internships from being returned.

4. **No Ordering Specified**: The query does not specify an ORDER BY clause, so the database returns internships in an arbitrary order (likely by insertion order or internal row ID), which means old internships are returned first.

## Correctness Properties

Property 1: Fault Condition - Only Unprocessed Internships Returned

_For any_ call to `list_discovered_internships()` where the database contains internships with status="discovered", the fixed function SHALL return ONLY internships where pre_score IS NULL, ensuring that already-processed internships are excluded and new internships enter the processing pipeline.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Pipeline Processing Unchanged

_For any_ internship returned by `list_discovered_internships()` (whether from the original or fixed function), the processing pipeline SHALL produce exactly the same behavior as before the fix, preserving all pre-scoring, email extraction, validation, scoring, draft generation, and sending logic.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

## Fix Implementation

### Changes Required

The fix is minimal and surgical - only one line needs to be added.

**File**: `backend/core/supabase_db.py`

**Function**: `list_discovered_internships`

**Specific Changes**:
1. **Add pre_score IS NULL Filter**: Add `.is_("pre_score", "null")` to the query chain after `.eq("status", "discovered")` and before `.limit(limit)`

**Before:**
```python
def list_discovered_internships(self, limit: int = 50) -> list[dict[str, Any]]:
    res = (
        self.client.table("internships")
        .select("*")
        .eq("status", "discovered")
        .limit(limit)
        .execute()
    )
    return list(res.data or [])
```

**After:**
```python
def list_discovered_internships(self, limit: int = 50) -> list[dict[str, Any]]:
    res = (
        self.client.table("internships")
        .select("*")
        .eq("status", "discovered")
        .is_("pre_score", "null")
        .limit(limit)
        .execute()
    )
    return list(res.data or [])
```

**Rationale**: The `.is_("pre_score", "null")` filter ensures that only internships with NULL pre_score are returned. This is the correct way to filter for NULL values in Supabase/PostgREST queries. The filter is placed after the status filter and before the limit to ensure the limit applies only to unprocessed internships.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the function returns already-processed internships when it should return only unprocessed ones.

**Test Plan**: Create a test database state with both processed (pre_score NOT NULL) and unprocessed (pre_score NULL) internships with status="discovered". Call the UNFIXED `list_discovered_internships()` and verify it returns processed internships. This confirms the bug.

**Test Cases**:
1. **Processed Internships Returned Test**: Insert 200 internships with status="discovered" and pre_score=75. Insert 42 internships with status="discovered" and pre_score=NULL. Call `list_discovered_internships(limit=200)`. Assert that the result contains internships with pre_score NOT NULL. (will fail on unfixed code - this is the bug)

2. **New Internships Not Returned Test**: Same setup as Test 1. Assert that the result does NOT contain all 42 new internships with pre_score=NULL. (will fail on unfixed code - confirms new internships are excluded)

3. **Mixed Results Test**: Insert 50 internships with status="discovered" and pre_score=NULL. Insert 150 internships with status="discovered" and pre_score=80. Call `list_discovered_internships(limit=200)`. Assert that the result contains internships with pre_score NOT NULL. (will fail on unfixed code)

4. **Empty Result When Only Processed Exist**: Insert 100 internships with status="discovered" and pre_score=90. Call `list_discovered_internships(limit=200)`. Assert that the result is NOT empty. (will fail on unfixed code - should be empty but returns processed internships)

**Expected Counterexamples**:
- The function returns internships with pre_score values (NOT NULL) when it should return only internships with pre_score=NULL
- New unprocessed internships are excluded from results when the limit is filled by old processed internships
- Possible causes: missing `.is_("pre_score", "null")` filter in the query

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL database_state WHERE isBugCondition(database_state) DO
  result := list_discovered_internships_fixed(limit)
  ASSERT all internships in result have pre_score IS NULL
  ASSERT all internships in result have status = "discovered"
  ASSERT no internships in result have pre_score IS NOT NULL
END FOR
```

**Test Cases**:
1. **Only Unprocessed Returned**: Insert 200 internships with status="discovered" and pre_score=75. Insert 42 internships with status="discovered" and pre_score=NULL. Call fixed `list_discovered_internships(limit=200)`. Assert result contains exactly 42 internships, all with pre_score=NULL.

2. **All Unprocessed Returned When Under Limit**: Insert 50 internships with status="discovered" and pre_score=NULL. Call fixed `list_discovered_internships(limit=200)`. Assert result contains exactly 50 internships, all with pre_score=NULL.

3. **Limit Respected**: Insert 300 internships with status="discovered" and pre_score=NULL. Call fixed `list_discovered_internships(limit=200)`. Assert result contains exactly 200 internships, all with pre_score=NULL.

4. **Empty Result When No Unprocessed**: Insert 100 internships with status="discovered" and pre_score=90. Call fixed `list_discovered_internships(limit=200)`. Assert result is empty list.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL database_state WHERE NOT isBugCondition(database_state) DO
  ASSERT list_discovered_internships_original(limit) = list_discovered_internships_fixed(limit)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for various database states where all internships have pre_score=NULL (no bug condition), then write property-based tests capturing that behavior.

**Test Cases**:
1. **All Unprocessed Preservation**: Insert N internships (N varies from 0 to 500) with status="discovered" and pre_score=NULL. Verify both original and fixed functions return the same results (all N internships, up to limit).

2. **Different Status Preservation**: Insert internships with status="low_priority", "no_email", "email_sent" (with or without pre_score). Verify both functions return empty list (status filter excludes them).

3. **Limit Parameter Preservation**: Test with various limit values (1, 10, 50, 100, 200, 500). Verify both functions respect the limit parameter identically.

4. **Empty Database Preservation**: Test with empty internships table. Verify both functions return empty list.

5. **Pipeline Processing Preservation**: For any internship returned by the fixed function, run it through `_process_discovered_internships()` and verify all pipeline steps (pre-scoring, email extraction, validation, scoring, draft generation) produce the same results as before.

### Unit Tests

- Test `list_discovered_internships()` with various database states (only unprocessed, only processed, mixed, empty)
- Test edge cases (limit=0, limit=1, limit > total internships)
- Test that pre_score=NULL filter works correctly
- Test that status="discovered" filter still works
- Test that limit parameter is respected

### Property-Based Tests

- Generate random database states with varying numbers of processed and unprocessed internships
- Verify fixed function always returns only unprocessed internships
- Generate random limit values and verify limit is respected
- Test preservation: for database states with only unprocessed internships, verify original and fixed functions return identical results

### Integration Tests

- Test full cycle flow: scrape internships → list_discovered_internships → process → verify emails sent
- Test that new internships are processed after fix is applied
- Test that daily email limits are still respected
- Test that all pipeline phases (pre-scoring, extraction, validation, scoring, drafts, sending) continue to work
