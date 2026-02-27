# LazyIntern 24/7 Setup Guide

## Overview

For 24/7 operation, you need 3 components running simultaneously:

1. **ngrok** - Provides public HTTPS URL for Twilio webhooks
2. **Backend API** - FastAPI server to receive webhooks and serve dashboard
3. **Scheduler** - Runs pipeline cycles automatically every 2 hours

---

## Quick Start (Automated)

### Option 1: Use the PowerShell Script (Easiest)

```powershell
.\RUN_24_7.ps1
```

This will automatically open 3 terminal windows with everything running!

---

## Manual Setup (Step by Step)

### Terminal 1: Start ngrok

```powershell
ngrok http 8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.dev`)

**Update `backend/.env`:**
```env
PUBLIC_BASE_URL="https://abc123.ngrok-free.dev"
```

**Keep this terminal running!**

---

### Terminal 2: Start Backend API

```powershell
cd backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Verify it's running:**
- Open browser: http://localhost:8000/health
- Should see: `{"status": "ok"}`

**Keep this terminal running!**

---

### Terminal 3: Start 24/7 Scheduler

```powershell
cd backend
python run_scheduler_24_7.py
```

**What this does:**
- Runs first cycle immediately
- Then runs every 2 hours automatically
- Logs all activity to console

**Keep this terminal running!**

---

## What Happens Every 2 Hours?

The scheduler automatically:

1. ✅ Discovers new internships from job boards
2. ✅ Scores and filters based on your preferences
3. ✅ Finds and validates recruiter emails
4. ✅ Generates personalized emails with AI
5. ✅ Sends you approval SMS via Twilio
6. ✅ Waits for your YES/NO reply
7. ✅ Sends approved emails via Gmail
8. ✅ Schedules follow-ups for day 5
9. ✅ Processes replies and cancels follow-ups if positive

---

## Monitoring

### Check Backend Health:
```powershell
curl http://localhost:8000/health
```

### View Supabase Data:
https://kjnksjxsnennhtwjtkdr.supabase.co

**Key tables to monitor:**
- `internships` - Discovered opportunities
- `email_drafts` - Pending approvals
- `pipeline_events` - Activity log
- `daily_usage_stats` - API usage

### Start Dashboard (Optional):
```powershell
cd dashboard
npm run dev
```
Open: http://localhost:3000

---

## Customizing Schedule

### Change Frequency

Edit `backend/run_scheduler_24_7.py`:

**Every 1 hour:**
```python
scheduler.add_job(scheduled_cycle, 'interval', hours=1)
```

**Every 4 hours:**
```python
scheduler.add_job(scheduled_cycle, 'interval', hours=4)
```

**Every 30 minutes:**
```python
scheduler.add_job(scheduled_cycle, 'interval', minutes=30)
```

**Specific times (e.g., 9 AM and 5 PM daily):**
```python
scheduler.add_job(scheduled_cycle, 'cron', hour='9,17')
```

---

## Windows Task Scheduler (Alternative)

If you don't want to keep terminals open, use Windows Task Scheduler:

### Step 1: Create Backend Service Task

1. Open Task Scheduler
2. Create Basic Task: "LazyIntern Backend"
3. Trigger: At startup
4. Action: Start a program
   - Program: `python`
   - Arguments: `-m uvicorn api.app:app --host 0.0.0.0 --port 8000`
   - Start in: `C:\Users\DIVYAM\Desktop\lazyintern\backend`

### Step 2: Create Scheduler Task

1. Create Basic Task: "LazyIntern Scheduler"
2. Trigger: At startup
3. Action: Start a program
   - Program: `python`
   - Arguments: `run_scheduler_24_7.py`
   - Start in: `C:\Users\DIVYAM\Desktop\lazyintern\backend`

### Step 3: Create ngrok Task

1. Create Basic Task: "LazyIntern ngrok"
2. Trigger: At startup
3. Action: Start a program
   - Program: `ngrok`
   - Arguments: `http 8000`

**Note:** For ngrok, consider getting a paid account for a persistent URL so you don't have to update `.env` every time.

---

## Stopping 24/7 Operation

### If using PowerShell script:
Close all 3 terminal windows (ngrok, backend, scheduler)

### If using Task Scheduler:
1. Open Task Scheduler
2. Find the 3 tasks
3. Right-click → End

---

## Troubleshooting

### Scheduler not running cycles:
Check Terminal 3 for errors. Common issues:
- Missing dependencies: `pip install apscheduler`
- Database connection issues: Check `.env` Supabase credentials

### Backend not receiving webhooks:
1. Check ngrok is running
2. Verify `PUBLIC_BASE_URL` in `.env` matches ngrok URL
3. Restart backend after updating `.env`

### No approval SMS received:
1. Check Twilio credentials in `.env`
2. Verify phone numbers are correct
3. Check backend logs for Twilio errors

### Emails not sending:
1. Check Gmail token exists: `secrets/gmail_token.json`
2. Verify daily limit not exceeded (check `daily_usage_stats` table)
3. Check warmup settings

---

## Best Practices

### 1. Monitor Daily
- Check Supabase `daily_usage_stats` table
- Review `pipeline_events` for errors
- Monitor API usage (Hunter, Groq, Firecrawl)

### 2. Adjust Frequency
- Start with every 4 hours
- Increase to every 2 hours once stable
- Don't go below 1 hour (respect rate limits)

### 3. Keep ngrok Running
- Consider ngrok paid plan for persistent URL
- Or use a cloud deployment (see below)

### 4. Backup Configuration
- Keep `.env` backed up securely
- Document any custom changes

---

## Cloud Deployment (Advanced)

For true 24/7 without keeping your PC on:

### Option 1: Railway
1. Deploy backend to Railway
2. Add environment variables from `.env`
3. Use Railway's public URL (no ngrok needed)

### Option 2: Render
1. Deploy as Web Service
2. Add cron job for scheduler
3. Use Render's public URL

### Option 3: AWS/GCP/Azure
1. Deploy to EC2/Compute Engine/VM
2. Set up systemd services
3. Use elastic IP

---

## Summary

**For 24/7 operation on your PC:**

1. Run: `.\RUN_24_7.ps1`
2. Copy ngrok URL to `.env`
3. Let it run!

**For 24/7 without keeping PC on:**

Use Windows Task Scheduler or deploy to cloud.

**Recommended schedule:** Every 2 hours (12 cycles per day)

---

## Success Indicators

You'll know it's working when:
- ✅ All 3 terminals show activity
- ✅ Supabase tables update every 2 hours
- ✅ You receive approval SMS regularly
- ✅ Emails appear in Gmail Sent folder
- ✅ Dashboard shows increasing metrics

🚀 Your internship search is now automated 24/7!
