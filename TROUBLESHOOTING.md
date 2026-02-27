# 🔧 LazyIntern - Troubleshooting Guide

Quick fixes for common issues.

---

## 🚨 Setup Issues

### ❌ "Module not found" or "No module named..."

**Problem:** Python dependencies not installed

**Fix:**
```bash
cd backend
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Still not working?**
```bash
# Reinstall everything
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

---

### ❌ "scrapling: command not found"

**Problem:** Scrapling browsers not installed

**Fix:**
```bash
scrapling install
```

**If that fails:**
```bash
pip install --upgrade scrapling
scrapling install --force
```

---

### ❌ "Virtual environment not activated"

**Problem:** Running Python outside venv

**Fix:**
```bash
cd backend
.\.venv\Scripts\activate
# You should see (.venv) in your prompt
```

**Check if activated:**
```bash
where python
# Should show: backend\.venv\Scripts\python.exe
```

---

## 🔑 API Key Issues

### ❌ "Supabase connection failed"

**Problem:** Wrong credentials or database not set up

**Checklist:**
- [ ] Created Supabase project
- [ ] Ran schema.sql in SQL Editor
- [ ] Copied correct URL (not anon key)
- [ ] Copied Service Role Key (not anon key)
- [ ] Added to .env file
- [ ] No extra spaces in .env

**Test connection:**
```bash
python -c "from core.supabase_db import db; print(db.client.table('internships').select('id').limit(1).execute())"
```

**Common mistakes:**
- Using anon key instead of service role key
- Not running schema.sql
- Typo in .env variable name

---

### ❌ "Groq API error" or "Invalid API key"

**Problem:** Wrong Groq API key

**Checklist:**
- [ ] Created account at https://console.groq.com/
- [ ] Generated API key
- [ ] Key starts with "gsk_"
- [ ] Added to .env as GROQ_API_KEY
- [ ] No quotes around the key in .env

**Test Groq:**
```bash
python -c "from core.config import settings; print(f'Groq key: {settings.groq_api_key[:10]}...')"
```

**Check credits:**
- Go to https://console.groq.com/settings/limits
- Free tier: 30 requests/minute

---

### ❌ "Gmail OAuth failed"

**Problem:** OAuth not configured correctly

**Checklist:**
- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Created OAuth 2.0 credentials (Desktop app)
- [ ] Downloaded JSON file
- [ ] Saved as backend/secrets/gmail_oauth_client.json
- [ ] File path correct in .env

**Fix:**
```bash
# Delete old token
del backend\secrets\gmail_token.json

# Re-authenticate (opens browser)
python -c "from outreach.gmail_client import _build_service; _build_service()"
```

**Common mistakes:**
- Using Web app instead of Desktop app credentials
- Wrong file path in .env
- Not enabling Gmail API in Google Cloud Console

---

### ❌ "Twilio webhook not receiving"

**Problem:** Webhook URL not configured

**Checklist:**
- [ ] ngrok is running: `ngrok http 8000`
- [ ] Copied HTTPS URL (not HTTP)
- [ ] Added to .env as PUBLIC_BASE_URL
- [ ] Configured in Twilio console
- [ ] Backend is running on port 8000

**Test webhook:**
```bash
# Check if backend is running
curl http://localhost:8000/healthz

# Check ngrok URL
curl https://your-ngrok-url.ngrok-free.app/healthz
```

**Twilio webhook URL should be:**
```
https://your-ngrok-url.ngrok-free.app/twilio/webhook
```

---

## 🗄️ Database Issues

### ❌ "Table does not exist"

**Problem:** Schema not executed

**Fix:**
1. Go to Supabase dashboard
2. Click "SQL Editor"
3. Copy all of backend/db/schema.sql
4. Paste and click "Run"
5. Verify 10 tables created in "Table Editor"

**Verify tables:**
```bash
python -c "from core.supabase_db import db; tables = ['internships', 'leads', 'email_drafts', 'daily_usage_stats', 'pipeline_events', 'retry_queue', 'followup_queue', 'quarantine', 'company_domains', 'scoring_config']; [print(f'{t}: OK') for t in tables if db.client.table(t).select('id').limit(1).execute()]"
```

---

### ❌ "Daily limit reached" but it's a new day

**Problem:** Daily usage stats not reset

**Fix:**
```bash
# Reset today's usage
python -c "from core.supabase_db import db, today_utc; db.client.table('daily_usage_stats').delete().eq('date', str(today_utc())).execute(); print('Reset complete')"
```

---

## 🌐 Network Issues

### ❌ "Connection timeout" or "Network error"

**Problem:** Internet connection or firewall

**Checklist:**
- [ ] Internet connection working
- [ ] Firewall not blocking Python
- [ ] Antivirus not blocking requests
- [ ] VPN not interfering

**Test connection:**
```bash
python -c "import httpx; resp = httpx.get('https://google.com'); print(f'Status: {resp.status_code}')"
```

---

### ❌ "SMTP ping getting blocked"

**Problem:** IP blacklisted from too many SMTP checks

**Fix:**
```bash
# Disable SMTP ping temporarily
# Edit .env:
ENABLE_SMTP_PING="false"
```

**Long-term fix:**
- Use a VPN
- Add proxy pool
- Only enable SMTP ping for low-confidence emails

---

## 📧 Email Issues

### ❌ "No internships discovered"

**Problem:** Scraping failed or no sources configured

**Checklist:**
- [ ] data/job_source.json exists
- [ ] URLs in job_source.json are valid
- [ ] Internet connection working
- [ ] Sites not blocking scraper

**Test scraping:**
```bash
python -c "from scraper.scrape_router import discover_and_store; count = discover_and_store(limit=5); print(f'Discovered: {count}')"
```

**Check job sources:**
```bash
type backend\data\job_source.json
```

---

### ❌ "No emails found"

**Problem:** Regex not matching or Hunter not configured

**Checklist:**
- [ ] Job descriptions contain email addresses
- [ ] Hunter API key configured (optional)
- [ ] Pre-score threshold met (≥ 40 for regex, ≥ 60 for Hunter)

**Test email extraction:**
```bash
python -c "from pipeline.email_extractor import extract_from_internship; internship = {'description': 'Contact us at hr@example.com', 'link': 'https://example.com'}; result = extract_from_internship(internship); print(f'Found: {result.email if result else None}')"
```

---

### ❌ "All emails marked invalid"

**Problem:** Validation too strict or disposable domain list issue

**Fix:**
```bash
# Refresh disposable domain list
python -c "from pipeline.email_validator import refresh_disposable_list_if_stale; refresh_disposable_list_if_stale(max_age_days=0); print('List refreshed')"

# Disable SMTP ping
# Edit .env:
ENABLE_SMTP_PING="false"
```

---

### ❌ "Groq not generating drafts"

**Problem:** API error or rate limit

**Checklist:**
- [ ] Groq API key valid
- [ ] Not hitting rate limit (30 req/min)
- [ ] resume.json exists and valid
- [ ] Internet connection working

**Test Groq:**
```bash
python -c "from pipeline.groq_client import generate_draft; from pipeline.pre_scorer import _load_resume; resume = _load_resume(); lead = {'recruiter_name': 'Test', 'email': 'test@example.com'}; internship = {'company': 'TestCo', 'role': 'AI Intern', 'description': 'Test job'}; draft = generate_draft(lead, internship, resume); print(f'Subject: {draft.subject}')"
```

---

## 🎨 Dashboard Issues

### ❌ "Dashboard shows 'Failed to fetch'"

**Problem:** Backend not running or CORS issue

**Checklist:**
- [ ] Backend running on port 8000
- [ ] Can access http://localhost:8000/healthz
- [ ] CORS enabled in backend/api/app.py
- [ ] No firewall blocking port 8000

**Test backend:**
```bash
curl http://localhost:8000/dashboard
```

**Check CORS:**
```bash
# Should see CORS middleware in backend/api/app.py
type backend\api\app.py | findstr CORS
```

---

### ❌ "Dashboard shows old data"

**Problem:** Cache or not refreshing

**Fix:**
- Hard refresh: Ctrl + Shift + R
- Clear browser cache
- Check dashboard auto-refreshes every 5 minutes

---

### ❌ "npm run dev fails"

**Problem:** Node modules not installed

**Fix:**
```bash
cd dashboard
npm install
npm run dev
```

**If still failing:**
```bash
# Delete node_modules and reinstall
rmdir /s /q node_modules
del package-lock.json
npm install
```

---

## 🔄 Pipeline Issues

### ❌ "Pipeline runs but nothing happens"

**Problem:** All leads getting killed by gates

**Debug:**
```bash
# Check daily usage
python -c "from core.supabase_db import db; usage = db.get_or_create_daily_usage(); print(f'Pre-score kills: {usage.pre_score_kills}, Validation fails: {usage.validation_fails}')"

# Check pipeline events
python -c "from core.supabase_db import db; events = db.client.table('pipeline_events').select('event').order('created_at', desc=True).limit(20).execute(); [print(e['event']) for e in events.data]"
```

**Common reasons:**
- Pre-score threshold too high (lower to 30)
- Email validation too strict (disable SMTP ping)
- Full score threshold too high (lower to 50)

---

### ❌ "Emails not sending"

**Problem:** Daily limit reached or Gmail not configured

**Checklist:**
- [ ] Gmail OAuth completed
- [ ] Daily limit not reached
- [ ] Emails approved (or auto-approved)
- [ ] resume.pdf exists

**Check queue:**
```bash
python -c "from core.supabase_db import db; drafts = db.client.table('email_drafts').select('status').execute(); print(f'Generated: {sum(1 for d in drafts.data if d[\"status\"] == \"generated\")}, Approved: {sum(1 for d in drafts.data if d[\"status\"] in [\"approved\", \"auto_approved\"])}, Sent: {sum(1 for d in drafts.data if d[\"status\"] == \"sent\")}')"
```

---

### ❌ "Follow-ups not sending"

**Problem:** Follow-up queue not processed

**Check:**
```bash
python -c "from core.supabase_db import db; followups = db.client.table('followup_queue').select('*').eq('sent', False).execute(); print(f'Pending follow-ups: {len(followups.data)}')"
```

**Manually process:**
```bash
python -c "from outreach.queue_manager import process_followups; process_followups(); print('Follow-ups processed')"
```

---

## 🐛 General Debugging

### Check System Health
```bash
python -c "
from core.supabase_db import db
from core.config import settings
print('✅ Supabase:', 'OK' if settings.supabase_url else '❌ Missing')
print('✅ Groq:', 'OK' if settings.groq_api_key else '❌ Missing')
print('✅ Gmail:', 'OK' if settings.gmail_oauth_client_path else '❌ Missing')
usage = db.get_or_create_daily_usage()
print(f'✅ Daily limit: {usage.emails_sent}/{usage.daily_limit}')
"
```

### View Recent Events
```bash
python -c "
from core.supabase_db import db
events = db.client.table('pipeline_events').select('event, metadata').order('created_at', desc=True).limit(10).execute()
for e in events.data:
    print(f'{e[\"event\"]}: {e.get(\"metadata\", {})}')
"
```

### Check All Tables
```bash
python -c "
from core.supabase_db import db
tables = ['internships', 'leads', 'email_drafts', 'daily_usage_stats']
for t in tables:
    count = db.client.table(t).select('*', count='exact').execute().count
    print(f'{t}: {count} rows')
"
```

---

## 🆘 Still Stuck?

### Collect Debug Info
```bash
# Run this and share output
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Platform: {sys.platform}')

from core.config import settings
print(f'Supabase URL: {settings.supabase_url[:30]}...')
print(f'Groq API: {\"Configured\" if settings.groq_api_key else \"Missing\"}')
print(f'Gmail: {\"Configured\" if settings.gmail_oauth_client_path else \"Missing\"}')

from core.supabase_db import db
usage = db.get_or_create_daily_usage()
print(f'Daily usage: {usage.emails_sent}/{usage.daily_limit}')

import os
print(f'Resume PDF: {\"Found\" if os.path.exists(\"data/resume.pdf\") else \"Missing\"}')
print(f'Job sources: {\"Found\" if os.path.exists(\"data/job_source.json\") else \"Missing\"}')
"
```

### Check Logs
- Backend terminal output
- Browser console (F12)
- Supabase logs (dashboard → Logs)

### Common Commands
```bash
# Restart everything
# 1. Stop all terminals (Ctrl+C)
# 2. Restart backend
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000

# 3. Restart frontend
cd dashboard
npm run dev

# 4. Run one cycle
cd backend
python -m scheduler.cycle_manager --once
```

---

## 📚 Documentation

- **Setup:** backend/SETUP_INSTRUCTIONS.md
- **API Keys:** backend/API_SETUP_GUIDE.md
- **Quick Start:** QUICKSTART.md
- **Commands:** RUN_COMMANDS.md
- **Architecture:** VISUAL_GUIDE.md
- **Pipeline Spec:** logs/final_pipeline.md

---

**Pro Tip:** Most issues are caused by:
1. Missing API keys in .env
2. Database schema not executed
3. Virtual environment not activated
4. Gmail OAuth not completed

Check these first! 🎯
