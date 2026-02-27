# How to Run LazyIntern - Complete Guide

## Prerequisites Checklist

Before running, make sure you have:

- ✅ Python 3.8+ installed
- ✅ All dependencies installed (`pip install -r backend/requirements.txt`)
- ✅ `.env` file configured in `backend/` folder
- ✅ `secrets/gmail_token.json` generated
- ✅ Supabase database set up with schema
- ✅ ngrok running for Twilio webhooks

---

## Step 1: Set Up Supabase Database

### Create Tables

1. Go to your Supabase project: https://kjnksjxsnennhtwjtkdr.supabase.co
2. Click "SQL Editor" in the left sidebar
3. Run the schema from `backend/db/schema.sql`

Or run this command:
```bash
# Copy the schema and paste it in Supabase SQL Editor
cat backend/db/schema.sql
```

---

## Step 2: Start ngrok (Required for Twilio)

Twilio needs a public URL to send webhook notifications.

### Start ngrok:
```bash
ngrok http 8000
```

### Copy the HTTPS URL:
You'll see something like:
```
Forwarding  https://brennan-nongeneralized-hunter.ngrok-free.dev -> http://localhost:8000
```

### Update .env:
Make sure your `.env` has the correct ngrok URL:
```env
PUBLIC_BASE_URL="https://your-ngrok-url.ngrok-free.dev"
```

**Important:** Keep ngrok running in a separate terminal!

---

## Step 3: Start the FastAPI Backend

### Option A: Using the start script (Windows)
```bash
cd backend
start.bat
```

### Option B: Using Python directly
```bash
cd backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Option C: Using the API module
```bash
cd backend
python -m api.app
```

### Verify Backend is Running:
Open browser: http://localhost:8000/health

You should see:
```json
{"status": "ok"}
```

---

## Step 4: Run One Pipeline Cycle

The pipeline cycle discovers internships, scores them, generates emails, and sends them.

### Run a single cycle:
```bash
cd backend
python -m scheduler.cycle_manager --once
```

### What This Does:
1. ✅ Discovers internships from job boards
2. ✅ Deduplicates against Supabase
3. ✅ Pre-scores with keywords
4. ✅ Extracts recruiter emails
5. ✅ Validates emails
6. ✅ Full scoring with historical data
7. ✅ Generates personalized emails with Groq
8. ✅ Sends approval SMS via Twilio
9. ✅ Waits for your approval (or auto-approves after 2h if score ≥90)
10. ✅ Sends emails via Gmail
11. ✅ Processes follow-ups

### Monitor the Output:
You'll see logs like:
```
INFO: Discovered 15 internships
INFO: Pre-scored: 12 passed threshold
INFO: Email found for 8 leads
INFO: Validated 6 emails
INFO: Generated 5 drafts
INFO: Sent approval SMS for draft_id=...
```

---

## Step 5: Approve Emails via SMS

When you receive an SMS from Twilio:
```
LazyIntern Approval Request
Company: Acme AI Labs
Role: ML Research Intern
Score: 85
Reply YES to approve, NO to reject
```

### Reply to the SMS:
- **YES** - Approves and queues for sending
- **NO** - Rejects and adds to quarantine (re-evaluated in 14 days)
- **No reply for 2 hours + score ≥90** - Auto-approves

---

## Step 6: Start the Dashboard (Optional)

The dashboard shows real-time pipeline metrics.

### Start Dashboard:
```bash
cd dashboard
npm install  # First time only
npm run dev
```

### Open Dashboard:
Browser: http://localhost:3000

### Configure Dashboard .env:
Create `dashboard/.env.local`:
```env
SUPABASE_URL="https://kjnksjxsnennhtwjtkdr.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

---

## Step 7: Set Up Gmail Push Notifications (Optional but Recommended)

For real-time reply detection instead of polling.

### Follow the guide:
See `backend/GMAIL_PUBSUB_SETUP.md` for complete instructions.

### Quick setup:
1. Create Google Cloud Pub/Sub topic
2. Create push subscription pointing to your ngrok URL
3. Call the setup endpoint:
```bash
curl http://localhost:8000/gmail/watch/setup
```

---

## Running in Production

### Option 1: Scheduled Cycles with APScheduler

Create `backend/run_scheduler.py`:
```python
from apscheduler.schedulers.blocking import BlockingScheduler
from scheduler.cycle_manager import run_cycle

scheduler = BlockingScheduler()

# Run every 2 hours
scheduler.add_job(run_cycle, 'interval', hours=2)

print("Scheduler started. Running cycle every 2 hours...")
scheduler.start()
```

Run it:
```bash
cd backend
python run_scheduler.py
```

### Option 2: Cron Job (Linux/Mac)

Add to crontab:
```bash
# Run every 2 hours
0 */2 * * * cd /path/to/lazyintern/backend && python -m scheduler.cycle_manager --once
```

### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 2 hours
4. Action: Start a program
   - Program: `python`
   - Arguments: `-m scheduler.cycle_manager --once`
   - Start in: `C:\path\to\lazyintern\backend`

---

## Monitoring and Debugging

### Check Logs:
```bash
# Backend logs
cd backend
python -m api.app

# Watch for errors
tail -f logs/lazyintern.log  # If you set up logging
```

### Check Supabase:
1. Go to Supabase dashboard
2. Check `pipeline_events` table for recent activity
3. Check `daily_usage_stats` for API usage
4. Check `email_drafts` for pending approvals

### Test Individual Components:

**Test Scraper:**
```bash
cd backend
python -c "from scraper.scrape_router import discover_and_store; discover_and_store(limit=5)"
```

**Test Email Validation:**
```bash
cd backend
python -c "from pipeline.email_validator import validate_email; print(validate_email('test@example.com', 80))"
```

**Test Groq:**
```bash
cd backend
python -c "from pipeline.groq_client import generate_draft; print('Groq API working')"
```

---

## Common Issues and Solutions

### Issue: "Module not found"
**Solution:** Make sure you're in the `backend/` directory and dependencies are installed:
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Supabase connection failed"
**Solution:** Check your `.env` file has correct Supabase credentials:
```bash
cat backend/.env | grep SUPABASE
```

### Issue: "Gmail API error"
**Solution:** Regenerate token:
```bash
python generate_gmail_token.py
```

### Issue: "Twilio webhook not receiving"
**Solution:** 
1. Make sure ngrok is running
2. Update `PUBLIC_BASE_URL` in `.env`
3. Restart FastAPI backend

### Issue: "No internships discovered"
**Solution:** Check if job sites are accessible:
```bash
curl https://internshala.com
```

---

## Quick Start Commands

### Full Stack (3 terminals):

**Terminal 1 - ngrok:**
```bash
ngrok http 8000
```

**Terminal 2 - Backend:**
```bash
cd backend
python -m uvicorn api.app:app --reload
```

**Terminal 3 - Run Cycle:**
```bash
cd backend
python -m scheduler.cycle_manager --once
```

**Terminal 4 - Dashboard (optional):**
```bash
cd dashboard
npm run dev
```

---

## What Happens in a Full Cycle?

1. **Discovery** (2-5 min): Scrapes job boards for internships
2. **Processing** (5-10 min): Scores, validates, generates emails
3. **Approval** (manual): You receive SMS and approve/reject
4. **Sending** (1-2 min): Emails sent with 45+ min spacing
5. **Follow-ups** (day 5): Automatic follow-up emails
6. **Replies** (real-time): Detected via Gmail Push, classified, follow-ups cancelled

---

## Success Indicators

You'll know it's working when:
- ✅ Backend responds at http://localhost:8000/health
- ✅ Supabase `internships` table has new rows
- ✅ You receive approval SMS from Twilio
- ✅ Emails appear in your Gmail Sent folder
- ✅ Dashboard shows live metrics
- ✅ `pipeline_events` table logs all activities

---

## Next Steps

1. Run your first cycle: `python -m scheduler.cycle_manager --once`
2. Monitor Supabase for discovered internships
3. Approve emails via SMS
4. Check Gmail sent folder
5. Set up scheduled runs for automation

🚀 You're ready to run LazyIntern!
