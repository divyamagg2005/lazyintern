# 🎮 LazyIntern - Command Cheat Sheet

Quick reference for all commands you'll need.

---

## 🔧 Initial Setup (One Time)

```bash
# 1. Install Python dependencies
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
scrapling install

# 2. Install Node dependencies
cd ../dashboard
npm install

# 3. Create environment file
cd ../backend
copy .env.example .env
notepad .env  # Fill in your API keys

# 4. Create secrets folder
mkdir secrets

# 5. Test setup
python test_setup.py
```

---

## 🏃 Running the System

### Start Backend API
```bash
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000
```
**Access:** http://localhost:8000/healthz

### Start Frontend Dashboard
```bash
cd dashboard
npm run dev
```
**Access:** http://localhost:3000

### Run One Pipeline Cycle
```bash
cd backend
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

### Run Continuous (Every 5 Hours)
```bash
# Not recommended for testing - use Task Scheduler instead
python -m scheduler.cycle_manager
```

---

## 🧪 Testing Individual Components

### Test All Components
```bash
cd backend
.\.venv\Scripts\activate
python test_setup.py
```

### Test Groq API
```bash
python -c "from pipeline.groq_client import generate_draft; print('Groq OK')"
```

### Test Gmail OAuth (Opens Browser)
```bash
python -c "from outreach.gmail_client import _build_service; _build_service(); print('Gmail OK')"
```

### Test Supabase Connection
```bash
python -c "from core.supabase_db import db; usage = db.get_or_create_daily_usage(); print(f'Emails sent today: {usage.emails_sent}/{usage.daily_limit}')"
```

### Test Email Validation
```bash
python -c "from pipeline.email_validator import validate_email; result = validate_email('test@gmail.com', 80); print(f'Valid: {result.valid}, MX: {result.mx_valid}')"
```

### Test Twilio (If Configured)
```bash
python -c "from approval.twilio_sender import _twilio_client; client = _twilio_client(); print('Twilio OK' if client else 'Not configured')"
```

---

## 📊 Database Operations

### View Daily Usage Stats
```bash
python -c "from core.supabase_db import db; usage = db.get_or_create_daily_usage(); print(f'Emails: {usage.emails_sent}/{usage.daily_limit}, Hunter: {usage.hunter_calls}/15, Groq: {usage.groq_calls}')"
```

### Count Internships
```bash
python -c "from core.supabase_db import db; result = db.client.table('internships').select('*', count='exact').execute(); print(f'Total internships: {result.count}')"
```

### Count Leads
```bash
python -c "from core.supabase_db import db; result = db.client.table('leads').select('*', count='exact').execute(); print(f'Total leads: {result.count}')"
```

### Count Email Drafts
```bash
python -c "from core.supabase_db import db; result = db.client.table('email_drafts').select('*', count='exact').execute(); print(f'Total drafts: {result.count}')"
```

### View Recent Pipeline Events
```bash
python -c "from core.supabase_db import db; events = db.client.table('pipeline_events').select('*').order('created_at', desc=True).limit(10).execute(); import json; print(json.dumps(events.data, indent=2))"
```

### Reset Daily Usage (New Day)
```bash
python -c "from core.supabase_db import db, today_utc; db.client.table('daily_usage_stats').delete().eq('date', str(today_utc())).execute(); print('Daily usage reset')"
```

---

## 🔄 Pipeline Phase Testing

### Test Discovery Only
```bash
python -c "from scraper.scrape_router import discover_and_store; count = discover_and_store(limit=5); print(f'Discovered {count} internships')"
```

### Test Pre-Scoring
```bash
python -c "from pipeline.pre_scorer import pre_score; internship = {'role': 'AI Intern', 'company': 'OpenAI', 'location': 'Remote', 'link': 'https://test.com'}; result = pre_score(internship); print(f'Pre-score: {result.score}')"
```

### Test Email Extraction
```bash
python -c "from pipeline.email_extractor import extract_from_internship; internship = {'description': 'Contact us at hr@example.com', 'link': 'https://example.com'}; result = extract_from_internship(internship); print(f'Found: {result.email if result else None}')"
```

### Test Full Scoring
```bash
python -c "from pipeline.full_scorer import full_score; from pipeline.pre_scorer import _load_resume; resume = _load_resume(); internship = {'role': 'AI Intern', 'company': 'OpenAI', 'description': 'Python ML internship', 'location': 'Remote', 'link': 'https://test.com'}; result = full_score(internship, resume); print(f'Full score: {result.score:.1f}')"
```

---

## 🛠️ Maintenance Commands

### Update Dependencies
```bash
cd backend
.\.venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

### Clear Browser Cache (Scrapling)
```bash
scrapling install --force
```

### Regenerate Gmail Token (If OAuth Fails)
```bash
cd backend
del secrets\gmail_token.json
python -c "from outreach.gmail_client import _build_service; _build_service()"
```

### View Logs (If Configured)
```bash
cd backend
type logs\pipeline.log
```

---

## 🐛 Debugging Commands

### Check Python Version
```bash
python --version
# Should be 3.10 or higher
```

### Check Virtual Environment
```bash
where python
# Should point to backend\.venv\Scripts\python.exe
```

### List Installed Packages
```bash
pip list
```

### Check Environment Variables
```bash
python -c "from core.config import settings; print(f'Supabase URL: {settings.supabase_url[:30]}...')"
```

### Test Internet Connection
```bash
python -c "import httpx; resp = httpx.get('https://google.com'); print(f'Status: {resp.status_code}')"
```

### Check Database Schema
```bash
python -c "from core.supabase_db import db; tables = db.client.table('internships').select('id').limit(1).execute(); print('Schema OK' if tables else 'Schema missing')"
```

---

## 📦 Production Commands

### Build Frontend for Production
```bash
cd dashboard
npm run build
npm run start
```

### Run Backend in Production Mode
```bash
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Export Environment Variables (Linux/Mac)
```bash
export $(cat .env | xargs)
```

### Create Windows Batch File for Scheduler
Create `run_cycle.bat`:
```batch
@echo off
cd C:\path\to\backend
call .venv\Scripts\activate.bat
python -m scheduler.cycle_manager --once
```

---

## 🔐 Security Commands

### Generate New Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Check for Exposed Secrets
```bash
# Make sure .env is in .gitignore
type .gitignore | findstr .env
```

### Verify Twilio Webhook Signature
```bash
python -c "from approval.webhook_handler import validate_twilio_request; print('Webhook validation configured')"
```

---

## 📊 Analytics Commands

### Get Today's Stats
```bash
python -c "from core.supabase_db import db, today_utc; usage = db.get_or_create_daily_usage(today_utc()); print(f'📊 Today:\n  Emails: {usage.emails_sent}/{usage.daily_limit}\n  Hunter: {usage.hunter_calls}/15\n  Groq: {usage.groq_calls}\n  Pre-score kills: {usage.pre_score_kills}\n  Validation fails: {usage.validation_fails}\n  Auto-approvals: {usage.auto_approvals}')"
```

### Get Funnel Stats
```bash
python -c "from core.supabase_db import db; discovered = db.client.table('internships').select('*', count='exact').execute().count; leads = db.client.table('leads').select('*', count='exact').execute().count; drafts = db.client.table('email_drafts').select('*', count='exact').execute().count; sent = db.client.table('email_drafts').select('*', count='exact').eq('status', 'sent').execute().count; print(f'📈 Funnel:\n  Discovered: {discovered}\n  Leads: {leads}\n  Drafts: {drafts}\n  Sent: {sent}\n  Conversion: {(sent/discovered*100):.1f}%' if discovered > 0 else 'No data yet')"
```

### Get Reply Stats
```bash
python -c "from core.supabase_db import db; domains = db.client.table('company_domains').select('reply_history').execute().data; total_pos = sum(d.get('reply_history', {}).get('positive', 0) for d in domains); total_neg = sum(d.get('reply_history', {}).get('negative', 0) for d in domains); total = total_pos + total_neg; print(f'💬 Replies:\n  Positive: {total_pos}\n  Negative: {total_neg}\n  Rate: {(total_pos/total*100):.1f}%' if total > 0 else 'No replies yet')"
```

---

## 🎯 Quick Workflows

### Fresh Start (Reset Everything)
```bash
# WARNING: Deletes all data!
python -c "from core.supabase_db import db; db.client.table('internships').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute(); db.client.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute(); db.client.table('email_drafts').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute(); print('All data cleared')"
```

### Test End-to-End (1 Internship)
```bash
# Discover 1 internship and process it
python -c "from scheduler.cycle_manager import run_cycle; run_cycle()"
```

### Check System Health
```bash
python -c "from core.supabase_db import db; from core.config import settings; print('✅ Supabase:', 'OK' if settings.supabase_url else 'Missing'); print('✅ Groq:', 'OK' if settings.groq_api_key else 'Missing'); print('✅ Gmail:', 'OK' if settings.gmail_oauth_client_path else 'Missing'); usage = db.get_or_create_daily_usage(); print(f'✅ Daily limit: {usage.emails_sent}/{usage.daily_limit}')"
```

---

## 📝 Notes

- Always activate virtual environment before running Python commands
- Use `--once` flag for testing (prevents infinite loops)
- Check dashboard at http://localhost:3000 for visual monitoring
- View Supabase dashboard for raw database access
- Use `Ctrl+C` to stop any running process

---

**Pro Tip:** Create a `run.bat` file in project root:
```batch
@echo off
echo Starting LazyIntern...
start cmd /k "cd backend && .venv\Scripts\activate && python -m uvicorn api.app:app --reload --port 8000"
start cmd /k "cd dashboard && npm run dev"
echo Backend: http://localhost:8000
echo Dashboard: http://localhost:3000
```

Then just double-click `run.bat` to start everything! 🚀
