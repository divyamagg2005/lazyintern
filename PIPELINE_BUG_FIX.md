# Pipeline Bug Fix - Drafts Not Generated

## Problem
Pipeline was stopping after email validation and not proceeding to full scoring, draft generation, and SMS sending.

## Root Cause
In `backend/scheduler/cycle_manager.py`, when email validation failed, the code was setting the internship status to `"email_invalid"` (line 138). This caused the internship to be removed from the processing queue because `list_discovered_internships()` only returns internships with `status = "discovered"`.

The pipeline flow was:
1. Internship discovered (status = "discovered")
2. Email extracted and lead created
3. Email validation fails
4. Status changed to "email_invalid" ❌
5. Internship no longer in "discovered" status
6. Full scoring, draft generation, and SMS never executed

## Fix Applied

### Change 1: Remove premature status update during validation
Removed the line that sets status to `"email_invalid"` during validation. The internship now stays in "discovered" status and continues through the pipeline even if email validation fails.

**Before:**
```python
if not v.valid:
    # ... validation failure handling ...
    db.client.table("internships").update(
        {"status": "email_invalid"}
    ).eq("id", iid).execute()
```

**After:**
```python
if not v.valid:
    # ... validation failure handling ...
    # NOTE: Don't change internship status here - let it continue to scoring
    # The lead is marked as unverified, but we still want to score and generate drafts
```

### Change 2: Add status update after SMS sent
Added status update to "pending_approval" after SMS is sent to prevent duplicate processing in the next cycle.

**Before:**
```python
send_approval_sms(draft, lead, internship, int(fs.score))
# No status update - internship stays "discovered"
```

**After:**
```python
send_approval_sms(draft, lead, internship, int(fs.score))

# Mark internship as processed to prevent duplicate processing
db.client.table("internships").update(
    {"status": "pending_approval"}
).eq("id", iid).execute()
db.log_event(iid, "approval_sent", {"draft_id": draft["id"]})
```

## Pipeline Flow After Fix

1. Internship discovered (status = "discovered")
2. Pre-scoring (if score < 40, status = "low_priority", stop)
3. Email extraction (regex or Hunter)
4. Email validation (lead marked verified=true/false, but internship stays "discovered")
5. Full scoring (if score < 60, status = "low_priority", stop)
6. Draft generation
7. SMS sent for approval
8. Status updated to "pending_approval" ✅
9. Auto-approver will approve after 2 hours (no score threshold)

## Expected Behavior Now

- All internships with emails (verified or not) will proceed to full scoring
- Drafts will be generated for internships with full_score >= 60
- SMS will be sent for approval
- Internships won't be processed multiple times
- Auto-approver will approve all drafts after 2 hours

## Next Steps

1. Run the cleanup query to reset today's partial data
2. Run the pipeline again
3. You should see:
   - Full scoring logs
   - Draft generation logs
   - SMS messages on your phone
   - Drafts in "generated" status in database
   - After 2 hours, drafts auto-approved and emails sent
