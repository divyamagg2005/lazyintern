# Send Pending Emails and Cleanup Database Guide

This guide explains how to send all pending emails and clean up your database to start fresh.

## Overview

You have 3 new scripts to help manage your database:

1. **send_all_pending_emails.py** - Sends all approved drafts
2. **cleanup_all_data.py** - Deletes all data from database
3. **SEND_AND_CLEANUP.ps1** / **SEND_AND_CLEANUP.bat** - Easy launcher for both

## Quick Start

### Option 1: Use the Launcher (Easiest)

**Windows PowerShell:**
```powershell
.\SEND_AND_CLEANUP.ps1
```

**Windows CMD:**
```cmd
SEND_AND_CLEANUP.bat
```

Then choose from the menu:
- Option 1: Send all pending emails
- Option 2: Cleanup database
- Option 3: Do both (recommended)

### Option 2: Run Scripts Directly

**Step 1: Send all pending emails**
```bash
cd backend
python send_all_pending_emails.py
```

**Step 2: Cleanup database**
```bash
cd backend
python cleanup_all_data.py
```

## Script Details

### 1. Send All Pending Emails (`send_all_pending_emails.py`)

**What it does:**
- Finds all approved/auto_approved drafts in database
- Sends them one by one with proper spacing (45-55 minutes)
- Respects daily email limit (default 15/day)
- Shows real-time progress
- Handles errors gracefully

**Features:**
- ✅ Automatic spacing enforcement
- ✅ Daily limit checking
- ✅ Progress tracking
- ✅ Error handling with notifications
- ✅ Can be interrupted (Ctrl+C) and resumed later

**Example Output:**
```
======================================================================
SEND ALL PENDING EMAILS
======================================================================

📊 Status:
  - Pending drafts: 9
  - Emails sent today: 0/15
  - Remaining capacity: 15

Send 9 email(s)? (yes/no): yes

======================================================================
SENDING EMAILS
======================================================================

📧 Sending email 1... ✓ Sent! [1/15] (8 pending)
⏳ Spacing constraint: waiting 45.0 minutes...
   (45 minutes must pass between emails)
   Next email can be sent at: 17:40:23
   Waiting... 2700s remaining

📧 Sending email 2... ✓ Sent! [2/15] (7 pending)
...

======================================================================
SUMMARY
======================================================================
✓ Emails sent: 9
✓ Total wait time: 360.0 minutes
✓ Emails sent today: 9/15
✓ Pending drafts remaining: 0

✓ All pending drafts have been sent!
======================================================================
```

**When to use:**
- Before cleaning up database
- After program crashes/interruptions
- To clear out old pending emails

### 2. Cleanup All Data (`cleanup_all_data.py`)

**What it does:**
- Deletes ALL data from database tables
- Gives you option to keep daily_usage_stats
- Requires triple confirmation (safety feature)
- Shows before/after counts

**Tables cleaned:**
- ✅ internships
- ✅ leads
- ✅ email_drafts
- ✅ followup_queue
- ✅ event_log
- ✅ retry_queue
- ⚠️ daily_usage_stats (optional - you can keep this)

**Safety Features:**
- ⚠️ Requires typing "DELETE ALL DATA" to proceed
- ⚠️ Shows record counts before deletion
- ⚠️ Cannot be undone
- ⚠️ Option to keep daily usage stats

**Example Output:**
```
======================================================================
⚠️  CLEANUP ALL DATA - DESTRUCTIVE OPERATION ⚠️
======================================================================

This will DELETE ALL DATA from the following tables:
  - internships
  - leads
  - email_drafts
  - followup_queue
  - event_log
  - retry_queue

⚠️  THIS CANNOT BE UNDONE! ⚠️
======================================================================

📊 Current record counts:
  - internships: 11
  - leads: 11
  - email_drafts: 9
  - followup_queue: 0
  - event_log: 156
  - retry_queue: 2
  - daily_usage_stats: 1 (will be kept)

⚠️  CONFIRMATION REQUIRED ⚠️
Type 'DELETE ALL DATA' to proceed (case-sensitive):
> DELETE ALL DATA

======================================================================
DELETING DATA
======================================================================

🗑️  Deleting Followup queue entries... ✓ Deleted all records
🗑️  Deleting Email drafts... ✓ Deleted all records
🗑️  Deleting Leads... ✓ Deleted all records
🗑️  Deleting Internships... ✓ Deleted all records
🗑️  Deleting Event logs... ✓ Deleted all records
🗑️  Deleting Retry queue entries... ✓ Deleted all records

======================================================================
CLEANUP SUMMARY
======================================================================
  - followup_queue: all
  - email_drafts: all
  - leads: all
  - internships: all
  - event_log: all
  - retry_queue: all

✓ Cleanup complete!

You can now start fresh with a clean database.
Run the pipeline to discover new internships and send emails.
======================================================================
```

**When to use:**
- After sending all pending emails
- When starting fresh with new data
- After testing/debugging
- When database has corrupted data

## Recommended Workflow

### Starting Fresh (Complete Reset)

1. **Send pending emails first:**
   ```bash
   python backend/send_all_pending_emails.py
   ```
   - This ensures no emails are lost
   - Wait for all emails to be sent (respects spacing)

2. **Clean up database:**
   ```bash
   python backend/cleanup_all_data.py
   ```
   - Choose to keep or delete daily_usage_stats
   - Type "DELETE ALL DATA" to confirm

3. **Start the pipeline:**
   ```bash
   .\START_HERE.ps1
   ```
   - Choose option 1 (Full Stack 24/7)
   - System will discover new internships
   - Emails will be sent immediately (no approval delay)

### Quick Reset (Using Launcher)

1. **Run launcher:**
   ```powershell
   .\SEND_AND_CLEANUP.ps1
   ```

2. **Choose option 3** (Do both)
   - Sends all pending emails first
   - Then cleans up database
   - All in one go!

3. **Start the pipeline:**
   ```bash
   .\START_HERE.ps1
   ```

## Important Notes

### Email Spacing
- **45-55 minutes** between emails (enforced automatically)
- Script will wait if spacing constraint is active
- You can interrupt (Ctrl+C) and resume later

### Daily Limits
- Default: **15 emails per day**
- Resets at 00:00 UTC
- Script stops when limit is reached
- Run again tomorrow to continue

### Daily Usage Stats
- Tracks emails sent, SMS sent, API usage
- **Recommendation:** Keep this data for history
- Only delete if you want to reset limits

### Error Handling
- Errors are logged and notified via SMS
- Script continues to next email on error
- Failed emails go to retry_queue

### Interrupting Scripts
- Press **Ctrl+C** to stop at any time
- Safe to interrupt - no data corruption
- Can resume later from where you left off

## Troubleshooting

### "No pending drafts found"
- All emails have been sent already
- Or no drafts were created yet
- Check database: `email_drafts` table with status='approved'

### "Daily limit reached"
- You've sent 15 emails today (default limit)
- Wait until tomorrow (00:00 UTC)
- Or increase limit in database: `daily_usage_stats.daily_limit`

### "Spacing constraint active"
- Last email was sent < 45 minutes ago
- Script will wait automatically
- Or run again later

### "Error sending email"
- Check Gmail credentials (token.json)
- Check internet connection
- Check error notification SMS for details
- Error is logged to retry_queue

### Cleanup fails with foreign key errors
- Script deletes in correct order (respects foreign keys)
- If error persists, check database constraints
- May need to manually delete some records first

## Database Schema

After cleanup, these tables will be empty:
- `internships` - Discovered job postings
- `leads` - Extracted email addresses
- `email_drafts` - Generated email drafts
- `followup_queue` - Scheduled follow-up emails
- `event_log` - Pipeline event history
- `retry_queue` - Failed operations to retry

These tables remain intact:
- `scoring_config` - Scoring algorithm configuration
- `daily_usage_stats` - Daily usage tracking (optional)

## Next Steps After Cleanup

1. **Verify database is clean:**
   - Check Supabase dashboard
   - All tables should be empty (except scoring_config)

2. **Start the pipeline:**
   ```bash
   .\START_HERE.ps1
   ```
   - Choose option 1 (Full Stack 24/7)

3. **Monitor progress:**
   - Watch console output
   - Check SMS notifications
   - View dashboard at http://localhost:3000

4. **Emails will be sent automatically:**
   - No approval needed (immediate send)
   - Respects spacing (45-55 min)
   - Respects daily limits (15/day)
   - SMS notifications for each email queued

## Support

If you encounter issues:
1. Check error logs in console output
2. Check SMS notifications for error details
3. Check Supabase logs for database errors
4. Check retry_queue table for failed operations

## Safety Checklist

Before running cleanup:
- ✅ All pending emails have been sent
- ✅ You have a backup (if needed)
- ✅ You understand this is permanent
- ✅ You're ready to start fresh

After cleanup:
- ✅ Verify tables are empty in Supabase
- ✅ scoring_config still has data
- ✅ daily_usage_stats kept (if desired)
- ✅ Ready to run pipeline again
