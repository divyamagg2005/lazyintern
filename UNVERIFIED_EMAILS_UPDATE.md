# Unverified Emails Update - March 1, 2026

## Change Request
User requested to send emails to ALL leads, including unverified ones (emails that failed MX/SMTP validation).

## Changes Made

### 1. Updated Backfill Script
**File**: `backend/backfill_drafts.py`

**Changes**:
- Removed `eq("verified", True)` and `eq("mx_valid", True)` filters
- Now queries ALL leads regardless of verification status
- Fixed `full_score` handling to default to 0 if None (some unverified leads don't have scores yet)

**Before**:
```python
leads_result = (
    db.client.table("leads")
    .select("*")
    .eq("verified", True)
    .eq("mx_valid", True)
    .execute()
)
```

**After**:
```python
leads_result = (
    db.client.table("leads")
    .select("*")
    .execute()
)
```

### 2. Updated Cycle Manager
**File**: `backend/scheduler/cycle_manager.py`

**Changes**:
- Removed `continue` statement after email validation fails
- Now continues to full scoring and draft generation even if email validation fails
- Still logs validation failures and marks internship status appropriately

**Before**:
```python
if not v.valid:
    # ... log and mark as invalid ...
    continue  # STOP HERE - don't generate draft
```

**After**:
```python
if not v.valid:
    # ... log and mark as invalid ...
    # CHANGED: Continue to scoring even if validation fails
    # Don't skip - just log the validation failure and continue
else:
    # ... mark as verified ...
```

## Results

### Before Changes:
- Total leads: 16
- Verified leads: 9
- Drafts created: 9
- Missing drafts: 7

### After Changes:
- Total leads: 16
- Verified leads: 9
- Unverified leads: 7
- **Drafts created: 16** ✓
- **Missing drafts: 0** ✓

## Impact

### Positive:
- All leads now get email drafts and SMS approval requests
- No leads are skipped due to validation failures
- Higher outreach volume

### Risks:
- Unverified emails may bounce (MX/SMTP validation failed)
- Could impact sender reputation if too many bounces occur
- Some emails might be invalid/non-existent

### Recommendation:
Monitor bounce rates closely. If bounce rate exceeds 5-10%, consider:
1. Re-enabling validation filters for future leads
2. Using a separate "risky leads" queue with lower priority
3. Implementing bounce tracking and automatic quarantine

## Verification

Run this command to verify all leads have drafts:
```bash
cd backend
python -c "from core.supabase_db import db; leads = db.client.table('leads').select('id').execute(); drafts = db.client.table('email_drafts').select('lead_id').execute(); draft_ids = set(d['lead_id'] for d in drafts.data); missing = [l['id'] for l in leads.data if l['id'] not in draft_ids]; print(f'Leads: {len(leads.data)}, Drafts: {len(drafts.data)}, Missing: {len(missing)}')"
```

Expected output: `Leads: 16, Drafts: 16, Missing: 0`

## Future Behavior

Going forward, the pipeline will:
1. Extract emails (regex or Hunter)
2. Validate emails (MX + SMTP check)
3. **Continue to scoring regardless of validation result** (NEW)
4. Generate Groq drafts for ALL leads with score >= 60
5. Send SMS approval for ALL drafts
6. Send emails after approval

The validation still happens and is logged, but it no longer blocks draft generation.
