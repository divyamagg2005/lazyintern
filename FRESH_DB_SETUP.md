# Fresh Database Setup Guide

## 🎯 Overview

This guide will help you set up a completely fresh database with all the latest schema changes.

---

## ⚠️ WARNING

**This will DELETE ALL existing data!**

Make sure you:
- ✅ Have backed up any important data
- ✅ Are ready to start fresh
- ✅ Understand this is irreversible

---

## 📋 What's Included in the New Schema

### Core Tables (9)
1. **internships** - Job opportunities
2. **leads** - Email contacts
3. **email_drafts** - AI-generated emails
4. **company_domains** - Hunter.io cache
5. **daily_usage_stats** - API limits (with `twilio_sms_sent` column)
6. **pipeline_events** - Audit log
7. **retry_queue** - Failed operations
8. **followup_queue** - Scheduled follow-ups
9. **quarantine** - Rejected leads
10. **scoring_config** - Tunable weights (auto-seeded)

### Indexes (15)
- Optimized for fast queries
- Status lookups
- Date range queries
- Foreign key joins

### Views (3)
- `pipeline_summary` - Quick stats
- `draft_summary` - Email status
- `todays_usage` - Current usage

### Functions (2)
- `get_pending_auto_approvals()` - Find drafts waiting for auto-approval
- `check_email_spacing()` - Verify email spacing compliance

---

## 🚀 Deployment Steps

### Step 1: Backup Current Data (Optional)

If you want to keep any data, export it first:

```sql
-- Export internships
COPY internships TO '/tmp/internships_backup.csv' CSV HEADER;

-- Export leads
COPY leads TO '/tmp/leads_backup.csv' CSV HEADER;

-- Export email_drafts
COPY email_drafts TO '/tmp/email_drafts_backup.csv' CSV HEADER;

-- Export daily_usage_stats
COPY daily_usage_stats TO '/tmp/daily_usage_backup.csv' CSV HEADER;
```

### Step 2: Drop All Tables

**In Supabase SQL Editor:**

```sql
-- Drop all tables (CASCADE removes dependencies)
DROP TABLE IF EXISTS pipeline_events CASCADE;
DROP TABLE IF EXISTS retry_queue CASCADE;
DROP TABLE IF EXISTS followup_queue CASCADE;
DROP TABLE IF EXISTS quarantine CASCADE;
DROP TABLE IF EXISTS email_drafts CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS company_domains CASCADE;
DROP TABLE IF EXISTS internships CASCADE;
DROP TABLE IF EXISTS daily_usage_stats CASCADE;
DROP TABLE IF EXISTS scoring_config CASCADE;

-- Drop views
DROP VIEW IF EXISTS pipeline_summary CASCADE;
DROP VIEW IF EXISTS draft_summary CASCADE;
DROP VIEW IF EXISTS todays_usage CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS get_pending_auto_approvals(INTEGER);
DROP FUNCTION IF EXISTS check_email_spacing(INTEGER);

-- Verify all tables are gone
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE';

-- Should return empty result
```

### Step 3: Run Fresh Schema

**Copy the entire contents of `backend/db/schema.sql` and run it in Supabase SQL Editor.**

Or run it via command line:

```bash
# If you have psql installed
psql "postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres" -f backend/db/schema.sql
```

### Step 4: Verify Schema

Run these verification queries:

```sql
-- 1. Check all tables exist (should return 10 tables)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Expected output:
-- company_domains
-- daily_usage_stats
-- email_drafts
-- followup_queue
-- internships
-- leads
-- pipeline_events
-- quarantine
-- retry_queue
-- scoring_config

-- 2. Check scoring_config is seeded (should return 5 rows)
SELECT * FROM scoring_config ORDER BY key;

-- Expected output:
-- historical_success_score | 0.10
-- location_score           | 0.10
-- relevance_score          | 0.35
-- resume_overlap_score     | 0.25
-- tech_stack_score         | 0.20

-- 3. Check twilio_sms_sent column exists
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
  AND column_name = 'twilio_sms_sent';

-- Expected output:
-- twilio_sms_sent | integer | 0

-- 4. Check indexes exist (should return ~15 indexes)
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 5. Check views exist (should return 3 views)
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Expected output:
-- draft_summary
-- pipeline_summary
-- todays_usage

-- 6. Check functions exist (should return 2 functions)
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_type = 'FUNCTION'
ORDER BY routine_name;

-- Expected output:
-- check_email_spacing        | FUNCTION
-- get_pending_auto_approvals | FUNCTION
```

### Step 5: Test the Schema

```sql
-- Test 1: Insert a test internship
INSERT INTO internships (company, role, link, description, location)
VALUES ('Test Company', 'AI Intern', 'https://test.com/job1', 'Test description', 'India');

-- Test 2: Check it was inserted
SELECT * FROM internships;

-- Test 3: Check pipeline_summary view
SELECT * FROM pipeline_summary;

-- Test 4: Check todays_usage view
SELECT * FROM todays_usage;

-- Test 5: Test get_pending_auto_approvals function
SELECT * FROM get_pending_auto_approvals(2);

-- Test 6: Clean up test data
DELETE FROM internships WHERE company = 'Test Company';
```

---

## 🔧 Post-Setup Configuration

### 1. Update Backend Code

Your backend code is already updated to use the new schema. No changes needed!

### 2. Restart Scheduler

```bash
# Stop current scheduler (Ctrl+C)

# Restart with fresh database
cd backend
python run_scheduler_24_7.py
```

### 3. Monitor First Cycle

Watch the logs to ensure everything works:

```bash
# Look for these messages:
Scraping source (1): YC Work at a Startup [daily]
Discovery complete: 26 sources scraped, 15 internships inserted
Pre-scored: 75 | Role: 'AI Intern' | Company: 'Company'
Email found (regex): recruiter@company.com
Email validated successfully: recruiter@company.com
Draft generated: draft_id
SMS approval sent for draft abc123 (code: D604CD) [1/15]
```

---

## 📊 New Features Available

### 1. Useful Views

```sql
-- Quick pipeline overview
SELECT * FROM pipeline_summary;

-- Email draft status
SELECT * FROM draft_summary;

-- Today's API usage
SELECT * FROM todays_usage;
```

### 2. Helpful Functions

```sql
-- Find drafts pending auto-approval
SELECT * FROM get_pending_auto_approvals(2);

-- Check email spacing compliance
SELECT * FROM check_email_spacing(45);
```

### 3. Better Indexes

Queries are now faster:
- Status lookups
- Date range queries
- Foreign key joins
- Event log searches

---

## 🐛 Troubleshooting

### Issue: "relation does not exist"

**Solution:** Run the schema.sql file again. Make sure all tables were created.

```sql
-- Check which tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Issue: "column twilio_sms_sent does not exist"

**Solution:** The schema wasn't applied correctly. Drop and recreate:

```sql
DROP TABLE IF EXISTS daily_usage_stats CASCADE;

-- Then run the CREATE TABLE statement from schema.sql
```

### Issue: "scoring_config is empty"

**Solution:** The INSERT statement didn't run. Run it manually:

```sql
INSERT INTO scoring_config (key, weight, description) VALUES
  ('relevance_score', 0.35, 'Role/title keyword match'),
  ('resume_overlap_score', 0.25, 'Resume keyword overlap with JD'),
  ('tech_stack_score', 0.20, 'Tech stack alignment'),
  ('location_score', 0.10, 'Location preference match'),
  ('historical_success_score', 0.10, 'Past reply rate for similar companies')
ON CONFLICT (key) DO NOTHING;
```

### Issue: Backend errors after schema update

**Solution:** Restart the scheduler to reload the database connection:

```bash
# Stop scheduler (Ctrl+C)
# Start again
python backend/run_scheduler_24_7.py
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] All 10 tables exist
- [ ] scoring_config has 5 rows
- [ ] twilio_sms_sent column exists in daily_usage_stats
- [ ] All 15+ indexes created
- [ ] 3 views created (pipeline_summary, draft_summary, todays_usage)
- [ ] 2 functions created (get_pending_auto_approvals, check_email_spacing)
- [ ] Test insert/select works
- [ ] Backend connects successfully
- [ ] Scheduler runs without errors

---

## 📈 What's Different from Old Schema

### Added
- ✅ `twilio_sms_sent` column in daily_usage_stats
- ✅ 15+ performance indexes
- ✅ 3 helpful views
- ✅ 2 utility functions
- ✅ CASCADE delete on foreign keys
- ✅ Comments for documentation
- ✅ Default values for all columns

### Improved
- ✅ Better index coverage
- ✅ Faster queries
- ✅ Cleaner foreign key relationships
- ✅ Auto-seeded scoring_config
- ✅ More helpful comments

### Same
- ✅ All original tables preserved
- ✅ All original columns preserved
- ✅ Compatible with existing code

---

## 🎉 You're Done!

Your database is now fresh and ready with:
- ✅ All latest schema changes
- ✅ SMS tracking column
- ✅ Performance indexes
- ✅ Helpful views and functions
- ✅ Clean slate for new data

Start the scheduler and watch your pipeline run! 🚀

---

## 📞 Need Help?

If you encounter issues:

1. Check the verification queries above
2. Review the troubleshooting section
3. Ensure backend code is up to date
4. Check scheduler logs for errors
5. Verify Supabase connection settings
