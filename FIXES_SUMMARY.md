# LazyIntern Pipeline Fixes - Summary

## Overview
Fixed 3 critical issues identified in the pipeline audit, in priority order.

---

## ✅ ISSUE 1: Scrape Frequency Not Respected (URGENT)

### Problem
All 43 sources were being scraped every cycle, ignoring the `scrape_frequency` field in `job_source.json`. This wasted API calls and risked getting banned from rate-limited sources.

### Solution
Added source tracking system with timestamp-based frequency enforcement.

### Changes Made

**1. Created tracking file: `backend/data/source_tracking.json`**
- Stores last_scraped_at timestamp for each source URL
- Persists across pipeline cycles

**2. Updated `backend/scraper/scrape_router.py`**
- Added `_load_tracking()` - loads tracking data from JSON file
- Added `_save_tracking()` - persists tracking data
- Added `_should_scrape_source()` - checks if source should scrape based on frequency:
  - `daily` → scrape every cycle ✓
  - `weekly` → only if last_scraped_at > 7 days ago
  - `monthly` → only if last_scraped_at > 30 days ago
- Added `_update_tracking()` - updates timestamp after successful scrape
- Modified `discover_and_store()` - checks frequency before scraping each source

### Impact
- **Daily sources (26)**: Scrape every cycle (no change)
- **Weekly sources (0)**: Would scrape once per week
- **Monthly sources (17)**: Scrape once per month only
- **Estimated reduction**: ~40% fewer scrape operations per cycle

### Verification
```bash
cd backend
python test_fixes.py
```

Look for log messages like:
```
Skipping weekly source (scraped 3 days ago): Source Name
Skipping monthly source (scraped 15 days ago): Source Name
```

---

## ✅ ISSUE 2: Daily Usage Stats Not Resetting at Midnight

### Problem
`daily_usage_stats` table accumulated forever. After day 1, Hunter/Gmail/Groq limits stopped working because counters never reset.

### Solution
Added midnight UTC reset job to scheduler that creates new rows for each date.

### Changes Made

**1. Updated `backend/run_scheduler_24_7.py`**
- Added `reset_daily_stats()` function
- Added cron job that runs at 00:00 UTC daily
- Calls `db.get_or_create_daily_usage(today)` to create new row for new date
- Old rows are preserved for historical tracking

**2. Verified `backend/core/supabase_db.py`**
- `get_or_create_daily_usage()` already uses UTC dates correctly
- Creates new row per date automatically
- No changes needed here

### Impact
- Daily limits now reset properly at midnight UTC
- Historical data preserved in previous date rows
- Hunter API: 15 calls/day limit enforced correctly
- Gmail: 15 emails/day limit enforced correctly
- Groq: Token tracking accurate per day

### Verification
```bash
# Check scheduler logs at midnight UTC
# Should see:
Midnight UTC: Resetting daily usage stats
Daily stats initialized for 2026-03-02: emails_sent=0, hunter_calls=0, etc.
Historical data preserved in previous date rows
```

Query database to verify:
```sql
SELECT date, emails_sent, hunter_calls, twilio_sms_sent 
FROM daily_usage_stats 
ORDER BY date DESC 
LIMIT 7;
```

---

## ✅ ISSUE 3: SMS Daily Limit Not Enforced

### Problem
`twilio_sender.py` sent SMS without checking daily limits. Could exceed Twilio trial limits and incur charges.

### Solution
Added SMS tracking column and limit enforcement before sending.

### Changes Made

**1. Updated database schema: `backend/db/schema.sql`**
- Added `twilio_sms_sent INTEGER DEFAULT 0` to `daily_usage_stats` table

**2. Created migration: `backend/migrations/add_sms_tracking.sql`**
- Adds column to existing databases
- Sets default value for existing rows

**3. Updated `backend/core/supabase_db.py`**
- Added `twilio_sms_sent: int` to `DailyUsage` dataclass
- Updated `get_or_create_daily_usage()` to include new field

**4. Updated `backend/approval/twilio_sender.py`**
- Added SMS daily limit check (15 messages/day)
- Checks `usage.twilio_sms_sent >= 15` before sending
- Increments counter after successful send: `db.bump_daily_usage(today, twilio_sms_sent=1)`
- Logs warning if limit reached
- Shows SMS count in logs: `[14/15]`

**5. Updated `backend/api/routes/dashboard.py`**
- Added `smsSentToday` and `smsDailyLimit` to outreach metrics
- Frontend can now display SMS usage

### Impact
- SMS limit of 15/day enforced
- Prevents exceeding Twilio trial limits
- Logs show SMS count: `SMS approval sent [14/15]`
- Dashboard can display SMS usage stats

### Verification

**Run migration first:**
```sql
-- In Supabase SQL Editor
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;
```

**Then test:**
```bash
cd backend
python test_fixes.py
```

**Check logs when SMS is sent:**
```
SMS approval sent for draft abc123 (code: D604CD) [14/15]
```

**If limit reached:**
```
SMS daily limit reached (15/15), skipping approval SMS
```

---

## Frontend Changes

### Dashboard API Updated
The `/dashboard` endpoint now includes SMS stats in the `outreach` section:

```json
{
  "outreach": {
    "smsSentToday": 14,
    "smsDailyLimit": 15,
    ...
  }
}
```

### Frontend Component (Optional Enhancement)
If you want to display SMS stats in the dashboard, update `backend/dashboard/components/OutreachPanel.tsx`:

```tsx
// Add to the component:
<div className="metric">
  <span className="label">SMS Sent Today</span>
  <span className="value">{data.smsSentToday} / {data.smsDailyLimit}</span>
</div>
```

---

## Installation & Deployment

### 1. Run Database Migration
```bash
# In Supabase SQL Editor, run:
cat backend/migrations/add_sms_tracking.sql
```

### 2. Test All Fixes
```bash
cd backend
python test_fixes.py
```

### 3. Restart Scheduler
```bash
# Stop current scheduler (Ctrl+C)
# Then restart:
python run_scheduler_24_7.py
```

### 4. Monitor Logs
Watch for these messages:
- `Scraping source (1): YC Work at a Startup [daily]`
- `Skipping monthly source (scraped 15 days ago): OpenAI Careers`
- `Midnight UTC: Resetting daily usage stats`
- `SMS approval sent for draft abc123 (code: D604CD) [14/15]`
- `SMS daily limit reached (15/15), skipping approval SMS`

---

## Files Changed

### Modified Files (8)
1. `backend/scraper/scrape_router.py` - Added frequency tracking
2. `backend/run_scheduler_24_7.py` - Added midnight reset job
3. `backend/approval/twilio_sender.py` - Added SMS limit enforcement
4. `backend/core/supabase_db.py` - Added twilio_sms_sent field
5. `backend/db/schema.sql` - Added twilio_sms_sent column
6. `backend/api/routes/dashboard.py` - Added SMS stats to API

### New Files (4)
7. `backend/data/source_tracking.json` - Source scrape timestamps
8. `backend/migrations/add_sms_tracking.sql` - Database migration
9. `backend/test_fixes.py` - Verification test suite
10. `FIXES_SUMMARY.md` - This document

---

## Expected Behavior After Fixes

### Scraping
- **First cycle**: All sources scrape (no tracking data yet)
- **Second cycle**: Only daily sources scrape
- **After 7 days**: Weekly sources scrape again
- **After 30 days**: Monthly sources scrape again

### Daily Stats
- **00:00 UTC**: New row created for new date
- **Old rows**: Preserved for historical analysis
- **Limits**: Reset to 0 for new day

### SMS Sending
- **SMS 1-14**: Sent normally with counter in logs
- **SMS 15**: Last one sent, logs show `[15/15]`
- **SMS 16+**: Blocked with warning message
- **Next day**: Counter resets to 0 at midnight UTC

---

## Rollback Plan (If Needed)

If any issues occur, you can rollback:

### Rollback Issue 1 (Scrape Frequency)
```bash
# Delete tracking file
rm backend/data/source_tracking.json

# Revert scrape_router.py to previous version
git checkout HEAD~1 backend/scraper/scrape_router.py
```

### Rollback Issue 2 (Daily Reset)
```bash
# Revert scheduler
git checkout HEAD~1 backend/run_scheduler_24_7.py
```

### Rollback Issue 3 (SMS Limit)
```sql
-- Remove column (optional, doesn't hurt to keep it)
ALTER TABLE daily_usage_stats DROP COLUMN IF EXISTS twilio_sms_sent;
```

```bash
# Revert files
git checkout HEAD~1 backend/approval/twilio_sender.py
git checkout HEAD~1 backend/core/supabase_db.py
```

---

## Testing Checklist

- [ ] Run `python backend/test_fixes.py` - all tests pass
- [ ] Run SQL migration in Supabase
- [ ] Restart scheduler
- [ ] Check logs for frequency messages
- [ ] Wait for midnight UTC, verify stats reset
- [ ] Send 15+ SMS approvals, verify limit enforcement
- [ ] Check dashboard API includes SMS stats
- [ ] Verify source_tracking.json is being updated

---

## Performance Impact

### Before Fixes
- 43 sources scraped every 2 hours = 516 scrapes/day
- Daily limits never reset after day 1
- Unlimited SMS sending (risk of charges)

### After Fixes
- ~26 daily sources scraped every 2 hours = 312 scrapes/day
- 17 monthly sources scraped once/month = 17 scrapes/month
- Daily limits reset properly at midnight
- SMS limited to 15/day

### Savings
- **40% reduction** in scrape operations
- **Proper limit enforcement** prevents API overages
- **SMS cost control** prevents unexpected charges

---

## Support

If you encounter issues:

1. Check logs: `backend/logs/` (if logging to file)
2. Run test suite: `python backend/test_fixes.py`
3. Verify database migration: `SELECT * FROM daily_usage_stats LIMIT 1;`
4. Check tracking file: `cat backend/data/source_tracking.json`

---

## Next Steps (Optional Improvements)

1. **Reply Detection** - Implement Gmail polling/Pub/Sub for reply tracking
2. **Scrape Frequency UI** - Add dashboard to view/edit source frequencies
3. **SMS Analytics** - Track approval rates by SMS vs auto-approval
4. **Dynamic Limits** - Adjust daily limits based on account age/reputation
