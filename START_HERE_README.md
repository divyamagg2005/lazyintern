# 🚀 START HERE - Complete Guide

## 🎯 Quick Start (3 Steps)

### 1. Setup Database (One Time)
```sql
-- In Supabase SQL Editor, run:
backend/db/fresh_setup_quick.sql
```

### 2. Start Everything
```bash
# Double-click this file:
start_here.bat
```

### 3. Go to Sleep 😴
The system runs 24/7 automatically!

---

## 📋 What `start_here.bat` Does

When you run it, it starts 4 services:

### 1. Ngrok (Twilio Webhook)
- **Purpose:** Exposes local API to internet for Twilio SMS replies
- **Window:** "Ngrok - Twilio Webhook"
- **URL:** Check window for `https://[random].ngrok-free.app`
- **Action Needed:** Update Twilio webhook URL (one time)

### 2. Backend API (FastAPI)
- **Purpose:** Handles Twilio webhooks and dashboard API
- **Window:** "Backend API - FastAPI"
- **URL:** http://localhost:8000
- **Endpoints:** 
  - `/twilio/reply` - SMS webhook
  - `/dashboard` - Dashboard data

### 3. Scheduler (Pipeline)
- **Purpose:** Runs pipeline every 2 hours
- **Window:** "Scheduler - Pipeline"
- **What it does:**
  - Discovers internships
  - Extracts emails
  - Scores leads
  - Generates drafts
  - Sends SMS
  - Auto-approves after 2h
  - Sends emails

### 4. Dashboard (Next.js)
- **Purpose:** Visual monitoring interface
- **Window:** "Dashboard - Next.js"
- **URL:** http://localhost:3000
- **Shows:** Real-time stats and metrics

---

## ⏰ Timeline (What Happens)

```
00:00 - You run start_here.bat
00:01 - All 4 services start
00:05 - First pipeline cycle begins
00:30 - Internships discovered
01:00 - Emails extracted
01:30 - Drafts generated
02:00 - SMS sent (up to 15/day)
02:00 - Second cycle begins
02:30 - Auto-approvals start (2h timeout)
03:00 - Emails sent (up to 15/day)
04:00 - Third cycle begins
06:00 - Fourth cycle begins
08:00 - You wake up! 🌅

Result: 15 SMS sent, 15 emails sent, 100+ internships discovered
```

---

## 📊 Expected Results (8 Hours)

| Metric | Expected |
|--------|----------|
| Pipeline Cycles | 4 |
| Internships Discovered | 100-200 |
| Emails Extracted | 30-50 |
| Drafts Generated | 15-25 |
| SMS Sent | 15 (limit) |
| Emails Sent | 15 (limit) |
| Follow-ups Scheduled | 15 |

---

## 🔍 How to Monitor

### While Running
1. **Scheduler Window** - See pipeline activity in real-time
2. **Dashboard** - http://localhost:3000 for visual stats
3. **Phone** - Receive SMS approvals
4. **Gmail** - See sent emails

### When You Wake Up
1. **Run Morning Checklist** - See `MORNING_CHECKLIST.md`
2. **Check Dashboard** - Verify numbers
3. **Review SMS** - Reply YES/NO if needed
4. **Check Gmail** - Look for replies

---

## 📁 Important Files

### Startup
- **start_here.bat** - Main startup script (run this!)
- **START_HERE_README.md** - This file

### Monitoring
- **MORNING_CHECKLIST.md** - Quick health check (5 min)
- **WHAT_TO_EXPECT.md** - Detailed expectations

### Configuration
- **backend/.env** - API keys and settings
- **backend/data/keywords.json** - Scoring keywords
- **backend/data/resume.json** - Your resume data

### Database
- **backend/db/fresh_setup_quick.sql** - Fresh database setup
- **backend/db/schema.sql** - Complete schema with docs

### Documentation
- **FIXES_SUMMARY.md** - All fixes explained
- **AUTO_APPROVAL_SUMMARY.md** - Auto-approval guide
- **DATABASE_CHANGES_SUMMARY.md** - Database changes

---

## ⚙️ Configuration Checklist

Before running, verify these are set in `backend/.env`:

### Required
- [ ] `SUPABASE_URL` - Your Supabase project URL
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - Supabase service key
- [ ] `GROQ_API_KEY` - For AI draft generation
- [ ] `GMAIL_OAUTH_CLIENT_PATH` - Gmail OAuth credentials
- [ ] `GMAIL_TOKEN_PATH` - Gmail access token

### Optional (but recommended)
- [ ] `HUNTER_API_KEY` - For email finding (15 calls/day free)
- [ ] `TWILIO_ACCOUNT_SID` - For SMS approvals
- [ ] `TWILIO_AUTH_TOKEN` - Twilio auth
- [ ] `TWILIO_FROM_NUMBER` - Your Twilio number
- [ ] `APPROVER_TO_NUMBER` - Your phone number

### Optional (advanced)
- [ ] `FIRECRAWL_API_KEY` - For difficult scraping

---

## 🎯 First Time Setup

### Step 1: Database (5 minutes)
```sql
-- 1. Go to Supabase SQL Editor
-- 2. Copy contents of backend/db/fresh_setup_quick.sql
-- 3. Paste and run
-- 4. Verify 10 tables created
```

### Step 2: Gmail (5 minutes)
```bash
# 1. Get OAuth credentials from Google Cloud Console
# 2. Save to secrets/gmail_oauth_client.json
# 3. Run authorization:
cd backend
python authorize_gmail.py
# 4. Follow browser prompts
# 5. Token saved to secrets/gmail_token.json
```

### Step 3: Twilio (5 minutes)
```bash
# 1. Sign up at twilio.com (free trial)
# 2. Get Account SID and Auth Token
# 3. Buy a phone number
# 4. Add to backend/.env
# 5. Run start_here.bat
# 6. Copy ngrok URL from window
# 7. Update Twilio webhook:
#    https://[your-ngrok-url].ngrok-free.app/twilio/reply
```

### Step 4: Test (5 minutes)
```bash
# Run tests
cd backend
python test_fixes.py
python test_auto_approval.py

# Both should show ✅ ALL TESTS PASSED
```

### Step 5: Start! (1 minute)
```bash
# Double-click:
start_here.bat

# Wait for all 4 windows to open
# Check dashboard at http://localhost:3000
```

---

## 🔧 Troubleshooting

### Services Won't Start

**Check:**
- Python installed? `python --version`
- Node installed? `node --version`
- Dependencies installed? `pip install -r backend/requirements.txt`
- Dashboard deps? `cd dashboard && npm install`

### No Internships Discovered

**Check:**
- Network connection working?
- Source tracking file exists? `backend/data/source_tracking.json`
- Scheduler logs show errors?

### No SMS Sent

**Check:**
- Twilio configured in `.env`?
- Phone number verified in Twilio?
- SMS limit not reached? (15/day)

### No Emails Sent

**Check:**
- Gmail token exists? `secrets/gmail_token.json`
- Token not expired? Run `python backend/authorize_gmail.py`
- Email limit not reached? (15/day)

---

## 📊 Dashboard Overview

### Discovery Panel
- Internships discovered today/week
- Pre-score kill rate
- Scraping tier success rates

### Email Panel
- Emails found (regex vs Hunter)
- Hunter API usage
- Validation failure breakdown

### Outreach Panel
- Drafts generated
- Approval rate
- Auto-approvals count
- Emails sent today
- SMS sent today
- Pending follow-ups

### Performance Panel
- Reply rate (over time)
- Funnel visualization
- Top company types

---

## 🎯 Daily Workflow

### Morning (5 minutes)
1. Check if services still running
2. Run `MORNING_CHECKLIST.md`
3. Review SMS and reply if needed
4. Check Gmail for replies

### During Day
- System runs automatically
- Receive SMS approvals
- Reply YES/NO or ignore (auto-approves after 2h)

### Evening (5 minutes)
1. Check dashboard stats
2. Review sent emails
3. Verify services still running

### Weekly (30 minutes)
1. Review overall performance
2. Adjust scoring if needed
3. Update keywords based on results
4. Check reply rates

---

## 🎉 Success Indicators

You'll know it's working when:

- ✅ All 4 service windows stay open
- ✅ Dashboard shows increasing numbers
- ✅ You receive SMS messages
- ✅ Gmail shows sent emails
- ✅ Database has new records
- ✅ No errors in scheduler logs

---

## 📞 Need Help?

### Quick Fixes
1. **Restart everything** - Run `start_here.bat` again
2. **Check logs** - Look at Scheduler window
3. **Run tests** - `python backend/test_fixes.py`
4. **Verify config** - Check `backend/.env`

### Documentation
- `MORNING_CHECKLIST.md` - Quick health check
- `WHAT_TO_EXPECT.md` - Detailed expectations
- `FIXES_SUMMARY.md` - All fixes explained
- `DEPLOYMENT_STEPS.md` - Setup verification

### Common Issues
- Services crash → Restart with `start_here.bat`
- No data → Check database setup
- No SMS → Check Twilio config
- No emails → Check Gmail token

---

## 🚀 You're Ready!

1. ✅ Database set up
2. ✅ Config verified
3. ✅ Tests passing
4. ✅ Run `start_here.bat`
5. ✅ Go to sleep! 😴

Wake up to 15 emails sent and 100+ opportunities discovered! 🌅

---

## 💡 Pro Tips

- **Run during business hours** for better scraping
- **Reply to SMS within 2h** to manually approve high-priority
- **Check dashboard daily** to monitor performance
- **Adjust scoring** based on reply rates
- **Update resume.json** with new skills
- **Fine-tune keywords** based on matches

---

## 🎯 Bottom Line

**One command starts everything:**
```bash
start_here.bat
```

**System runs 24/7 automatically:**
- Discovers internships every 2 hours
- Extracts emails and scores leads
- Generates AI drafts
- Sends SMS approvals
- Auto-approves after 2 hours
- Sends emails with proper delays
- Resets limits at midnight

**You just monitor and optimize!** 🚀
