# 🚀 LazyIntern Backend Setup Instructions

## ✅ Phase 1 & 2 Complete!

I've completed:
- ✅ Groq API Integration (email generation)
- ✅ SMTP Email Validation (full ping implementation)
- ✅ Twilio WhatsApp Integration (approval workflow)
- ✅ Gmail API Integration (with resume attachment)
- ✅ Dashboard Backend API (real-time metrics)
- ✅ Frontend connection (removed mock data)

---

## 📋 Setup Checklist

### 1. Install Python Dependencies

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
scrapling install  # Downloads browsers for dynamic scraping
```

---

### 2. Set Up API Keys

Follow `backend/API_SETUP_GUIDE.md` to get all API keys, then create `backend/.env`:

```bash
# Copy example
cp .env.example .env

# Edit with your keys
# Use any text editor to fill in the values
```

**Required keys:**
- Supabase URL + Service Role Key
- Groq API Key
- Twilio Account SID + Auth Token + Phone Numbers
- Gmail OAuth Client JSON

**Optional:**
- Hunter API Key
- Firecrawl API Key

---

### 3. Set Up Supabase Database

1. Go to https://supabase.com/dashboard
2. Create new project
3. Wait for provisioning (~2 min)
4. Go to SQL Editor
5. Copy entire contents of `backend/db/schema.sql`
6. Paste and execute
7. Verify all 10 tables created

---

### 4. Set Up Gmail OAuth

1. Download OAuth client JSON from Google Cloud Console
2. Save as `backend/secrets/gmail_oauth_client.json`
3. Create secrets folder if needed:
   ```bash
   mkdir -p backend/secrets
   ```

---

### 5. Add Resume PDF

```bash
# Add your resume as PDF
cp /path/to/your/resume.pdf backend/data/resume.pdf
```

This will be attached to all outreach emails.

---

### 6. Set Up Twilio WhatsApp (Testing)

1. Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Send the join message to Twilio's WhatsApp number
3. Use the sandbox number in your `.env`:
   ```
   TWILIO_FROM_NUMBER="whatsapp:+14155238886"
   APPROVER_TO_NUMBER="whatsapp:+919811394884"
   ```

---

### 7. Set Up ngrok (for Twilio Webhooks)

```bash
# Install ngrok
# Mac: brew install ngrok
# Windows: Download from https://ngrok.com/download

# Start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Add to backend/.env:
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"
```

Then configure Twilio webhook:
1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Set "When a message comes in" to: `https://abc123.ngrok-free.app/twilio/webhook`

---

## 🏃 Running the System

### Terminal 1: Backend API

```bash
cd backend
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Mac/Linux

python -m uvicorn api.app:app --reload --port 8000
```

Should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test: http://localhost:8000/healthz

---

### Terminal 2: Frontend Dashboard

```bash
# From project root
npm run dev
```

Should see:
```
▲ Next.js running on http://localhost:3000
```

Open: http://localhost:3000

---

### Terminal 3: Run One Pipeline Cycle (Testing)

```bash
cd backend
.venv/Scripts/activate

python -m scheduler.cycle_manager --once
```

This runs one complete cycle:
1. Discovery (scrapes internships)
2. Deduplication
3. Pre-scoring
4. Email extraction (regex + Hunter)
5. Email validation (MX + SMTP)
6. Full scoring
7. Groq draft generation
8. WhatsApp approval request
9. (Wait for your approval)
10. Gmail sending

---

## 🧪 Testing Individual Components

### Test Groq API
```bash
cd backend
python -c "
from pipeline.groq_client import generate_draft
from pipeline.pre_scorer import _load_resume
resume = _load_resume()
lead = {'recruiter_name': 'Test', 'email': 'test@example.com'}
internship = {'company': 'TestCo', 'role': 'AI Intern', 'description': 'Test job'}
draft = generate_draft(lead, internship, resume)
print(f'Subject: {draft.subject}')
print(f'Body: {draft.body[:100]}...')
"
```

### Test Email Validation
```bash
python -c "
from pipeline.email_validator import validate_email
result = validate_email('test@gmail.com', 80)
print(f'Valid: {result.valid}, MX: {result.mx_valid}')
"
```

### Test Supabase Connection
```bash
python -c "
from core.supabase_db import db
usage = db.get_or_create_daily_usage()
print(f'Daily usage: {usage.emails_sent}/{usage.daily_limit}')
"
```

### Test Gmail OAuth (Opens Browser)
```bash
python -c "
from outreach.gmail_client import _build_service
service = _build_service()
print('Gmail OAuth successful!')
"
```

---

## 📊 Dashboard Features

Once backend is running, the dashboard shows:

1. **Overview**: Today's internships, emails sent, reply rate, active retries
2. **Discovery**: Scraping health, tier success rates, Firecrawl usage
3. **Email**: Regex vs Hunter split, validation failures
4. **Outreach**: Drafts generated, approval rate, warmup progress
5. **Performance**: Full funnel, reply rates, top company types
6. **Retries**: Active retry jobs, max-retry failures

---

## 🔄 Production Scheduler

For continuous operation, set up Windows Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 08:00
4. Action: Start a program
   - Program: `C:\path\to\backend\.venv\Scripts\python.exe`
   - Arguments: `-m scheduler.cycle_manager --once`
   - Start in: `C:\path\to\backend`
5. Repeat task every 5 hours (08:00, 13:00, 18:00)

---

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Supabase connection failed"
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`
- Verify database schema was executed

### "Gmail OAuth failed"
- Check `secrets/gmail_oauth_client.json` exists
- Delete `secrets/gmail_token.json` and re-authenticate

### "Twilio webhook not receiving"
- Check ngrok is running
- Verify `PUBLIC_BASE_URL` in `.env` matches ngrok URL
- Check Twilio webhook configuration

### "SMTP ping getting blocked"
- Set `ENABLE_SMTP_PING="false"` temporarily
- Use a VPN or proxy
- Only enable after testing other components

---

## 📈 Next Steps

After everything is working:

1. ✅ Test one complete cycle
2. ✅ Verify WhatsApp approval works
3. ✅ Send one test email via Gmail
4. ✅ Check dashboard shows real data
5. 🔄 Set up production scheduler
6. 📊 Monitor for 24 hours
7. 🚀 Scale up daily limits gradually

---

## 🆘 Need Help?

Check logs:
- Backend: Terminal output from uvicorn
- Frontend: Browser console (F12)
- Pipeline: `backend/logs/` (if configured)

Common issues are usually:
1. Missing API keys in `.env`
2. Supabase schema not executed
3. Gmail OAuth not completed
4. ngrok URL not updated in Twilio

---

**Status: Phase 1 & 2 Complete ✅**
**Next: Get API keys and test the system!**
