# Deployment Steps for Pipeline Fixes

## ⚠️ IMPORTANT: Run these steps in order

---

## Step 1: Run Database Migration (REQUIRED)

The `twilio_sms_sent` column needs to be added to your Supabase database.

### Option A: Supabase Dashboard (Recommended)
1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the left sidebar
3. Click "New Query"
4. Copy and paste this SQL:

```sql
-- Add SMS tracking column
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

-- Set default value for existing rows
UPDATE daily_usage_stats 
SET twilio_sms_sent = 0 
WHERE twilio_sms_sent IS NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
AND column_name = 'twilio_sms_sent';
```

5. Click "Run" (or press Ctrl+Enter)
6. You should see output showing the new column

### Option B: Using psql CLI
```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" -f backend/migrations/add_sms_tracking.sql
```

---

## Step 2: Verify Migration

Run the test suite to confirm everything is working:

```bash
cd backend
python test_fixes.py
```

Expected output:
```
======================================================================
✅ ALL TESTS PASSED
======================================================================
```

If you see this error:
```
column daily_usage_stats.twilio_sms_sent does not exist
```

Go back to Step 1 and run the migration.

---

## Step 3: Restart the Scheduler

Stop the current scheduler (if running):
```bash
# Press Ctrl+C in the terminal running the scheduler
```

Start the scheduler with the new fixes:
```bash
cd backend
python run_scheduler_24_7.py
```

You should see:
```
======================================================================
LazyIntern 24/7 Scheduler Started
Pipeline will run every 2 hours
Daily stats reset at 00:00 UTC
Press Ctrl+C to stop
======================================================================
```

---

## Step 4: Monitor Logs

Watch for these new log messages to confirm fixes are working:

### Fix 1: Scrape Frequency
```
Scraping source (1): YC Work at a Startup [daily]
Scraping source (2): LinkedIn — AI Internships India [daily]
Skipping monthly source (scraped 15 days ago): OpenAI Careers
```

### Fix 2: Daily Stats Reset (at midnight UTC)
```
======================================================================
Midnight UTC: Resetting daily usage stats
======================================================================
Daily stats initialized for 2026-03-02: emails_sent=0, hunter_calls=0, etc.
Historical data preserved in previous date rows
```

### Fix 3: SMS Limit Enforcement
```
SMS approval sent for draft abc123 (code: D604CD) [14/15]
```

When limit is reached:
```
SMS daily limit reached (15/15), skipping approval SMS
```

---

## Step 5: Verify in Dashboard (Optional)

If you have the dashboard running, check the API:

```bash
curl http://localhost:8000/dashboard
```

Look for the new SMS stats in the response:
```json
{
  "outreach": {
    "smsSentToday": 0,
    "smsDailyLimit": 15,
    ...
  }
}
```

---

## Troubleshooting

### Issue: "column does not exist" error
**Solution**: Run the database migration (Step 1)

### Issue: Sources still scraping every cycle
**Solution**: 
- Check that `backend/data/source_tracking.json` exists
- Wait for second cycle (first cycle always scrapes all sources)
- Check logs for "Skipping" messages

### Issue: Daily stats not resetting
**Solution**:
- Verify scheduler is running with new code
- Check scheduler logs at 00:00 UTC
- Verify timezone is set to UTC in scheduler

### Issue: SMS still sending after limit
**Solution**:
- Verify migration was run successfully
- Check `daily_usage_stats` table has `twilio_sms_sent` column
- Restart scheduler

---

## Verification Checklist

After deployment, verify:

- [ ] Database migration completed successfully
- [ ] Test suite passes (`python test_fixes.py`)
- [ ] Scheduler restarted with new code
- [ ] `source_tracking.json` file exists and is being updated
- [ ] Logs show scrape frequency messages
- [ ] SMS counter appears in logs: `[X/15]`
- [ ] Dashboard API includes SMS stats (if using dashboard)

---

## Rollback (If Needed)

If you need to rollback the changes:

```bash
# Stop scheduler
# Press Ctrl+C

# Revert code changes
git checkout HEAD~1 backend/scraper/scrape_router.py
git checkout HEAD~1 backend/run_scheduler_24_7.py
git checkout HEAD~1 backend/approval/twilio_sender.py
git checkout HEAD~1 backend/core/supabase_db.py

# Restart scheduler with old code
python run_scheduler_24_7.py
```

The database column can stay (it won't hurt anything).

---

## Next Steps

After successful deployment:

1. Monitor for 24 hours to ensure stability
2. Check Supabase logs for any errors
3. Verify daily stats reset at midnight UTC
4. Confirm SMS limit enforcement after 15 messages
5. Review `source_tracking.json` to see which sources are being skipped

---

## Support

If you encounter issues:

1. Check scheduler logs
2. Run `python test_fixes.py` to diagnose
3. Verify database migration: 
   ```sql
   SELECT * FROM daily_usage_stats ORDER BY date DESC LIMIT 1;
   ```
4. Check tracking file: `cat backend/data/source_tracking.json`
