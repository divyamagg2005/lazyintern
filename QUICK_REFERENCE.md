# LazyIntern Fixes - Quick Reference Card

## 🚀 Deployment (3 Steps)

```bash
# 1. Run SQL migration in Supabase
ALTER TABLE daily_usage_stats ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

# 2. Test
cd backend && python test_fixes.py

# 3. Restart scheduler
python run_scheduler_24_7.py
```

---

## 📋 What Was Fixed

| Issue | Before | After |
|-------|--------|-------|
| **Scrape Frequency** | All 43 sources every 2h | Daily: every 2h, Monthly: once/month |
| **Daily Stats** | Never reset (broken after day 1) | Reset at midnight UTC daily |
| **SMS Limit** | Unlimited (risk of charges) | 15/day max, enforced |

---

## 🔍 Verification Commands

```bash
# Test all fixes
python backend/test_fixes.py

# Check tracking file
cat backend/data/source_tracking.json

# Query database
psql -c "SELECT date, emails_sent, hunter_calls, twilio_sms_sent FROM daily_usage_stats ORDER BY date DESC LIMIT 3;"

# Watch logs
tail -f backend/logs/scheduler.log  # If logging to file
```

---

## 📊 Expected Log Messages

### Scrape Frequency
```
Scraping source (1): YC Work at a Startup [daily]
Skipping monthly source (scraped 15 days ago): OpenAI Careers
Discovery complete: 26 sources scraped, 15 internships inserted
```

### Daily Reset (at 00:00 UTC)
```
Midnight UTC: Resetting daily usage stats
Daily stats initialized for 2026-03-01: emails_sent=0, hunter_calls=0, etc.
```

### SMS Limit
```
SMS approval sent for draft abc123 (code: D604CD) [14/15]
SMS daily limit reached (15/15), skipping approval SMS
```

---

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| `column twilio_sms_sent does not exist` | Run SQL migration |
| Sources scraping every cycle | Wait for 2nd cycle (1st always scrapes all) |
| Stats not resetting | Check scheduler logs at midnight UTC |
| SMS not limited | Verify migration, restart scheduler |

---

## 📁 Files Changed

```
Modified (6):
- backend/scraper/scrape_router.py
- backend/approval/twilio_sender.py
- backend/core/supabase_db.py
- backend/db/schema.sql
- backend/api/routes/dashboard.py
- backend/run_scheduler_24_7.py

Created (4):
- backend/data/source_tracking.json
- backend/migrations/add_sms_tracking.sql
- backend/test_fixes.py
- FIXES_SUMMARY.md (+ docs)
```

---

## 💾 Database Migration

```sql
-- Run this in Supabase SQL Editor
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

UPDATE daily_usage_stats 
SET twilio_sms_sent = 0 
WHERE twilio_sms_sent IS NULL;
```

---

## 📈 Impact

- **Scraping**: 40% reduction (516 → 312 scrapes/day)
- **API Limits**: Now reset daily (was broken)
- **SMS Cost**: Controlled at 15/day (was unlimited)

---

## ✅ Success Checklist

- [ ] SQL migration run
- [ ] `python test_fixes.py` passes
- [ ] Scheduler restarted
- [ ] Logs show "Skipping" messages
- [ ] Midnight reset works (check at 00:00 UTC)
- [ ] SMS counter shows [X/15]

---

## 🔄 Rollback (If Needed)

```bash
git checkout HEAD~1 backend/scraper/scrape_router.py
git checkout HEAD~1 backend/run_scheduler_24_7.py
git checkout HEAD~1 backend/approval/twilio_sender.py
git checkout HEAD~1 backend/core/supabase_db.py
python run_scheduler_24_7.py
```

---

## 📚 Documentation

- `FIXES_SUMMARY.md` - Detailed explanation
- `DEPLOYMENT_STEPS.md` - Step-by-step guide
- `FIXES_VISUAL_SUMMARY.md` - Visual diagrams
- `QUICK_REFERENCE.md` - This file

---

## 🎯 Key Metrics to Monitor

```
Daily Stats (should reset at midnight):
- emails_sent: 0-15
- hunter_calls: 0-15
- twilio_sms_sent: 0-15

Scraping (should vary by frequency):
- Daily sources: ~26 per cycle
- Weekly sources: ~0 per cycle (except once/week)
- Monthly sources: ~0 per cycle (except once/month)
```

---

## 🆘 Support

If issues persist:
1. Run `python backend/test_fixes.py`
2. Check scheduler logs
3. Verify database migration
4. Review `DEPLOYMENT_STEPS.md`
