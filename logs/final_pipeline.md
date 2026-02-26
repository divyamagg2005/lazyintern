# 🧠 LazyIntern — FINAL PRODUCTION PIPELINE v2
### Groq · Scrapling · Firecrawl · Hunter · Supabase · Twilio · Gmail API

---

## SYSTEM OBJECTIVE

> Discover internships → Deduplicate → Pre-score cheap → Extract + validate emails → Full score → Personalize with Groq → Human approval → Send 15/day → Detect replies → Feed back into scoring.

---

## ⚙️ GLOBAL SYSTEM GUARDS

```python
MAX_EMAILS_PER_DAY              = 15
HUNTER_DAILY_LIMIT              = 15
FIRECRAWL_DAILY_LIMIT           = 10
FIRECRAWL_PER_DOMAIN_WEEK       = 2
SCRAPE_BATCH_LIMIT              = 50
MIN_EMAIL_INTERVAL_MIN          = 45
AUTO_APPROVE_THRESHOLD          = 90
TWILIO_TIMEOUT_HOURS            = 2
EMAIL_WARMUP_PHASE              = True

# UPDATED — split thresholds for regex vs Hunter
PRE_SCORE_THRESHOLD_REGEX       = 40   # try free regex extraction
PRE_SCORE_THRESHOLD_HUNTER      = 60   # only spend Hunter credit above this
```

All counters are DB-backed in `daily_usage_stats`. Nothing runs from in-memory state.

---

## 🗃️ COMPLETE DATABASE SCHEMA

```sql
-- Core internship data
CREATE TABLE internships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company TEXT NOT NULL,
  role TEXT NOT NULL,
  link TEXT UNIQUE NOT NULL,
  description TEXT,
  location TEXT,
  posted_date DATE,
  source_url TEXT,
  pre_score INTEGER,
  full_score INTEGER,
  status TEXT DEFAULT 'discovered',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validated leads with emails
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  recruiter_name TEXT,
  email TEXT NOT NULL,
  source TEXT,
  confidence INTEGER,
  verified BOOLEAN DEFAULT FALSE,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Domain-level Hunter cache
CREATE TABLE company_domains (
  domain TEXT PRIMARY KEY,
  emails JSONB,
  hunter_called BOOLEAN DEFAULT FALSE,
  last_checked TIMESTAMPTZ,
  reply_history JSONB,
  firecrawl_calls_this_week INTEGER DEFAULT 0,
  week_start DATE
);

-- Generated email drafts
CREATE TABLE email_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  followup_body TEXT,
  status TEXT DEFAULT 'generated',
  approval_sent_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quarantine for rejected leads
CREATE TABLE quarantine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id),
  draft_id UUID REFERENCES email_drafts(id),
  rejected_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  re_evaluate_after DATE,
  re_evaluated BOOLEAN DEFAULT FALSE,
  re_evaluation_score INTEGER
);

-- Daily API usage tracking
CREATE TABLE daily_usage_stats (
  date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
  emails_sent INTEGER DEFAULT 0,
  daily_limit INTEGER DEFAULT 5,
  hunter_calls INTEGER DEFAULT 0,
  firecrawl_calls INTEGER DEFAULT 0,
  groq_calls INTEGER DEFAULT 0,
  groq_tokens_used INTEGER DEFAULT 0,
  pre_score_kills INTEGER DEFAULT 0,
  validation_fails INTEGER DEFAULT 0,
  auto_approvals INTEGER DEFAULT 0
);

-- Full pipeline event log
CREATE TABLE pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  event TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NEW — Retry queue for failed API calls
CREATE TABLE retry_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phase TEXT NOT NULL,        -- 'groq' | 'twilio' | 'gmail' | 'hunter'
  payload JSONB NOT NULL,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  next_retry_at TIMESTAMPTZ,
  last_error TEXT,
  resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NEW — Follow-up email queue
CREATE TABLE followup_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES email_drafts(id),
  lead_id UUID REFERENCES leads(id),
  send_after DATE,            -- sent_at + 5 days
  sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NEW — Tunable scoring weights (no code edits needed)
CREATE TABLE scoring_config (
  key TEXT PRIMARY KEY,
  weight FLOAT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default scoring weights
INSERT INTO scoring_config VALUES
  ('relevance_score',          0.35, 'Role/title keyword match'),
  ('resume_overlap_score',     0.25, 'Resume keyword overlap with JD'),
  ('tech_stack_score',         0.20, 'Tech stack alignment'),
  ('location_score',           0.10, 'Location preference match'),
  ('historical_success_score', 0.10, 'Past reply rate for similar companies');
```

---

## 📄 resume.json Structure

This file lives in `data/resume.json` and is the input to every Groq prompt.
Define it clearly before writing any pipeline code.

```json
{
  "name": "Divyam",
  "target_roles": ["AI Intern", "ML Intern", "Research Intern", "Data Intern"],
  "skills": {
    "languages": ["Python", "JavaScript", "SQL"],
    "frameworks": ["PyTorch", "TensorFlow", "FastAPI", "Next.js"],
    "tools": ["Supabase", "Docker", "Git", "Groq API"],
    "domains": ["NLP", "Computer Vision", "LLM fine-tuning", "RAG"]
  },
  "projects": [
    {
      "name": "Project Name",
      "description": "One sentence description",
      "tech": ["Python", "PyTorch"],
      "impact": "Quantified result if any"
    }
  ],
  "education": {
    "degree": "B.Tech Computer Science",
    "college": "Your College",
    "year": "2nd Year",
    "gpa": "X.X"
  },
  "preferred_locations": ["Remote", "Bangalore", "Mumbai"],
  "preferred_company_types": ["startup", "AI lab", "YC", "research org"]
}
```

Groq reads this structure to find specific overlaps with each job description.
The more precise this file is, the more genuine the emails feel.

---

## 🔹 PHASE 0 — SCHEDULER

**Runs:** 3x per day (08:00, 13:00, 18:00)
**File:** `scheduler/cycle_manager.py`

```
On each cycle start:
  1. Load daily_usage_stats for today
  2. Check followup_queue for pending follow-ups → process first
  3. Check quarantine for re-evaluation candidates → process
  4. If emails_sent >= daily_limit → run discovery only, skip outreach
  5. If all limits hit → exit, log skip reason
  6. Else → begin discovery cycle
```

---

## 🔹 PHASE 1 — 3-TIER SCRAPING ENGINE

**File:** `scraper/scrape_router.py`

### Tier 1 — Scrapling HTTP Fetch
- Concurrency: 5–8 workers
- Delay: 2–3 sec + random jitter
- Respect robots.txt strictly

**If DOM populated → extract**

### Tier 2 — Scrapling DynamicFetcher (Playwright)
Triggered when DOM is empty or JS-rendered.
**File:** `scraper/dynamic_fetcher.py`

### Tier 3 — Firecrawl Fallback
**File:** `scraper/firecrawl_fetcher.py`

Only triggers when:
- Both Scrapling tiers failed
- `firecrawl_calls_today < FIRECRAWL_DAILY_LIMIT`
- `firecrawl_calls_this_week_for_domain < FIRECRAWL_PER_DOMAIN_WEEK`

If limits hit → skip, log `scrape_failed`.

### Proxy Rotation ← NEW
**File:** `scraper/http_fetcher.py`

Running 50 URLs × 3 cycles/day will trigger IP blocks within a week.
Add a rotating proxy pool from the start:

```python
import itertools

PROXY_POOL = [
    "http://proxy1:port",
    "http://proxy2:port",
    # add free rotating proxies or use a paid pool
]
proxy_cycle = itertools.cycle(PROXY_POOL)

def get_next_proxy():
    return next(proxy_cycle)
```

Use a new proxy per domain, not per request.
Start with free proxies; upgrade to paid (Oxylabs, Brightdata) if blocks increase.

### Extract Internship Data
From successful scrape, extract:
- Company name, Role title, Job link
- Full description, Location, Posted date, Source URL

**Store in `internships` → status = `discovered`**
**Log to `pipeline_events` → event = `discovered`**

---

## 🔹 PHASE 2 — DEDUPLICATION

**File:** `pipeline/deduplicator.py`

```python
Skip if ANY of:
  - Same company + role exists in DB
  - Same job link seen before
  - status in (processed, emailed, rejected, quarantined)
```

**Log → event = `deduplicated`**

---

## 🔹 PHASE 3 — PRE-SCORING (CHEAP GATE)

**File:** `pipeline/pre_scorer.py`

Zero API calls. Pure local keyword matching on title + company + location only.

```python
score = 0
if any kw in ["AI", "ML", "data", "NLP", "research", "LLM"] in role_title:
    score += 40
if company_type == "startup" or "YC" in company_tags:
    score += 20
if location in preferred_locations:
    score += 20
if company in past_success_list:
    score += 20
```

**Gate logic — UPDATED with split thresholds:**
```python
if score < PRE_SCORE_THRESHOLD_REGEX (40):
    status = 'low_priority'
    log pre_score_kills++
    STOP — nothing runs

elif score >= PRE_SCORE_THRESHOLD_REGEX (40):
    proceed to regex email extraction

# Hunter only triggered if score >= 60 (separate check in Phase 6)
```

**Log → event = `pre_scored`**

---

## 🔹 PHASE 4 — FREE EMAIL EXTRACTION (REGEX)

**File:** `pipeline/email_extractor.py`

1. Regex over raw HTML + visible text
2. Normalize obfuscated patterns (`[at]`, `(dot)`, `_at_`)
3. Filter by recruiter keywords: `hr`, `hiring`, `talent`, `recruiter`, `careers`
4. Match domain against company domain

**If email found:**
- Store in `leads`, source = `regex`
- Skip Hunter
- Go to Phase 5 (validation)

**If no email found:**
- Check pre_score >= PRE_SCORE_THRESHOLD_HUNTER (60) before trying Hunter
- If score 40–59 → mark `no_email_low_score` → STOP (won't qualify for Hunter)
- If score >= 60 → go to Phase 6 (Hunter)

**Log → event = `email_found_regex` or `no_email_found`**

---

## 🔹 PHASE 5 — EMAIL VALIDATION

**File:** `pipeline/email_validator.py`

Runs for ALL emails — regex-found and Hunter-found. Protects Gmail sender reputation.

**Step 1 — Format Check**
```python
import re
RFC_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

**Step 2 — Disposable Domain Blocklist**
```python
# data/disposable_domains.txt
with open('data/disposable_domains.txt') as f:
    DISPOSABLE = set(f.read().splitlines())
if domain in DISPOSABLE:
    reject
```

**Step 3 — MX Record Check**
```python
import dns.resolver
try:
    records = dns.resolver.resolve(domain, 'MX')
    mx_valid = True
except:
    mx_valid = False
    reject
```

**Step 4 — SMTP Ping (only if confidence < 90%)**
```python
# EHLO handshake only — no actual email sent
import smtplib
server = smtplib.SMTP(mx_host)
server.ehlo()
code, _ = server.rcpt(email)
smtp_valid = (code == 250)
```

**If any check fails:**
- Mark lead `invalid_email`
- Log reason
- Increment `validation_fails`
- STOP

**Log → event = `email_valid` or `email_invalid`**

---

## 🔹 PHASE 6 — HUNTER CREDIT SHIELD

**File:** `pipeline/hunter_client.py`

Only reached if: regex found nothing AND pre_score >= 60.

**Step 1 — Extract domain**
```
jobs.startup.ai → startup.ai
```

**Step 2 — Domain cache check**
```python
result = db.query("SELECT * FROM company_domains WHERE domain = ?", domain)
if result and result.hunter_called:
    reuse stored emails → skip to Phase 5 validation
```

**Step 3 — Daily guard**
```python
if hunter_calls_today >= HUNTER_DAILY_LIMIT:
    mark `hunter_limit_reached` → STOP
```

**Step 4 — Hunter API call**
One call per new domain. Filter:
- Roles: `hr@`, `hiring@`, `recruiter@`, `talent@`
- Confidence > 80%

Cache result in `company_domains`.

**Step 5 — Optional verification**
Only if confidence < 90% AND daily budget remaining.

**After Hunter → always run through Phase 5 validation.**

**On Hunter API failure → log to `retry_queue`:**
```python
retry_queue.insert({
    'phase': 'hunter',
    'payload': {'domain': domain, 'internship_id': id},
    'next_retry_at': now + 15 minutes
})
```

---

## 🔹 PHASE 7 — FULL SCORING ENGINE

**File:** `pipeline/full_scorer.py`

Weights loaded from `scoring_config` table — tunable from dashboard.

```python
# Load weights from DB (not hardcoded)
weights = db.query("SELECT key, weight FROM scoring_config")

full_score = (
    relevance_score          * weights['relevance_score'] +
    resume_overlap_score     * weights['resume_overlap_score'] +
    tech_stack_score         * weights['tech_stack_score'] +
    location_score           * weights['location_score'] +
    historical_success_score * weights['historical_success_score']
)
```

`historical_success_score` comes from `company_domains.reply_history` — this is what the feedback loop populates.

**If full_score < 60 → mark `low_priority` → STOP**
**If full_score >= 60 → proceed to Groq**

**Log → event = `full_scored`**

---

## 🔹 PHASE 8 — GROQ PERSONALIZATION ENGINE

**File:** `pipeline/groq_client.py`

### System Prompt (static string — enables Groq prompt caching)
```
You are an expert cold email writer for internship outreach.
Candidate: {resume.name}
Skills: {resume.skills}
Projects: {resume.projects}
Education: {resume.education}
Tone: professional, concise, genuine. Never sound like a template.
Format:
  - Subject line (max 8 words)
  - Email body (150-200 words, 3 paragraphs)
  - Follow-up template (75 words, day 5 if no reply)
Output as JSON: {subject, body, followup}
```

### User Prompt (dynamic per lead)
```
Company: {company}
Role: {role}
Description summary: {first 300 words of description}
Recruiter: {recruiter_name or "Hiring Team"}
Score breakdown: {score_details}
```

**On Groq API failure → log to retry_queue:**
```python
retry_queue.insert({
    'phase': 'groq',
    'payload': {'lead_id': id, 'internship_id': internship_id},
    'max_attempts': 3,
    'next_retry_at': now + 5 minutes
})
```

**Store result in `email_drafts` → status = `generated`**
**Also create entry in `followup_queue`:**
```python
followup_queue.insert({
    'draft_id': draft.id,
    'lead_id': lead.id,
    'send_after': today + 5 days
})
```

**Log → event = `draft_generated`**

---

## 🔹 PHASE 9 — TWILIO HUMAN APPROVAL

**Files:** `approval/twilio_sender.py`, `approval/webhook_handler.py`, `approval/auto_approver.py`

### Security — Twilio Signature Verification ← NEW
```python
# approval/webhook_handler.py
from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException

validator = RequestValidator(TWILIO_AUTH_TOKEN)

async def validate_twilio_request(request: Request):
    signature = request.headers.get('X-Twilio-Signature', '')
    url = str(request.url)
    params = await request.form()
    
    if not validator.validate(url, dict(params), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
```

Every incoming webhook is verified before processing. Prevents fake YES/NO injections.

### SMS Format
```
[LazyIntern]
Company: Startup X
Role: AI Research Intern
Score: 87%
Email: hr@startup.ai
Source: Hunter

Reply:
YES — approve
NO — reject
PREVIEW — see full email
```

### Webhook Response Handling
- `YES` → status = `approved` → enters email queue
- `NO` → status = `rejected` → moved to quarantine
- `PREVIEW` → SMS back with full email body → await YES/NO

### Auto-Approve Rule
```python
# approval/auto_approver.py — runs every 30 min
pending = db.query("""
    SELECT * FROM email_drafts
    WHERE status = 'generated'
    AND approval_sent_at < NOW() - INTERVAL '2 hours'
""")

for draft in pending:
    if draft.full_score >= AUTO_APPROVE_THRESHOLD:
        draft.status = 'auto_approved'
        email_queue.add(draft)
        daily_usage_stats.auto_approvals++
    else:
        draft.status = 'approval_timeout'
        # defer to next cycle
```

**On Twilio SMS failure → log to retry_queue:**
```python
retry_queue.insert({
    'phase': 'twilio',
    'payload': {'draft_id': draft.id},
    'next_retry_at': now + 2 minutes
})
```

**Log → event = `approval_sent` / `approved` / `rejected` / `auto_approved`**

---

## 🔹 PHASE 10 — QUARANTINE QUEUE

**File:** `outreach/quarantine_manager.py`

All `NO` rejections enter quarantine — nothing is permanently discarded.

```python
quarantine.insert({
    'lead_id': lead.id,
    'draft_id': draft.id,
    're_evaluate_after': today + 14 days
})
```

### Re-evaluation (runs every scheduler cycle)
```python
candidates = db.query("""
    SELECT * FROM quarantine
    WHERE re_evaluate_after <= CURRENT_DATE
    AND re_evaluated = FALSE
""")

for candidate in candidates:
    new_score = full_scorer.score(candidate.lead)
    candidate.re_evaluated = True
    candidate.re_evaluation_score = new_score
    
    if new_score >= 75:
        # Re-enter at Groq phase with updated score
        pipeline.resume_from_groq(candidate.lead)
```

---

## 🔹 PHASE 11 — EMAIL QUEUE

**File:** `outreach/queue_manager.py`

### Warmup Schedule
```python
# scheduler/warmup.py
def get_daily_limit(account_created_date):
    days_active = (today - account_created_date).days
    if days_active <= 3:   return 5
    if days_active <= 7:   return 8
    if days_active <= 11:  return 12
    return 15
```

### Sending Rules
```python
if emails_sent_today >= daily_limit:
    stop

gap = timedelta(minutes=45 + random.randint(0, 10))
if last_sent_at + gap > now:
    wait
```

### Gmail API Send
**File:** `outreach/gmail_client.py`

```python
def send_email(draft, lead):
    message = create_message(
        to=lead.email,
        subject=draft.subject,
        body=draft.body,
        attachment='data/resume.pdf'
    )
    
    try:
        gmail.users().messages().send(userId='me', body=message).execute()
        draft.status = 'sent'
        draft.sent_at = now
        daily_usage_stats.emails_sent++
        log_event('sent', draft.internship_id)
        
    except Exception as e:
        retry_queue.insert({
            'phase': 'gmail',
            'payload': {'draft_id': draft.id},
            'last_error': str(e),
            'next_retry_at': now + 10 minutes
        })
```

---

## 🔹 PHASE 12 — FOLLOW-UP ENGINE ← NEW

**File:** `outreach/queue_manager.py` (follow-up section)

Runs at the start of every scheduler cycle.

```python
due_followups = db.query("""
    SELECT fq.*, ed.followup_body, l.email
    FROM followup_queue fq
    JOIN email_drafts ed ON fq.draft_id = ed.id
    JOIN leads l ON fq.lead_id = l.id
    WHERE fq.send_after <= CURRENT_DATE
    AND fq.sent = FALSE
    AND ed.status != 'replied_positive'  -- don't follow up if they replied
    AND ed.status != 'replied_negative'
""")

for followup in due_followups:
    gmail_client.send_followup(followup)
    followup.sent = True
    followup.sent_at = now
```

Follow-ups are skipped automatically if a reply was already detected.

---

## 🔹 PHASE 13 — REPLY DETECTION LOOP

**Files:** `feedback/gmail_watcher.py`, `feedback/reply_classifier.py`, `feedback/score_updater.py`

### Gmail Push Notification Setup
```python
# feedback/gmail_watcher.py
gmail.users().watch(
    userId='me',
    body={
        'topicName': 'projects/YOUR_PROJECT/topics/gmail-replies',
        'labelIds': ['INBOX']
    }
)
# Re-register every 7 days (Gmail watch expires)
```

### On Notification Received
```python
# feedback/reply_classifier.py
POSITIVE_SIGNALS = ["interested", "let's connect", "can you send",
                    "interview", "would love", "tell me more"]
NEGATIVE_SIGNALS = ["not hiring", "no openings", "unsubscribe",
                    "not interested", "remove me"]

def classify(email_body):
    body_lower = email_body.lower()
    if any(s in body_lower for s in POSITIVE_SIGNALS):
        return 'positive'
    if any(s in body_lower for s in NEGATIVE_SIGNALS):
        return 'negative'
    return 'neutral'  # auto-reply, OOO, etc.
```

### Update Lead + Feed Back into Scoring
```python
# feedback/score_updater.py
def update_on_reply(domain, reply_type):
    domain_record = db.get_domain(domain)
    history = domain_record.reply_history or {'positive': 0, 'negative': 0, 'neutral': 0}
    history[reply_type] += 1
    db.update_domain(domain, reply_history=history)
    
    # Cancel follow-up if positive reply
    if reply_type == 'positive':
        db.query("""
            UPDATE followup_queue SET sent = TRUE
            WHERE lead_id = ? AND sent = FALSE
        """, lead_id)
```

Next time a similar company/role is scored, `historical_success_score` reflects real data.

---

## 🔹 PHASE 14 — RETRY QUEUE PROCESSOR

**File:** `core/guards.py` (retry section)

Runs at the start of every scheduler cycle, before discovery.

```python
def process_retry_queue():
    pending = db.query("""
        SELECT * FROM retry_queue
        WHERE resolved = FALSE
        AND attempts < max_attempts
        AND next_retry_at <= NOW()
    """)
    
    for job in pending:
        try:
            if job.phase == 'groq':
                groq_client.generate(job.payload)
            elif job.phase == 'twilio':
                twilio_sender.send(job.payload)
            elif job.phase == 'gmail':
                gmail_client.send(job.payload)
            elif job.phase == 'hunter':
                hunter_client.search(job.payload)
            
            job.resolved = True
            
        except Exception as e:
            job.attempts += 1
            job.last_error = str(e)
            job.next_retry_at = now + (2 ** job.attempts * 5 minutes)  # exponential backoff
            
            if job.attempts >= job.max_attempts:
                log_alert(f"Max retries hit for {job.phase}: {job.payload}")
```

Exponential backoff: retry at 5min → 10min → 20min → give up + alert.

---

## 🔹 PHASE 15 — ANALYTICS DASHBOARD

**Folder:** `dashboard/` (Next.js app)

### Discovery Panel
- Internships found today / this week
- Scrapling tier breakdown (T1 vs T2 vs T3 success rates)
- Pre-score kill rate
- Firecrawl calls used / remaining

### Email Panel
- Regex vs Hunter email source split
- Hunter calls today / credits remaining
- Validation failure breakdown (MX / format / SMTP)

### Outreach Panel
- Groq drafts generated
- Approval rate + auto-approvals
- Emails sent vs daily limit
- Warmup phase progress bar
- Pending follow-ups

### Performance Panel
- Reply rate + positive reply rate
- Full funnel: discovered → pre-scored → email found → validated → full-scored → drafted → approved → sent → replied
- Top performing company types
- Scoring weight tuner (reads/writes `scoring_config` table) ← NEW

### Retry Panel ← NEW
- Active retries by phase
- Max-retry failures (needs manual action)

---

## 🔁 COMPLETE FINAL FLOW

```
Scheduler (3x/day)
   ↓
Process retry_queue (exponential backoff)
   ↓
Process followup_queue (day 5 follow-ups)
   ↓
Process quarantine re-evaluations (14-day lookback)
   ↓
Load daily counters + enforce global limits
   ↓
┌──────────────────────────────────────────┐
│   3-TIER SCRAPING + PROXY ROTATION       │
│   Tier 1: Scrapling HTTP                 │
│   Tier 2: Scrapling Dynamic (Playwright) │
│   Tier 3: Firecrawl (dual-guarded)       │
└──────────────────────────────────────────┘
   ↓
Extract internship data
   ↓
Deduplication
   ↓
PRE-SCORE — Gate 1 (title + company, no API)
   → score < 40 → STOP (zero cost)
   ↓
Regex Email Extraction (free)
   ↓
   ├── score 40–59 + no email → STOP (skip Hunter to protect credits)
   └── score 60+ + no email  → Hunter Credit Shield
                                  → domain cache check
                                  → daily guard
                                  → Hunter API (once per new domain)
                                  → on failure → retry_queue
   ↓
EMAIL VALIDATION — Gate 2 (MX + format + SMTP)
   → invalid → STOP
   ↓
FULL SCORING — Gate 3 (resume + description + history)
   → score < 60 → STOP
   ↓
Groq Personalization (static system prompt for caching)
   → on failure → retry_queue
   → create followup_queue entry (day 5)
   ↓
Twilio Approval SMS (Twilio signature verified)
   → on failure → retry_queue
   → YES / NO / PREVIEW
   → 2hr timeout → auto-approve if score >= 90
   → NO → quarantine (14-day re-eval)
   ↓
Email Queue
   → warmup-aware daily limit
   → 45min+ spacing + jitter
   ↓
Gmail API Send (resume attached)
   → on failure → retry_queue
   ↓
Reply Detection (Gmail Push Notifications)
   → classify: positive / neutral / negative
   → update lead status
   → cancel follow-up if positive reply
   → update company reply_history
   → feed into historical_success_score
   ↓
Analytics Dashboard (real-time via Supabase)
```

---

## 💰 FINAL COST CONTROL SUMMARY

| Component   | Control Mechanism                                          |
|-------------|------------------------------------------------------------|
| Scrapling   | Unlimited — always try first                               |
| Firecrawl   | Daily cap + per-domain weekly cap                          |
| Hunter      | Domain cache + daily cap + score >= 60 required            |
| Groq        | All 3 gates must pass + system prompt caching              |
| Gmail       | Warmup schedule + strict daily limit + 45min spacing       |
| Twilio      | ~15 SMS/day max + signature verification                   |

**Accurate kill gate summary:**
- Gate 1 + Gate 2 protect Hunter (2 guards)
- Gate 1 + Gate 2 + Gate 3 protect Groq (3 guards)
- Nothing reaches Gmail without human or auto-approval

---

## ⚖️ ETHICAL + SAFETY DESIGN

- Respect robots.txt on all scraping tiers
- No LinkedIn private data scraping
- No login automation
- No bulk burst sending (warmup + spacing enforced)
- Twilio webhook signature verified (no spoofed approvals)
- Human approval before every send
- Quarantine over permanent discard
- Reply classification never auto-responds

---

*LazyIntern v2 — 3 kill gates, retry resilience, tunable scoring, follow-up automation, and a feedback loop that makes every cycle smarter than the last.*