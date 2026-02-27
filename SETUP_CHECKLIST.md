# LazyIntern Setup Checklist

Use this checklist to make sure everything is configured before running.

## ✅ Prerequisites

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed (for dashboard)
- [ ] Git installed
- [ ] ngrok installed

## ✅ Dependencies

- [ ] Backend dependencies installed
  ```bash
  cd backend
  pip install -r requirements.txt
  ```

- [ ] Dashboard dependencies installed (optional)
  ```bash
  cd dashboard
  npm install
  ```

## ✅ Supabase Setup

- [ ] Supabase project created
- [ ] Database schema applied (`backend/db/schema.sql`)
- [ ] Service role key copied to `.env`
- [ ] Anon key copied to `.env` (optional, for dashboard)

**Verify:** Go to https://kjnksjxsnennhtwjtkdr.supabase.co and check tables exist

## ✅ API Keys

- [ ] Groq API key in `.env`
  - Get from: https://console.groq.com/keys
  
- [ ] Hunter.io API key in `.env`
  - Get from: https://hunter.io/api_keys
  
- [ ] Firecrawl API key in `.env`
  - Get from: https://firecrawl.dev/app/api-keys

## ✅ Twilio Setup

- [ ] Twilio account created
- [ ] Phone number purchased
- [ ] Account SID in `.env`
- [ ] Auth token in `.env`
- [ ] From number in `.env`
- [ ] Your phone number in `.env` (APPROVER_TO_NUMBER)

**Verify:** Send test SMS from Twilio console

## ✅ Gmail Setup

- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth consent screen configured
- [ ] Desktop app credentials downloaded
- [ ] Credentials saved as `secrets/gmail_oauth_client.json`
- [ ] Gmail token generated (`secrets/gmail_token.json`)

**Verify:** Run `python generate_gmail_token.py` successfully

## ✅ Configuration Files

- [ ] `backend/.env` file exists and configured
- [ ] `secrets/gmail_oauth_client.json` exists
- [ ] `secrets/gmail_token.json` exists
- [ ] `backend/data/resume.json` has your resume data
- [ ] `backend/data/keywords.json` configured for your preferences

## ✅ ngrok Setup

- [ ] ngrok installed
- [ ] ngrok account created (optional, for persistent URLs)
- [ ] ngrok running: `ngrok http 8000`
- [ ] PUBLIC_BASE_URL in `.env` updated with ngrok URL

**Verify:** Visit your ngrok URL in browser

## ✅ Twilio Webhook Configuration

- [ ] Twilio webhook URL set to: `https://your-ngrok-url.ngrok-free.dev/twilio/sms`
- [ ] Webhook method set to POST
- [ ] Webhook configured for incoming messages

**Verify:** Send SMS to your Twilio number and check backend logs

## ✅ Test Individual Components

- [ ] Backend health check works
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] Supabase connection works
  ```bash
  cd backend
  python -c "from core.supabase_db import db; print(db.get_or_create_daily_usage())"
  ```

- [ ] Gmail API works
  ```bash
  cd backend
  python -c "from outreach.gmail_client import _build_service; print(_build_service())"
  ```

- [ ] Groq API works
  ```bash
  cd backend
  python -c "from pipeline.groq_client import generate_draft; print('Groq OK')"
  ```

## ✅ Optional: Gmail Push Notifications

- [ ] Google Cloud Pub/Sub topic created
- [ ] Push subscription configured
- [ ] GOOGLE_CLOUD_PROJECT_ID in `.env`
- [ ] Gmail watch setup endpoint called

**Verify:** See `backend/GMAIL_PUBSUB_SETUP.md`

## ✅ Ready to Run!

Once all items are checked:

1. **Start ngrok:**
   ```bash
   ngrok http 8000
   ```

2. **Start backend:**
   ```bash
   cd backend
   python -m uvicorn api.app:app --reload
   ```

3. **Run first cycle:**
   ```bash
   cd backend
   python -m scheduler.cycle_manager --once
   ```

4. **Monitor results:**
   - Check Supabase tables
   - Wait for approval SMS
   - Reply YES/NO
   - Check Gmail sent folder

## 🚀 Quick Start

Or just run:
```bash
START_HERE.bat
```

And follow the menu!

---

## Troubleshooting

If something doesn't work:

1. Check `.env` file has all required values
2. Verify ngrok is running and URL is updated
3. Check backend logs for errors
4. Verify Supabase tables exist
5. Test API keys individually
6. See `RUN_LAZYINTERN.md` for detailed troubleshooting

---

## Need Help?

- Full running guide: `RUN_LAZYINTERN.md`
- Gmail setup: `GMAIL_TOKEN_SETUP.md`
- Pipeline overview: `PIPELINE_COMPARISON_REPORT.md`
- Pub/Sub setup: `backend/GMAIL_PUBSUB_SETUP.md`
