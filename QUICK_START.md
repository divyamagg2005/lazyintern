# LazyIntern - Quick Start Guide

## 🚀 Fastest Way to Run

### Option 1: Use the Menu (Easiest)
```bash
START_HERE.bat
```
Follow the interactive menu!

### Option 2: Manual Commands

**Terminal 1 - Start ngrok:**
```bash
ngrok http 8000
```
Copy the HTTPS URL and update `backend/.env`:
```env
PUBLIC_BASE_URL="https://your-url.ngrok-free.dev"
```

**Terminal 2 - Start Backend:**
```bash
cd backend
python -m uvicorn api.app:app --reload
```

**Terminal 3 - Run Pipeline:**
```bash
cd backend
python -m scheduler.cycle_manager --once
```

---

## 📋 Before First Run

1. ✅ Install dependencies: `pip install -r backend/requirements.txt`
2. ✅ Configure `backend/.env` with all API keys
3. ✅ Generate Gmail token: `python generate_gmail_token.py`
4. ✅ Apply database schema in Supabase SQL Editor
5. ✅ Start ngrok and update PUBLIC_BASE_URL

**Full checklist:** See `SETUP_CHECKLIST.md`

---

## 🎯 What Happens in a Cycle?

1. **Discovers** internships from job boards (2-5 min)
2. **Scores** them based on your preferences (1-2 min)
3. **Finds** recruiter emails (2-3 min)
4. **Validates** emails (1-2 min)
5. **Generates** personalized emails with AI (1-2 min)
6. **Sends** you approval SMS via Twilio
7. **Waits** for your YES/NO reply (or auto-approves after 2h if score ≥90)
8. **Sends** approved emails via Gmail
9. **Schedules** follow-ups for day 5
10. **Detects** replies and cancels follow-ups if positive

---

## 📱 Approving Emails

You'll receive SMS like:
```
LazyIntern Approval Request
Company: Acme AI Labs
Role: ML Research Intern
Score: 85
Reply YES to approve, NO to reject
```

**Reply:**
- `YES` - Approves and sends email
- `NO` - Rejects and quarantines for 14 days
- No reply + score ≥90 - Auto-approves after 2 hours

---

## 🔍 Monitoring

### Check Backend Health:
```bash
curl http://localhost:8000/health
```

### View Supabase Data:
https://kjnksjxsnennhtwjtkdr.supabase.co

**Key Tables:**
- `internships` - Discovered opportunities
- `leads` - Validated email addresses
- `email_drafts` - Generated emails
- `pipeline_events` - Activity log
- `daily_usage_stats` - API usage tracking

### Start Dashboard:
```bash
cd dashboard
npm run dev
```
Open: http://localhost:3000

---

## 🛠️ Common Commands

### Run One Cycle:
```bash
cd backend
python -m scheduler.cycle_manager --once
```

### Start Backend:
```bash
cd backend
python -m uvicorn api.app:app --reload
```

### Generate Gmail Token:
```bash
python generate_gmail_token.py
```

### Test Scraper:
```bash
cd backend
python -c "from scraper.scrape_router import discover_and_store; discover_and_store(limit=5)"
```

### Check Supabase Connection:
```bash
cd backend
python -c "from core.supabase_db import db; print(db.get_or_create_daily_usage())"
```

---

## 📚 Documentation

- **Complete Guide:** `RUN_LAZYINTERN.md`
- **Setup Checklist:** `SETUP_CHECKLIST.md`
- **Gmail Setup:** `GMAIL_TOKEN_SETUP.md`
- **Pipeline Details:** `PIPELINE_COMPARISON_REPORT.md`
- **Pub/Sub Setup:** `backend/GMAIL_PUBSUB_SETUP.md`

---

## ⚡ Production Setup

### Scheduled Runs (Every 2 Hours):

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 2 hours
4. Action: `python -m scheduler.cycle_manager --once`
5. Start in: `C:\path\to\lazyintern\backend`

**Linux/Mac Cron:**
```bash
0 */2 * * * cd /path/to/lazyintern/backend && python -m scheduler.cycle_manager --once
```

---

## 🐛 Troubleshooting

### Backend won't start:
```bash
cd backend
pip install -r requirements.txt
```

### Gmail API error:
```bash
python generate_gmail_token.py
```

### Twilio webhook not working:
1. Check ngrok is running
2. Update PUBLIC_BASE_URL in `.env`
3. Restart backend

### No internships found:
- Check internet connection
- Verify job sites are accessible
- Check `pipeline_events` table for errors

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ Backend responds at http://localhost:8000/health
- ✅ Supabase `internships` table has new rows
- ✅ You receive approval SMS
- ✅ Emails appear in Gmail Sent folder
- ✅ Dashboard shows live metrics

---

## 🎉 You're Ready!

Run your first cycle:
```bash
cd backend
python -m scheduler.cycle_manager --once
```

Or use the menu:
```bash
START_HERE.bat
```

Good luck with your internship search! 🚀
