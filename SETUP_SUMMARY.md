# ⚡ LazyIntern - Setup Summary

## 🎯 What You Actually Need

### ✅ Required (5 things)
1. **Supabase** - Database (FREE)
2. **Groq** - AI email generation (FREE)
3. **Gmail** - Email sending (FREE)
4. **Twilio** - WhatsApp approval (FREE trial with $15 credit)
5. **ngrok** - Webhook tunnel (FREE)

### ❌ Optional (Can add later)
6. **Hunter.io** - Email discovery ($49/month, has free tier)
7. **Firecrawl** - Advanced scraping ($20/month, has free tier)

---

## 🚀 Minimum Setup (30 Minutes)

```bash
# 1. Install dependencies (5 min)
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
scrapling install

cd ../dashboard
npm install

# 2. Get 5 API keys (15 min)
# - Supabase: https://supabase.com/dashboard
# - Groq: https://console.groq.com/keys
# - Gmail: https://console.cloud.google.com/
# - Twilio: https://console.twilio.com/
# - ngrok: https://ngrok.com/download

# 3. Configure (5 min)
cd backend
copy .env.example .env
notepad .env  # Add all API keys

# 4. Setup database (2 min)
# Go to Supabase → SQL Editor → Run schema.sql

# 5. Add files (1 min)
mkdir secrets
# Copy Gmail OAuth JSON to secrets/gmail_oauth_client.json
# Copy resume PDF to data/resume.pdf

# 6. Start ngrok (1 min)
ngrok http 8000
# Copy URL to .env as PUBLIC_BASE_URL
# Configure Twilio webhook

# 7. Run! (1 min)
run.bat  # Or start manually
```

---

## 📋 .env Configuration

### Required Configuration
```bash
# Database
SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="YOUR_KEY"

# AI Email Generation
GROQ_API_KEY="gsk_YOUR_KEY"

# Gmail Sending
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"

# WhatsApp Approval (REQUIRED)
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"

# Email Validation
ENABLE_SMTP_PING="false"
```

---

## 🎯 Approval Workflow

### How It Works
```
Draft Generated (score: 92)
    ↓
WhatsApp message sent to you
    ↓
You reply "YES DRAFT:abc-123"
    ↓
Email sent!
```

**Auto-approval fallback:**
- If you don't respond within 2 hours
- AND score ≥ 90
- Email is auto-approved and sent

---

## 📊 What Works Without Optional Services

| Feature | Without Hunter | Without Firecrawl | Without Twilio/ngrok |
|---------|----------------|-------------------|----------------------|
| Discovery | ✅ (regex only) | ✅ (HTTP + Playwright) | ✅ |
| Email extraction | ✅ (regex) | ✅ | ✅ |
| Email validation | ✅ | ✅ | ✅ |
| AI drafts | ✅ | ✅ | ✅ |
| Approval | ✅ (auto) | ✅ (auto) | ✅ (auto) |
| Sending | ✅ | ✅ | ✅ |
| Follow-ups | ✅ | ✅ | ✅ |

**Bottom line:** Everything works with just the 3 required services!

---

## 🔍 When to Add Optional Services

### Add Hunter.io When:
- Regex finds < 50% of emails
- You need more email sources
- You're okay spending $49/month

### Add Firecrawl When:
- Scraping fails on JS-heavy sites
- You need 100% success rate
- You're okay spending $20/month

### Add Twilio/ngrok When:
- You want manual approval
- You're sending to important contacts
- You have time to review each email

---

## 💰 Cost Breakdown

### Free Tier (Recommended)
- Supabase: FREE (500MB)
- Groq: FREE (30 req/min)
- Gmail: FREE (250 emails/day)
- **Total: $0/month**

### With Optional Services
- Hunter.io: $49/month (500 searches)
- Firecrawl: $20/month (3000 credits)
- Twilio: ~$15/month (3000 messages)
- **Total: $84/month**

### Recommended Approach
- **Month 1:** Free tier only ($0)
- **Month 2:** Add Hunter if needed ($49)
- **Month 3:** Add Firecrawl if needed ($69)
- **Month 4:** Add Twilio if needed ($84)

---

## 🎯 Quick Decision Tree

```
Do you want to test the system first?
    ↓
   YES → Use free tier only (no Hunter, no Firecrawl, no Twilio)
    |
    ↓
Is regex finding enough emails (>50%)?
    ↓
   YES → Keep free tier
   NO  → Add Hunter.io ($49/month)
    |
    ↓
Is scraping working well (>80% success)?
    ↓
   YES → Keep current setup
   NO  → Add Firecrawl ($20/month)
    |
    ↓
Do you trust the AI scoring?
    ↓
   YES → Keep auto-approval
   NO  → Add Twilio + ngrok (~$15/month)
```

---

## 📝 Files You Need

### Required
- [ ] `backend/.env` (with 3 API keys)
- [ ] `backend/secrets/gmail_oauth_client.json` (from Google Cloud)
- [ ] `backend/data/resume.pdf` (your resume)
- [ ] `backend/data/resume.json` (your info)

### Optional
- [ ] `backend/data/job_source.json` (job board URLs)

### Auto-Generated
- [ ] `backend/secrets/gmail_token.json` (created on first run)
- [ ] `backend/data/disposable_domains.txt` (auto-downloaded)

---

## 🚀 Start Command

```bash
# Simplest way (Windows)
run.bat

# Manual way
# Terminal 1: Backend
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000

# Terminal 2: Dashboard
cd dashboard
npm run dev

# Terminal 3: Pipeline
cd backend
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

---

## ✅ Success Checklist

After first run, you should see:
- [ ] Backend running on http://localhost:8000
- [ ] Dashboard showing data on http://localhost:3000
- [ ] At least 1 internship discovered
- [ ] At least 1 email found
- [ ] At least 1 draft generated
- [ ] At least 1 email sent (if score ≥ 90)

---

## 🆘 Common Issues

### "No emails found"
- Normal! Regex only finds ~50% of emails
- Add Hunter.io for better results
- Or manually add emails to database

### "No internships discovered"
- Check `data/job_source.json` has valid URLs
- Try different job boards
- Check internet connection

### "Emails not sending"
- Check Gmail OAuth completed
- Check daily limit not reached
- Check drafts are approved (or score ≥ 90)

---

## 📚 Documentation

- **START_HERE.md** - Main entry point
- **NGROK_OPTIONAL.md** - Do you need ngrok?
- **QUICKSTART.md** - Detailed setup
- **TROUBLESHOOTING.md** - Fix issues

---

**Bottom line:** Start with the free tier (3 services), add optional services later if needed! 🚀
