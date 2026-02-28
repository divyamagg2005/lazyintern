# Supabase Setup - Step by Step

## 🚨 Current Issue

You're getting: `permission denied for schema public`

This means Supabase needs proper permissions set up before creating tables.

---

## ✅ Solution: 3 Simple Steps

### Step 1: Fix Permissions (2 minutes)

1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project: `kjnksjxsnennhtwjtkdr`
3. Click **SQL Editor** in left sidebar
4. Click **New Query**
5. Copy the entire contents of `backend/db/fix_permissions.sql`
6. Paste into SQL Editor
7. Click **Run** (or press Ctrl+Enter)

**Expected output:**
```
Success. No rows returned
```

---

### Step 2: Create Tables (2 minutes)

1. Still in SQL Editor, click **New Query**
2. Copy the entire contents of `backend/db/fresh_setup_quick.sql`
3. Paste into SQL Editor
4. Click **Run** (or press Ctrl+Enter)

**Expected output:**
```
Success. No rows returned
(followed by verification queries showing tables created)
```

---

### Step 3: Verify Setup (1 minute)

Run this verification query in SQL Editor:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Expected output (10 tables):**
```
company_domains
daily_usage_stats
email_drafts
followup_queue
internships
leads
pipeline_events
quarantine
retry_queue
scoring_config
```

---

### Step 4: Verify Scoring Config (1 minute)

Run this query:

```sql
SELECT * FROM scoring_config ORDER BY key;
```

**Expected output (5 rows):**
```
historical_success_score | 0.10
location_score           | 0.10
relevance_score          | 0.35
resume_overlap_score     | 0.25
tech_stack_score         | 0.20
```

---

## 🎯 After Setup Complete

Once all steps are done, restart your scheduler:

```bash
# Stop the scheduler (Ctrl+C in scheduler window)
# Then restart it:
cd backend
python run_scheduler_24_7.py
```

You should see:
```
LazyIntern 24/7 Scheduler Started
Pipeline will run every 2 hours
Starting scheduled pipeline cycle
Discovery complete: X sources scraped, Y internships inserted
```

---

## 🔍 Troubleshooting

### If Step 1 fails with "permission denied"

You might need to use the Supabase dashboard's built-in admin privileges:

1. Go to **Database** > **Tables** in left sidebar
2. Click **SQL Editor** at top
3. Make sure you're using the **postgres** role (check top right)
4. Try running `fix_permissions.sql` again

### If Step 2 fails with "table already exists"

Your database isn't empty. You need to drop existing tables first:

```sql
-- Drop all tables (WARNING: deletes all data)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO service_role;

-- Then run fix_permissions.sql
-- Then run fresh_setup_quick.sql
```

### If verification shows no tables

The SQL didn't run successfully. Check for error messages in SQL Editor output.

---

## 📞 Quick Test

After setup, test the connection:

```bash
cd backend
python diagnose_supabase.py
```

**Expected output:**
```
✓ Client created successfully
✓ Table exists, rows: 5
✓ Can read daily_usage_stats
```

---

## 🚀 Ready to Go!

Once you see all ✓ checkmarks, your database is ready. Run `start_here.bat` and the pipeline will work!

---

## 🎯 Summary

1. **Fix permissions** - Grant service_role access to schema
2. **Create tables** - Run fresh_setup_quick.sql
3. **Verify** - Check tables and scoring_config exist
4. **Restart scheduler** - Pipeline should work now

Total time: ~5 minutes
