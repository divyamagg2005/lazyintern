# Run Pipeline Again - Fixed Version

## What Was Fixed
The pipeline was stopping after email validation because it was changing the internship status too early. This prevented full scoring, draft generation, and SMS sending from running.

The fix ensures:
- Internships continue through the full pipeline even if email validation fails
- Drafts are generated for all high-scoring internships
- SMS messages are sent for approval
- Internships are marked as processed to prevent duplicates

## Steps to Run

### 1. Clean Up Partial Data (Optional)
If you want to start fresh, run the cleanup query in Supabase:

```sql
-- See what will be deleted
SELECT COUNT(*) FROM internships WHERE DATE(created_at) = CURRENT_DATE;
SELECT COUNT(*) FROM leads WHERE DATE(created_at) = CURRENT_DATE;
SELECT COUNT(*) FROM email_drafts WHERE DATE(created_at) = CURRENT_DATE;

-- Delete today's data
DELETE FROM email_drafts WHERE DATE(created_at) = CURRENT_DATE;
DELETE FROM leads WHERE DATE(created_at) = CURRENT_DATE;
DELETE FROM internships WHERE DATE(created_at) = CURRENT_DATE;
DELETE FROM daily_usage WHERE date = CURRENT_DATE;
```

### 2. Run the Pipeline
```bash
cd backend
python run_scheduler_24_7.py
```

Or use the batch file:
```bash
.\RUN_24_7.ps1
```

### 3. What to Expect

You should see logs like this:

```
Phase 3 - Pre-scoring:
- pre_scored events with scores

Phase 4 - Email extraction:
- email_found_regex or email_found_hunter events

Phase 5 - Email validation:
- email_valid or email_invalid events
- Internship stays in "discovered" status ✅

Phase 7 - Full scoring:
- full_scored events with breakdown ✅
- Internships with score < 60 marked as "low_priority"

Phase 8 - Draft generation:
- draft_generated events ✅

Phase 9 - SMS approval:
- SMS sent to your phone ✅
- approval_sent events
- Internship marked as "pending_approval"
```

### 4. Check Your Phone
You should receive SMS messages with:
- Company name
- Role
- Score
- Short code to approve/reject

### 5. Auto-Approval
After 2 hours, all drafts will be auto-approved (no score threshold) and emails will be sent automatically.

### 6. Monitor Dashboard
Start the dashboard to see real-time stats:
```bash
cd backend/dashboard
npm run dev
```

Open http://localhost:3000 to see:
- Discovery stats
- Email extraction stats
- Outreach stats (drafts, approvals, emails sent)
- Performance metrics

## Troubleshooting

### No SMS received?
- Check Twilio credentials in .env
- Check logs for "approval_sent" events
- Verify phone number format in Twilio settings

### No drafts generated?
- Check logs for "full_scored" events
- Verify full_score >= 60 for internships
- Check Groq API key in .env

### Duplicates in next cycle?
- Verify internships are marked as "pending_approval" after SMS sent
- Check logs for "approval_sent" events

## Database Queries to Verify

```sql
-- Check internship statuses
SELECT status, COUNT(*) 
FROM internships 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY status;

-- Check leads
SELECT verified, COUNT(*) 
FROM leads 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY verified;

-- Check drafts
SELECT status, COUNT(*) 
FROM email_drafts 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY status;

-- Check full scores
SELECT COUNT(*) 
FROM internships 
WHERE full_score IS NOT NULL 
AND DATE(created_at) = CURRENT_DATE;
```
