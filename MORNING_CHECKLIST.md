# Morning Checklist ☀️

## 🎯 Quick 5-Minute Health Check

Run through this checklist when you wake up to verify everything worked overnight.

---

## ✅ 1. Services Running (30 seconds)

Check if all 4 windows are still open:

- [ ] **Ngrok** window (Twilio webhook)
- [ ] **Backend API** window (FastAPI on port 8000)
- [ ] **Scheduler** window (Pipeline cycles)
- [ ] **Dashboard** window (Next.js on port 3000)

**If any crashed:** Run `start_here.bat` again

---

## ✅ 2. Dashboard Quick Check (1 minute)

Open http://localhost:3000 and verify:

- [ ] **Discovery Panel** shows internships > 0
- [ ] **Email Panel** shows emails extracted > 0
- [ ] **Outreach Panel** shows emails sent = 15
- [ ] **Outreach Panel** shows SMS sent = 15
- [ ] **No error messages** displayed

**If all zeros:** Check scheduler logs for errors

---

## ✅ 3. Database Quick Query (1 minute)

Run this in Supabase SQL Editor:

```sql
SELECT 
  (SELECT COUNT(*) FROM internships WHERE created_at > NOW() - INTERVAL '8 hours') as new_internships,
  (SELECT COUNT(*) FROM leads WHERE created_at > NOW() - INTERVAL '8 hours') as new_leads,
  (SELECT COUNT(*) FROM email_drafts WHERE created_at > NOW() - INTERVAL '8 hours') as new_drafts,
  (SELECT emails_sent FROM daily_usage_stats WHERE date = CURRENT_DATE) as emails_sent,
  (SELECT twilio_sms_sent FROM daily_usage_stats WHERE date = CURRENT_DATE) as sms_sent;
```

**Expected:**
- new_internships: 50-200
- new_leads: 20-50
- new_drafts: 10-25
- emails_sent: 15
- sms_sent: 15

**If all zeros:** Pipeline didn't run - check scheduler

---

## ✅ 4. Phone Check (1 minute)

- [ ] Received **~15 SMS messages** from Twilio
- [ ] Messages show format: "LazyIntern (75%) AI Intern at Company..."
- [ ] Each has a short code: "Reply: YES ABC123"

**If no SMS:** Check Twilio config in `.env`

---

## ✅ 5. Gmail Check (1 minute)

Open Gmail Sent folder:

- [ ] **~15 emails sent** overnight
- [ ] All have **resume.pdf attached**
- [ ] Subject lines are **personalized**
- [ ] No **bounce/error messages**

**If no emails:** Check Gmail token and config

---

## ✅ 6. Scheduler Logs (1 minute)

Look at Scheduler window for:

- [ ] **"Cycle completed successfully"** messages (should see 4)
- [ ] **No red ERROR messages**
- [ ] **"Discovery complete: X sources scraped"** messages
- [ ] **"Email sent"** messages

**If errors:** Read error messages and check config

---

## 🎯 Quick Status Summary

### ✅ All Good (Everything Working)
```
✓ All 4 services running
✓ Dashboard shows data
✓ Database has new records
✓ 15 SMS sent
✓ 15 emails sent
✓ No errors in logs

Action: Nothing! Let it continue running.
```

### ⚠️ Partial Success (Some Issues)
```
⚠ Some services crashed
⚠ Dashboard shows partial data
⚠ <15 SMS or emails sent
⚠ Some errors in logs

Action: Check specific issues below.
```

### ❌ Not Working (Major Issues)
```
✗ Services crashed
✗ Dashboard shows no data
✗ Database empty
✗ No SMS or emails sent
✗ Many errors in logs

Action: Restart everything and check config.
```

---

## 🔧 Quick Fixes

### Issue: Services Crashed

```bash
# Restart everything
start_here.bat
```

### Issue: No Internships Discovered

```bash
# Check source tracking
cat backend/data/source_tracking.json

# If all sources have recent timestamps, it's working
# Wait for next cycle or manually trigger
cd backend
python -c "from scheduler.cycle_manager import run_cycle; run_cycle()"
```

### Issue: No SMS Sent

```bash
# Check Twilio config
cd backend
python -c "from core.config import settings; print(f'Twilio SID: {settings.twilio_account_sid[:10]}...')"

# If empty, add to .env file
```

### Issue: No Emails Sent

```bash
# Check Gmail token
ls -la secrets/gmail_token.json

# If missing, run:
cd backend
python authorize_gmail.py
```

### Issue: Database Empty

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- If empty, run fresh_setup_quick.sql
```

---

## 📊 Expected Numbers (After 8 Hours)

| Metric | Expected | Acceptable | Problem |
|--------|----------|------------|---------|
| Internships | 100-200 | 50-100 | <50 |
| Leads | 30-50 | 15-30 | <15 |
| Drafts | 15-25 | 10-20 | <10 |
| SMS Sent | 15 | 10-15 | <10 |
| Emails Sent | 15 | 10-15 | <10 |
| Cycles | 4 | 3-4 | <3 |

---

## 🎯 Next Steps Based on Results

### If Everything Worked (✅)

1. **Review SMS** - Reply YES/NO to any you want to override
2. **Check Gmail** - Look for any replies (unlikely after 8h)
3. **Let it run** - System will continue automatically
4. **Check again tonight** - See cumulative results

### If Partial Success (⚠️)

1. **Fix specific issues** - Use quick fixes above
2. **Restart services** - Run `start_here.bat`
3. **Monitor next cycle** - Watch scheduler logs
4. **Adjust if needed** - Check config files

### If Not Working (❌)

1. **Check all config** - Verify `.env` file
2. **Run tests** - `python backend/test_fixes.py`
3. **Check database** - Run `fresh_setup_quick.sql` if needed
4. **Restart everything** - Run `start_here.bat`
5. **Monitor closely** - Watch first cycle complete

---

## 📞 Detailed Troubleshooting

If quick fixes don't work, see:
- **WHAT_TO_EXPECT.md** - Detailed expectations
- **FIXES_SUMMARY.md** - All fixes explained
- **DEPLOYMENT_STEPS.md** - Setup verification

---

## 🎉 Success Criteria

You can go back to sleep if:
- ✅ All services running
- ✅ Dashboard shows data
- ✅ 15 SMS sent
- ✅ 15 emails sent
- ✅ No errors in logs
- ✅ Database has records

**The system is working! Let it continue running.** 🚀

---

## ⏰ Daily Routine

### Morning (5 minutes)
1. Run this checklist
2. Review SMS and reply if needed
3. Check Gmail for replies
4. Verify services still running

### Evening (5 minutes)
1. Check dashboard for daily stats
2. Review sent emails
3. Check for any replies
4. Verify services still running

### Weekly (30 minutes)
1. Review overall performance
2. Adjust scoring weights if needed
3. Update keywords based on results
4. Check reply rates and optimize

---

## 💤 Sleep Well, Wake Up to Results!

The system is designed to run 24/7. This checklist helps you verify everything worked while you slept. Most days, you'll just see ✅ across the board and can continue with your day! 🌟
