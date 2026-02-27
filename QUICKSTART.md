# 🚀 LazyIntern - Quick Start Guide

**Last Updated:** February 27, 2026

This guide will get you from zero to running the complete pipeline in ~30 minutes.

---

## 📋 Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- **Git** installed
- **Windows** (you're on Windows, commands are Windows-specific)
- **Internet connection** for API calls

---

## ⚡ 5-Minute Setup (Minimum Viable)

### Step 1: Install Python Dependencies

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.\.venv\Scripts\activate

# Install dependencies (takes ~2 minutes)
pip install -r requirements.txt

# Install browser for dynamic scraping
scrapling install
```

### Step 2: Get Essential API Keys

You need these 4 services to run the pipeline:

1. **Supabase** (Database) - https://supabase.com/dashboard
   - Create project → Copy URL and Service Role Key
   
2. **Groq** (AI Email Generation) - https://console.groq.com/keys
   - Sign up → Create API Key
   
3. **Gmail** (Email Sending) - https://console.cloud.google.com/
   - Create project → Enable Gmail API → Download OAuth JSON

4. **Twilio** (WhatsApp Approval) - https://console.twilio.com/
   - Sign up → Get Account SID and Auth Token
   - Set up WhatsApp sandbox

5. **ngrok** (Webhook Tunnel) - https://ngrok.com/download
   - Download and install
   - Required for Twilio webhooks

### Step 3: Configure Environment

```bash
# Copy example file
copy .env.example .env

# Edit .env with your favorite text editor
notepad .env
```

**Minimum required in .env:**
```bash
SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="YOUR_KEY_HERE"
GROQ_API_KEY="gsk_YOUR_KEY_HERE"
GROQ_MODEL="llama-3.1-70b-versatile"
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
GMAIL_TOKEN_PATH="secrets/gmail_token.json"
GMAIL_SENDER="me"
ENABLE_SMTP_PING="false"

# Twilio WhatsApp (REQUIRED)
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"
```

### Step 4: Set Up Database

1. Go to your Supabase project
2. Click "SQL Editor"
3. Open `backend/db/schema.sql` in a text editor
4. Copy all contents
5. Paste into Supabase SQL Editor
6. Click "Run"
7. Verify 10 tables created

### Step 5: Add Gmail OAuth

```bash
# Create secrets folder
mkdir secrets

# Copy your downloaded OAuth JSON file to:
# backend/secrets/gmail_oauth_client.json
```

### Step 6: Add Resume

```bash
# Copy your resume PDF to:
copy "C:\path\to\your\resume.pdf" data\resume.pdf
```

### Step 7: Test Setup

```bash
# Still in backend folder with .venv activated
python test_setup.py
```

Should see:
```
✅ Supabase connection: OK
✅ Groq API: OK
✅ Gmail OAuth: OK (will open browser)
✅ Resume PDF: Found
✅ Database schema: OK
```

---

## 🏃 Running the System

### Option A: Run Complete Pipeline (Recommended for First Test)

Open **3 terminals**:

**Terminal 1 - Backend API:**
```bash
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000
```

**Terminal 2 - Frontend Dashboard:**
```bash
# From project root
cd dashboard
npm install  # First time only
npm run dev
```

**Terminal 3 - Run One Cycle:**
```bash
cd backend
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

### Option B: Test Individual Components

**Test Groq (AI Email Generation):**
```bash
cd backend
.\.venv\Scripts\activate
python -c "from pipeline.groq_client import generate_draft; from pipeline.pre_scorer import _load_resume; resume = _load_resume(); lead = {'recruiter_name': 'Test', 'email': 'test@example.com'}; internship = {'company': 'TestCo', 'role': 'AI Intern', 'description': 'Test job'}; draft = generate_draft(lead, internship, resume); print(f'Subject: {draft.subject}\nBody: {draft.body[:200]}...')"
```

**Test Email Validation:**
```bash
python -c "from pipeline.email_validator import validate_email; result = validate_email('test@gmail.com', 80); print(f'Valid: {result.valid}, MX: {result.mx_valid}')"
```

**Test Supabase:**
```bash
python -c "from core.supabase_db import db; usage = db.get_or_create_daily_usage(); print(f'Daily usage: {usage.emails_sent}/{usage.daily_limit}')"
```

**Test Gmail (Opens Browser):**
```bash
python -c "from outreach.gmail_client import _build_service; service = _build_service(); print('Gmail OAuth successful!')"
```

---

## 📊 What Happens When You Run a Cycle?

```
1. Discovery (Phase 1-2)
   └─ Scrapes internships from job_source.json
   └─ Deduplicates by link/company+role
   └─ Stores in database

2. Pre-Scoring (Phase 3) - Gate 1
   └─ Keyword matching on role/company
   └─ Kills low-quality leads (< 40 score)

3. Email Extraction (Phase 4)
   └─ Tries regex first (free)
   └─ Falls back to Hunter if score ≥ 60

4. Email Validation (Phase 5) - Gate 2
   └─ Format check
   └─ Disposable domain check
   └─ MX record check
   └─ Optional SMTP ping

5. Full Scoring (Phase 7) - Gate 3
   └─ Weighted scoring (resume overlap, tech stack, etc.)
   └─ Kills if score < 60

6. Groq Draft Generation (Phase 8)
   └─ AI generates personalized email
   └─ Creates subject, body, follow-up

7. Approval (Phase 9)
   └─ If Twilio configured: sends WhatsApp approval
   └─ If not: auto-approves high scores (≥ 90)

8. Email Queue (Phase 11)
   └─ Respects warmup schedule (5→15 emails/day)
   └─ Sends via Gmail with resume attached

9. Follow-ups (Phase 12)
   └─ Sends 5-day follow-ups if no reply
```

---

## 🎯 Expected Output (First Run)

**Console Output:**
```
INFO: Discovered 15 internships
INFO: Pre-scored: 8 passed, 7 killed
INFO: Email found (regex): 3
INFO: Email found (Hunter): 2
INFO: Validated: 4 passed, 1 failed
INFO: Full scored: 3 passed, 1 killed
INFO: Groq drafts generated: 3
INFO: Auto-approved: 2 (score ≥ 90)
INFO: Emails sent: 2
```

**Dashboard (http://localhost:3000):**
- Discovery: 15 internships today
- Email: 3 regex, 2 Hunter
- Outreach: 3 drafts, 2 sent
- Performance: Full funnel visualization

**Database (Supabase):**
- `internships` table: 15 rows
- `leads` table: 5 rows
- `email_drafts` table: 3 rows
- `daily_usage_stats` table: 1 row with today's counts

---

## 🔧 Add WhatsApp Approval (Required)

WhatsApp approval is a core feature of LazyIntern for quality control.

### Step 1: Get Twilio Account
1. Go to https://console.twilio.com/
2. Sign up (free trial gives $15 credit)
3. Get Account SID and Auth Token

### Step 2: Set Up WhatsApp Sandbox
1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Send the join message to Twilio's number
3. Note the sandbox number (e.g., +14155238886)

### Step 3: Set Up ngrok (for webhooks)
```bash
# Install ngrok
# Download from https://ngrok.com/download

# Run ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
```

### Step 4: Update .env
```bash
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"  # Your WhatsApp
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"
```

### Step 5: Configure Twilio Webhook
1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Set "When a message comes in" to: `https://abc123.ngrok-free.app/twilio/webhook`
3. Save

Now when a draft is generated, you'll get a WhatsApp message:
```
[LazyIntern]
Company: Startup X
Role: AI Research Intern
Score: 87%
Email: hr@startup.ai

Reply:
YES — approve
NO — reject
PREVIEW — see full email

DRAFT:abc-123-def
```

Reply with "YES DRAFT:abc-123-def" to approve!

---

## 📈 Monitoring & Logs

### View Dashboard
- Open http://localhost:3000
- Auto-refreshes every 5 minutes
- Shows real-time metrics

### Check Database
- Go to Supabase dashboard
- Click "Table Editor"
- View all tables and data

### View API Logs
- Backend terminal shows all API calls
- Look for errors in red

### Check Pipeline Events
- Supabase → `pipeline_events` table
- Shows every step of every internship

---

## 🐛 Common Issues & Fixes

### "Module not found" error
```bash
cd backend
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### "Supabase connection failed"
- Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
- Verify you ran schema.sql in Supabase

### "Gmail OAuth failed"
- Check secrets/gmail_oauth_client.json exists
- Delete secrets/gmail_token.json and try again
- Make sure Gmail API is enabled in Google Cloud Console

### "No internships discovered"
- Check data/job_source.json has valid URLs
- Try running with --limit flag: `python -m scheduler.cycle_manager --once`
- Check internet connection

### "Groq API error"
- Verify GROQ_API_KEY in .env
- Check you have credits: https://console.groq.com/settings/limits
- Try a different model: `GROQ_MODEL="llama-3.1-8b-instant"`

### "SMTP ping getting blocked"
- Set `ENABLE_SMTP_PING="false"` in .env
- This disables SMTP validation (less accurate but safer)

### Dashboard shows "Failed to fetch"
- Make sure backend is running on port 8000
- Check CORS is enabled in backend/api/app.py
- Try refreshing the page

---

## 🎓 Understanding the Data Flow

### Job Sources (data/job_source.json)
```json
{
  "sources": [
    {
      "name": "Internshala",
      "url": "https://internshala.com/internships/...",
      "type": "http"
    }
  ]
}
```

### Resume Data (data/resume.json)
```json
{
  "name": "Your Name",
  "target_roles": ["AI Intern", "ML Intern"],
  "skills": {
    "languages": ["Python", "JavaScript"],
    "frameworks": ["PyTorch", "FastAPI"]
  }
}
```

### Database Tables
1. **internships** - Discovered jobs
2. **leads** - Validated emails
3. **email_drafts** - Generated emails
4. **daily_usage_stats** - API usage tracking
5. **pipeline_events** - Audit log
6. **company_domains** - Hunter cache
7. **quarantine** - Rejected leads
8. **retry_queue** - Failed API calls
9. **followup_queue** - 5-day follow-ups
10. **scoring_config** - Tunable weights

---

## 🚀 Production Deployment

### Option 1: Windows Task Scheduler (Local)

1. Open Task Scheduler
2. Create Basic Task
3. Name: "LazyIntern Pipeline"
4. Trigger: Daily at 08:00
5. Action: Start a program
   - Program: `C:\path\to\backend\.venv\Scripts\python.exe`
   - Arguments: `-m scheduler.cycle_manager --once`
   - Start in: `C:\path\to\backend`
6. Advanced: Repeat every 5 hours

### Option 2: Cloud Deployment (Recommended)

**Backend (Railway/Render):**
1. Push code to GitHub
2. Connect Railway/Render to repo
3. Set environment variables
4. Deploy

**Frontend (Vercel):**
1. Push dashboard folder to GitHub
2. Connect Vercel to repo
3. Set NEXT_PUBLIC_API_BASE_URL
4. Deploy

**Scheduler (Railway Cron):**
1. Add cron job in Railway
2. Schedule: `0 8,13,18 * * *` (8am, 1pm, 6pm)
3. Command: `python -m scheduler.cycle_manager --once`

---

## 📊 Success Metrics (After 1 Week)

- [ ] 100+ internships discovered
- [ ] 50+ emails validated
- [ ] 20+ emails sent
- [ ] 2+ positive replies
- [ ] < $5 API costs
- [ ] 0 Gmail blocks/warnings

---

## 🎯 Next Steps

1. **Day 1:** Run one cycle, verify everything works
2. **Day 2-3:** Monitor dashboard, check email deliverability
3. **Day 4-7:** Gradually increase daily limit (5→8→12→15)
4. **Week 2:** Add more job sources to data/job_source.json
5. **Week 3:** Tune scoring weights based on reply data
6. **Week 4:** Set up production scheduler

---

## 🆘 Need Help?

**Check these files:**
- `backend/SETUP_INSTRUCTIONS.md` - Detailed setup
- `backend/API_SETUP_GUIDE.md` - API key guides
- `PIPELINE_COMPARISON_REPORT.md` - Implementation status
- `logs/final_pipeline.md` - Complete pipeline spec

**Common commands:**
```bash
# Activate virtual environment
cd backend
.\.venv\Scripts\activate

# Run backend
python -m uvicorn api.app:app --reload --port 8000

# Run one cycle
python -m scheduler.cycle_manager --once

# Test setup
python test_setup.py

# Check database
python -c "from core.supabase_db import db; print(db.client.table('internships').select('*').limit(5).execute())"
```

---

**Ready to start? Begin with Step 1! 🚀**
