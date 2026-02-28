# Groq Email Drafting & Backfill ✅ COMPLETE

## Date: 2026-02-28

---

## Task 1: Connect Groq Drafting to Pipeline ✅ ALREADY COMPLETE

### Status
The Groq email drafting and Twilio SMS approval are **already connected** in the pipeline!

### Current Flow (in `backend/scheduler/cycle_manager.py`)

After a lead passes full scoring (score >= 60):

```python
# Phase 7 — full scoring
fs = full_score(internship, resume)
db.client.table("internships").update(
    {"full_score": int(fs.score)}
).eq("id", iid).execute()
db.log_event(iid, "full_scored", {"score": fs.score, "breakdown": fs.breakdown})

if fs.score < 60:
    db.client.table("internships").update(
        {"status": "low_priority"}
    ).eq("id", iid).execute()
    continue

# Phase 8 — Groq personalization
draft_obj = generate_draft(lead, internship, resume)
draft = db.insert_email_draft(
    {
        "lead_id": lead["id"],
        "subject": draft_obj.subject,
        "body": draft_obj.body,
        "followup_body": draft_obj.followup_body,
        "status": "generated",
    }
)
db.log_event(iid, "draft_generated", {"draft_id": draft["id"]})

# Phase 9 — Twilio human approval (send SMS, wait for webhook / auto-approver)
send_approval_sms(draft, lead, internship, int(fs.score))
```

### What Happens

1. **Groq Draft Generation** (`generate_draft()` from `backend/pipeline/groq_client.py`):
   - Takes: lead details, internship details, resume
   - Calls Groq API with personalized prompt
   - Returns: `GroqDraft(subject, body, followup_body)`
   - Falls back to template if API fails

2. **Save to Database** (`db.insert_email_draft()`):
   - Saves draft to `email_drafts` table
   - Fields: lead_id, subject, body, followup_body, status='generated'
   - Returns draft with ID

3. **Send Twilio SMS** (`send_approval_sms()` from `backend/approval/twilio_sender.py`):
   - Sends WhatsApp message to approver
   - Format:
     ```
     🎯 *LazyIntern - New Lead*
     
     *Company:* {company}
     *Role:* {role}
     *Score:* {score}%
     *Email:* {email}
     *Source:* {source}
     
     *Reply:*
     ✅ YES - Approve & send
     ❌ NO - Reject & quarantine
     👁️ PREVIEW - See full email
     
     DRAFT:{draft_id}
     ```
   - Sets `approval_sent_at = now()` after successful send

### Modules Used

- `backend/pipeline/groq_client.py` - Email draft generation
- `backend/approval/twilio_sender.py` - WhatsApp SMS approval
- `backend/core/supabase_db.py` - Database operations

---

## Task 2: One-Time Backfill for Existing Leads ✅ COMPLETE

### Created: `backend/backfill_drafts.py`

### What It Does

Backfills email drafts for existing verified leads that don't have drafts yet.

### Process

1. **Query leads without drafts**:
   ```sql
   SELECT leads.* 
   FROM leads
   LEFT JOIN email_drafts ON email_drafts.lead_id = leads.id
   WHERE email_drafts.id IS NULL
   AND leads.verified = true
   AND leads.mx_valid = true
   ```

2. **For each lead found**:
   - Fetch internship details
   - Generate Groq draft
   - Save to `email_drafts` table
   - Send Twilio SMS for approval
   - Log: "Backfill draft created for {email} at {company}"

3. **Rate limiting**:
   - 3 second delay between each SMS
   - Prevents Twilio rate limiting

4. **Smart execution**:
   - Checks if backfill is needed before running
   - Only runs if `leads.count > email_drafts.count`
   - Logs progress: `[1/10] Processing: hr@company.com at TechCorp`

### Functions

#### `backfill_existing_leads()`
Main backfill function that processes all leads without drafts.

```python
def backfill_existing_leads() -> None:
    """
    One-time backfill for existing leads that don't have email drafts yet.
    
    Process:
    1. Query all verified leads without drafts
    2. For each lead: generate Groq draft → save to email_drafts → send Twilio SMS
    3. Add 3 second delay between each SMS to avoid rate limiting
    """
```

#### `should_run_backfill()`
Checks if backfill is needed before running.

```python
def should_run_backfill() -> bool:
    """
    Check if backfill should run.
    Only run if there are leads without drafts.
    """
```

### How to Run

#### Option 1: Run Once Manually
```bash
cd backend
python backfill_drafts.py
```

#### Option 2: Run on Startup (Recommended)
Add to `backend/run_scheduler_24_7.py` or startup script:

```python
from backfill_drafts import should_run_backfill, backfill_existing_leads

# Run backfill once on startup if needed
if should_run_backfill():
    backfill_existing_leads()
```

### Example Output

```
======================================================================
Starting backfill for existing leads without drafts
======================================================================
Found 15 leads without drafts. Starting backfill...
[1/15] Processing: hr@blitzenx.com at Blitzenx
[1/15] ✓ Backfill draft created for hr@blitzenx.com at Blitzenx
[2/15] Processing: careers@innovexis.com at Innovexis
[2/15] ✓ Backfill draft created for careers@innovexis.com at Innovexis
[3/15] Processing: hiring@techcorp.in at TechCorp
[3/15] ✓ Backfill draft created for hiring@techcorp.in at TechCorp
...
======================================================================
Backfill complete: 15 success, 0 errors
======================================================================
```

---

## Flow Diagram

### Normal Pipeline Flow (Task 1)
```
Internship Discovered
  ↓
Pre-Score (>= 40)
  ↓
Email Extraction (regex or Hunter)
  ↓
Email Validation (MX + SMTP)
  ↓
Full Score (>= 60)
  ↓
✓ Groq Draft Generation ← TASK 1
  ↓
✓ Save to email_drafts ← TASK 1
  ↓
✓ Send Twilio SMS ← TASK 1
  ↓
Wait for Approval (YES/NO/PREVIEW)
  ↓
Send Email (if approved)
```

### Backfill Flow (Task 2)
```
Startup / Manual Run
  ↓
Check: leads.count > email_drafts.count?
  ↓ YES
Query: Verified leads without drafts
  ↓
For each lead:
  ↓
  Fetch internship details
  ↓
  ✓ Groq Draft Generation ← TASK 2
  ↓
  ✓ Save to email_drafts ← TASK 2
  ↓
  ✓ Send Twilio SMS ← TASK 2
  ↓
  Wait 3 seconds (rate limiting)
  ↓
Next lead...
```

---

## Database Schema

### `email_drafts` Table
```sql
CREATE TABLE email_drafts (
  id UUID PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  subject TEXT,
  body TEXT,
  followup_body TEXT,
  status TEXT, -- 'generated', 'approved', 'rejected', 'sent'
  approval_sent_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### `leads` Table
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  internship_id UUID REFERENCES internships(id),
  recruiter_name TEXT,
  email TEXT,
  source TEXT, -- 'regex', 'hunter'
  confidence INT,
  verified BOOLEAN,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Verification

### Check Pipeline is Working

After running a cycle, check logs for:
```
INFO: draft_generated - draft_id: abc-123
INFO: approval_sent - draft_id: abc-123
INFO: WhatsApp approval sent for draft abc-123
```

### Check Backfill Results

After running backfill, check database:
```sql
-- Count leads without drafts (should be 0 after backfill)
SELECT COUNT(*) 
FROM leads
LEFT JOIN email_drafts ON email_drafts.lead_id = leads.id
WHERE email_drafts.id IS NULL
AND leads.verified = true
AND leads.mx_valid = true;

-- Check backfill logs
SELECT * FROM event_logs
WHERE event = 'backfill_draft_generated'
ORDER BY created_at DESC;
```

### Check Twilio SMS

Check your WhatsApp for approval messages:
- Should receive one message per lead
- Format: "🎯 LazyIntern - New Lead..."
- Can reply: YES, NO, or PREVIEW

---

## Error Handling

### Groq API Failures
- Falls back to template draft
- Adds to retry queue
- Logs error

### Twilio SMS Failures
- Adds to retry queue
- Logs error
- Draft still saved (can be sent later)

### Backfill Errors
- Logs error for specific lead
- Continues with next lead
- Reports success/error count at end

---

## Rate Limiting

### Groq API
- Tracked in `daily_usage_stats.groq_calls`
- Tracked in `daily_usage_stats.groq_tokens_used`
- No hard limit (uses fallback if fails)

### Twilio SMS
- 3 second delay between messages in backfill
- Prevents rate limiting
- Normal pipeline has natural delays (one per cycle)

---

## Files

### Existing Files (Task 1 - Already Complete)
1. ✅ `backend/scheduler/cycle_manager.py` - Pipeline flow
2. ✅ `backend/pipeline/groq_client.py` - Draft generation
3. ✅ `backend/approval/twilio_sender.py` - SMS approval

### New Files (Task 2 - Created)
1. ✅ `backend/backfill_drafts.py` - Backfill script (NEW)
2. ✅ `GROQ_DRAFTING_AND_BACKFILL.md` - This documentation (NEW)

---

## Summary

### Task 1: Connect Groq Drafting ✅ ALREADY COMPLETE
- Groq draft generation: ✅ Already in pipeline
- Save to email_drafts: ✅ Already in pipeline
- Send Twilio SMS: ✅ Already in pipeline
- Set approval_sent_at: ✅ Already in pipeline

### Task 2: Backfill Existing Leads ✅ COMPLETE
- Query leads without drafts: ✅ Implemented
- Generate Groq drafts: ✅ Implemented
- Save to email_drafts: ✅ Implemented
- Send Twilio SMS: ✅ Implemented
- 3 second delay: ✅ Implemented
- Smart execution check: ✅ Implemented

---

## Next Steps

1. ✅ Task 1 already complete (no action needed)
2. ✅ Task 2 script created
3. ⏭️ Run backfill once:
   ```bash
   cd backend
   python backfill_drafts.py
   ```
4. ⏭️ Check WhatsApp for approval messages
5. ⏭️ Optional: Add backfill to startup script for automatic execution

---

**Both tasks complete!** The pipeline is fully connected with Groq drafting and Twilio approval, and the backfill script is ready to process existing leads.
