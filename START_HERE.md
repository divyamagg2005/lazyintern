# 🚀 START HERE - LazyIntern Setup

**Welcome!** This is your starting point for running LazyIntern.

---

## 📖 What is LazyIntern?

An automated internship discovery and outreach pipeline that:
1. **Discovers** internships from job boards
2. **Validates** email addresses
3. **Generates** personalized emails using AI
4. **Gets approval** via WhatsApp (optional)
5. **Sends** emails via Gmail with your resume
6. **Tracks** replies and improves over time

---

## ⚡ Quick Start (30 Minutes)

### Step 1: Install Dependencies (5 min)

```bash
# Backend
cd backend
pip install -r requirements.txt
scrapling install

# Frontend
cd ../dashboard
npm install
```

**Note:** Virtual environment is optional. If you prefer to use venv:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Step 2: Get API Keys (20 min)

You need 4 essential services:

1. **Supabase** (Database) - FREE
   - Go to https://supabase.com/dashboard
   - Create project → Copy URL and Service Role Key

2. **Groq** (AI) - FREE
   - Go to https://console.groq.com/keys
   - Create API Key

3. **Gmail** (Sending) - FREE
   - Go to https://console.cloud.google.com/
   - Create project → Enable Gmail API → Download OAuth JSON

4. **Twilio** (WhatsApp Approval) - FREE trial ($15 credit)
   - Go to https://console.twilio.com/
   - Sign up → Get Account SID and Auth Token
   - Set up WhatsApp sandbox

5. **ngrok** (Webhook Tunnel) - FREE
   - Download from https://ngrok.com/download
   - Required for Twilio webhooks

📖 **Detailed guide:** `backend/API_SETUP_GUIDE.md`

### Step 3: Configure (5 min)

```bash
cd backend
copy .env.example .env
notepad .env  # Fill in your API keys
```

**Required configuration:**
```bash
# Database
SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="YOUR_KEY"

# AI Email Generation
GROQ_API_KEY="gsk_YOUR_KEY"
GROQ_MODEL="llama-3.1-70b-versatile"

# Gmail Sending
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
GMAIL_TOKEN_PATH="secrets/gmail_token.json"
GMAIL_SENDER="me"

# WhatsApp Approval (REQUIRED)
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"

# Email Validation
ENABLE_SMTP_PING="false"
```

### Step 4: Set Up Database (3 min)

1. Go to Supabase dashboard
2. Click "SQL Editor"
3. Copy all of `backend/db/schema.sql`
4. Paste and click "Run"

### Step 5: Add Files (2 min)

```bash
# Create secrets folder
mkdir backend\secrets

# Add Gmail OAuth JSON (downloaded from Google Cloud)
# Save as: backend/secrets/gmail_oauth_client.json

# Add your resume PDF
copy "C:\path\to\resume.pdf" backend\data\resume.pdf
```

### Step 6: Start ngrok (Required for Twilio)

```bash
# Open a new terminal
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Add to backend/.env as PUBLIC_BASE_URL
```

**Configure Twilio Webhook:**
1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Set "When a message comes in" to: `https://abc123.ngrok-free.app/twilio/webhook`
3. Save

### Step 7: Test Setup (1 min)

```bash
cd backend
python test_setup.py
```

Should see all ✅ checks pass!

---

## 🏃 Running the System

Open **4 terminals**:

**Terminal 1 - ngrok (Keep Running):**
```bash
ngrok http 8000
# Copy the HTTPS URL to .env as PUBLIC_BASE_URL
```

**Terminal 2 - Backend:**
```bash
cd backend
python -m uvicorn api.app:app --reload --port 8000
```

**Terminal 3 - Dashboard:**
```bash
cd dashboard
npm run dev
```

**Terminal 4 - Run Pipeline:**
```bash
cd backend
python -m scheduler.cycle_manager --once
```

**Access:**
- Backend: http://localhost:8000/healthz
- Dashboard: http://localhost:3000

---

## 📊 What to Expect

After running one cycle, you should see:

**Console Output:**
```
INFO: Discovered 15 internships
INFO: Pre-scored: 8 passed, 7 killed
INFO: Email found: 5
INFO: Validated: 4 passed, 1 failed
INFO: Groq drafts: 3
INFO: Auto-approved: 2
INFO: Emails sent: 2
```

**Dashboard:**
- Discovery panel: 15 internships today
- Email panel: 5 emails found
- Outreach panel: 2 emails sent
- Performance panel: Full funnel visualization

**Database (Supabase):**
- `internships` table: 15 rows
- `leads` table: 5 rows
- `email_drafts` table: 3 rows

---

## 📚 Documentation

### Essential Reading
1. **QUICKSTART.md** - Detailed setup guide
2. **RUN_COMMANDS.md** - All commands you'll need
3. **TROUBLESHOOTING.md** - Fix common issues

### Reference
4. **VISUAL_GUIDE.md** - Architecture diagrams
5. **PIPELINE_COMPARISON_REPORT.md** - Implementation status
6. **backend/API_SETUP_GUIDE.md** - API key guides
7. **logs/final_pipeline.md** - Complete pipeline spec

---

## 🎯 Success Checklist

After first run:
- [ ] Backend running on port 8000
- [ ] Dashboard showing real data
- [ ] At least 1 internship discovered
- [ ] At least 1 email validated
- [ ] At least 1 draft generated
- [ ] No errors in console

---

## 🐛 Common Issues

### "Module not found"
```bash
cd backend
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### "Supabase connection failed"
- Check you ran schema.sql in Supabase
- Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env

### "Gmail OAuth failed"
- Check secrets/gmail_oauth_client.json exists
- Make sure Gmail API is enabled in Google Cloud Console

### "No internships discovered"
- Check data/job_source.json has valid URLs
- Verify internet connection

📖 **Full troubleshooting:** `TROUBLESHOOTING.md`

---

## 🚀 Next Steps

### Day 1: Test Everything
- Run one cycle
- Check dashboard
- Verify emails sent
- Monitor for errors

### Day 2-3: Monitor
- Check email deliverability
- Review reply rates
- Tune scoring weights

### Day 4-7: Scale Up
- Increase daily limit (5→8→12→15)
- Add more job sources
- Enable WhatsApp approval

### Week 2+: Optimize
- Add proxy pool for scraping
- Tune scoring based on replies
- Set up production scheduler

---

## 💰 Expected Costs

**Free Tier (First Month):**
- Supabase: FREE (500MB database)
- Groq: FREE (30 req/min)
- Gmail: FREE (250 emails/day)
- Twilio: $15 credit (optional)

**Paid (Optional):**
- Hunter.io: $49/month (500 searches)
- Firecrawl: $20/month (3000 credits)

**Total:** $0-$69/month depending on scale

---

## 📈 Success Metrics (After 1 Week)

Target:
- 100+ internships discovered
- 50+ emails validated
- 20+ emails sent
- 2+ positive replies
- < $5 API costs

---

## 🆘 Need Help?

1. Check **TROUBLESHOOTING.md** first
2. Review **QUICKSTART.md** for detailed steps
3. Check console output for errors
4. View Supabase logs in dashboard

---

## 🎓 Understanding the Pipeline

```
Job Boards
    ↓
Discovery (3-tier scraping)
    ↓
Pre-Score (Gate 1: keyword matching)
    ↓
Email Extraction (regex + Hunter)
    ↓
Validation (Gate 2: MX + SMTP)
    ↓
Full Score (Gate 3: weighted scoring)
    ↓
Groq AI (personalized email)
    ↓
Approval (WhatsApp or auto)
    ↓
Gmail Send (with resume)
    ↓
Follow-up (day 5)
    ↓
Reply Detection
```

**3 Kill Gates** filter 90% of leads before expensive API calls!

---

## 🔐 Security Notes

- Never commit `.env` to git (already in .gitignore)
- Keep API keys secret
- Use Service Role Key for Supabase (not anon key)
- Gmail OAuth opens browser for first-time auth
- Twilio webhook signature is verified

---

## 🎯 Ready to Start?

1. Follow **Step 1-6** above
2. Run `python test_setup.py`
3. Start all 3 terminals
4. Open http://localhost:3000
5. Watch the magic happen! ✨

---

**Questions?** Check the documentation files listed above.

**Good luck with your internship search! 🚀**
