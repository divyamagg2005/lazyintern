# 🚨 QUICK FIX: Permission Denied Error

## The Problem

Your scheduler is failing with:
```
permission denied for schema public
```

## The Solution (5 Minutes)

### 1. Open Supabase SQL Editor

Go to: https://supabase.com/dashboard/project/kjnksjxsnennhtwjtkdr/sql

### 2. Run Permission Fix

Copy and paste this into SQL Editor and click **Run**:

```sql
-- Grant schema permissions
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;

-- Grant to postgres
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;
```

### 3. Create Tables

Open `backend/db/fresh_setup_quick.sql` in your editor, copy ALL contents, paste into SQL Editor, and click **Run**.

### 4. Verify

Run this query:

```sql
SELECT * FROM scoring_config;
```

Should return 5 rows. If yes, you're done! ✅

### 5. Restart Scheduler

Go to your scheduler window, press Ctrl+C to stop, then run:

```bash
cd backend
python run_scheduler_24_7.py
```

Should now work without errors! 🎉

---

## Files to Use

1. **Permission fix**: `backend/db/fix_permissions.sql` (or copy from above)
2. **Create tables**: `backend/db/fresh_setup_quick.sql`
3. **Detailed guide**: `SUPABASE_SETUP_STEPS.md`

---

## Expected Result

After fix, scheduler should show:

```
LazyIntern 24/7 Scheduler Started
Starting scheduled pipeline cycle
Discovery complete: 26 sources scraped, 15 internships inserted
✓ No more permission errors
```

---

## Need More Help?

See `SUPABASE_SETUP_STEPS.md` for detailed troubleshooting.
