# Database Changes Summary

## 🎯 What Changed

Only **ONE** new column was added to support SMS tracking:

### New Column
```sql
ALTER TABLE daily_usage_stats 
ADD COLUMN twilio_sms_sent INTEGER DEFAULT 0;
```

That's it! Everything else in the schema was already there.

---

## 📊 Complete Schema Overview

### Tables (10)
1. **internships** - Job opportunities
2. **leads** - Email contacts  
3. **email_drafts** - AI-generated emails
4. **company_domains** - Hunter.io cache
5. **daily_usage_stats** - API limits ⭐ (updated with `twilio_sms_sent`)
6. **pipeline_events** - Audit log
7. **retry_queue** - Failed operations
8. **followup_queue** - Scheduled follow-ups
9. **quarantine** - Rejected leads
10. **scoring_config** - Tunable weights

### What's in daily_usage_stats
```sql
CREATE TABLE daily_usage_stats (
  date DATE PRIMARY KEY,
  emails_sent INTEGER DEFAULT 0,
  daily_limit INTEGER DEFAULT 5,
  hunter_calls INTEGER DEFAULT 0,
  firecrawl_calls INTEGER DEFAULT 0,
  groq_calls INTEGER DEFAULT 0,
  groq_tokens_used INTEGER DEFAULT 0,
  pre_score_kills INTEGER DEFAULT 0,
  validation_fails INTEGER DEFAULT 0,
  auto_approvals INTEGER DEFAULT 0,
  twilio_sms_sent INTEGER DEFAULT 0  ⭐ NEW!
);
```

---

## 🚀 Two Options for Setup

### Option 1: Add Column Only (Recommended)

If you want to keep your existing data:

```sql
-- In Supabase SQL Editor
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

-- Set default for existing rows
UPDATE daily_usage_stats 
SET twilio_sms_sent = 0 
WHERE twilio_sms_sent IS NULL;

-- Verify
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
  AND column_name = 'twilio_sms_sent';
```

**Done!** Your existing data is preserved.

### Option 2: Fresh Setup (Clean Slate)

If you want to start completely fresh:

**Use:** `backend/db/fresh_setup_quick.sql`

This will:
1. Drop all tables
2. Recreate everything
3. Add all indexes
4. Create helpful views
5. Create utility functions
6. Seed scoring_config

**Warning:** This deletes ALL existing data!

---

## 📋 Files Available

### For Migration (Keep Data)
- `backend/migrations/add_sms_tracking.sql` - Just adds the column

### For Fresh Setup (Clean Slate)
- `backend/db/schema.sql` - Complete schema with documentation
- `backend/db/fresh_setup_quick.sql` - Quick version without comments
- `FRESH_DB_SETUP.md` - Detailed setup guide

---

## ✅ Verification

After adding the column, verify it works:

```sql
-- Check column exists
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
  AND column_name = 'twilio_sms_sent';

-- Expected output:
-- twilio_sms_sent | integer | 0

-- Test insert
INSERT INTO daily_usage_stats (date, twilio_sms_sent) 
VALUES (CURRENT_DATE, 5)
ON CONFLICT (date) DO UPDATE 
SET twilio_sms_sent = 5;

-- Check it worked
SELECT date, twilio_sms_sent FROM daily_usage_stats 
WHERE date = CURRENT_DATE;

-- Expected output:
-- 2026-03-01 | 5
```

---

## 🔧 Backend Code Changes

The backend code is already updated to use `twilio_sms_sent`:

### Files Modified
1. `backend/core/supabase_db.py` - Added field to DailyUsage dataclass
2. `backend/approval/twilio_sender.py` - Checks and increments SMS counter
3. `backend/api/routes/dashboard.py` - Exposes SMS stats in API

### How It's Used
```python
# Check SMS limit before sending
usage = db.get_or_create_daily_usage(today)
if usage.twilio_sms_sent >= 15:
    logger.warning("SMS daily limit reached")
    return

# Send SMS
client.messages.create(...)

# Increment counter
db.bump_daily_usage(today, twilio_sms_sent=1)
```

---

## 📊 What This Enables

### SMS Tracking
- ✅ Track SMS sent per day
- ✅ Enforce 15 SMS/day limit
- ✅ Prevent Twilio overages
- ✅ Display in dashboard

### Logs Show
```
SMS approval sent for draft abc123 (code: D604CD) [14/15]
SMS daily limit reached (15/15), skipping approval SMS
```

### Dashboard Shows
```json
{
  "outreach": {
    "smsSentToday": 14,
    "smsDailyLimit": 15
  }
}
```

---

## 🎯 Recommendation

**Use Option 1 (Add Column Only)** unless you specifically want to start fresh.

### Why?
- ✅ Keeps your existing data
- ✅ Faster (one SQL command)
- ✅ Less risky
- ✅ Can always do fresh setup later

### When to Use Option 2?
- You have test data you want to remove
- You want to start with a clean slate
- You're having schema issues
- You want the new indexes and views

---

## 🚀 Quick Start

### If Keeping Data (Recommended)
```sql
-- 1. Add column
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

-- 2. Restart scheduler
# Ctrl+C to stop
python backend/run_scheduler_24_7.py

-- 3. Done!
```

### If Starting Fresh
```sql
-- 1. Run fresh_setup_quick.sql in Supabase
-- (Copy entire file contents and execute)

-- 2. Restart scheduler
# Ctrl+C to stop
python backend/run_scheduler_24_7.py

-- 3. Done!
```

---

## 📞 Support

If you encounter issues:

### "column does not exist" error
```sql
-- Run this:
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;
```

### "table does not exist" error
```sql
-- You need to run the full schema
-- Use: backend/db/fresh_setup_quick.sql
```

### Backend connection errors
```bash
# Restart the scheduler
python backend/run_scheduler_24_7.py
```

---

## ✅ Summary

**Only one column was added:** `twilio_sms_sent`

**Two ways to add it:**
1. Migration (keeps data) - Recommended
2. Fresh setup (clean slate) - If you want to start over

**Backend code:** Already updated and ready

**Next step:** Add the column and restart the scheduler!

🎉 That's it! Your database will be ready for SMS tracking.
