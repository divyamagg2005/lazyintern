# 🧠 FINAL PRODUCTION PIPELINE — INTERNSHIP OUTREACH SYSTEM
### Groq · Scrapling · Firecrawl · Hunter · Supabase · Twilio · Gmail API

---

## SYSTEM OBJECTIVE

> Discover internships → Deduplicate → Pre-score cheap → Extract + validate emails → Full score → Personalize with Groq → Human approval → Send 15/day → Detect replies → Feed back into scoring.

---

## ⚙️ GLOBAL SYSTEM GUARDS

```python
MAX_EMAILS_PER_DAY        = 15
HUNTER_DAILY_LIMIT        = 15
FIRECRAWL_DAILY_LIMIT     = 10
FIRECRAWL_PER_DOMAIN_WEEK = 2       # NEW — prevents one bad source burning quota
SCRAPE_BATCH_LIMIT        = 50
MIN_EMAIL_INTERVAL_MIN    = 45
AUTO_APPROVE_THRESHOLD    = 90      # NEW — score above this auto-approves after 2hr
TWILIO_TIMEOUT_HOURS      = 2       # NEW — auto-approve timeout
EMAIL_WARMUP_PHASE        = True    # NEW — ramp from 5/day to 15/day over 2 weeks
```

All counters are DB-backed in `daily_usage_stats`. Nothing runs from in-memory state.

---

## 🔹 PHASE 0 — SCHEDULER

**Runs:** 3x per day (e.g. 08:00, 13:00, 18:00)  
**Processes:** Max `SCRAPE_BATCH_LIMIT` URLs per cycle  
**Enforces:** All daily counters before any work begins

```
On each cycle start:
  1. Load daily_usage_stats for today
  2. If emails_sent >= MAX_EMAILS_PER_DAY → skip outreach, run discovery only
  3. If all limits hit → exit early, log skip reason
  4. Else → begin discovery cycle
```

---

## 🔹 PHASE 1 — 3-TIER SCRAPING ENGINE

### Tier 1 — Scrapling HTTP Fetch
- Concurrency: 5–8 workers
- Delay: 2–3 sec between requests + random jitter
- Respect robots.txt strictly
- Extract raw HTML DOM

**If DOM is populated → proceed to extraction**

---

### Tier 2 — Scrapling DynamicFetcher (Playwright)
Triggered when:
- DOM is empty
- Content is JS-rendered
- Light bot protection detected

**If successful → proceed to extraction**

---

### Tier 3 — Firecrawl Fallback
Triggered only when:
- Both Scrapling tiers failed
- `firecrawl_calls_today < FIRECRAWL_DAILY_LIMIT`
- `firecrawl_calls_this_week_for_domain < FIRECRAWL_PER_DOMAIN_WEEK`  ← NEW guard

If either Firecrawl limit is hit → **skip page entirely, log as `scrape_failed`**

**Per-domain weekly cap prevents one broken source from consuming your entire daily quota.**

---

### Internship Data Extraction
From successful scrape, extract:
- Company name
- Role title
- Job link (canonical URL)
- Full description text
- Location
- Posted date
- Source URL

**Store in `internships` table → status = `discovered`**

---

## 🔹 PHASE 2 — DEDUPLICATION

Before any further work:

```python
Skip if ANY of:
  - Same company + role already in DB
  - status in (processed, emailed, rejected, quarantined)
  - Same job link already seen
```

This protects every downstream phase from wasted work.

---

## 🔹 PHASE 3 — PRE-SCORING (CHEAP GATE) ← MOVED UP

**This is the most important architectural change.**  
Runs immediately after deduplication, before email extraction, before Hunter, before Groq.

Uses only:
- Role title
- Company name
- Location

**No LLM. No API calls. Pure keyword matching.**

```python
score = 0
if any keyword in ["AI", "ML", "data", "NLP", "research"] in role_title:
    score += 40
if company_type == "startup" or "YC" in company_tags:
    score += 20
if location matches preference:
    score += 20
if company in past_success_list:
    score += 20
```

**If pre_score < 40 → mark `low_priority` → STOP**  
No email extraction. No Hunter. No Groq. Killed at zero cost.

**If pre_score >= 40 → proceed to email extraction**

---

## 🔹 PHASE 4 — FREE EMAIL EXTRACTION (REGEX)

Attempt to find recruiter email directly from scraped page content.

Steps:
1. Run regex over raw HTML + visible text
2. Normalize obfuscated patterns (`[at]`, `(dot)`, etc.)
3. Filter by recruiter keywords: `hr`, `hiring`, `talent`, `recruiter`, `careers`
4. Match email domain against company domain

**If valid email found:**
- Store in `leads` table, source = `regex`
- Skip Hunter entirely
- Proceed to email validation (Phase 5)

**If no email found:**
- Proceed to Hunter flow (Phase 6)

---

## 🔹 PHASE 5 — EMAIL VALIDATION ← NEW

**Runs for ALL emails — both regex-found and Hunter-found.**  
Protecting Gmail sender reputation is non-negotiable.

**Step 1 — MX Record Check**
```python
import dns.resolver
records = dns.resolver.resolve(domain, 'MX')
# If no MX records → email domain is dead → discard
```

**Step 2 — Format Validation**
- RFC-compliant format check
- Disposable domain blocklist check (using `disposable-email-domains` list)

**Step 3 — SMTP Ping (optional, for low-confidence emails)**
- EHLO handshake only — no actual send
- Confirms mailbox exists at server level

**If validation fails:**
- Mark lead as `invalid_email`
- Do not proceed to scoring or Groq
- Log reason

**If validation passes → proceed to full scoring**

---

## 🔹 PHASE 6 — HUNTER CREDIT SHIELD

Only reached if regex extraction found nothing.

### Step 1 — Extract Company Domain
```
jobs.startup.ai → startup.ai
```

### Step 2 — Domain Cache Check
Query `company_domains` table.  
If domain exists and `hunter_called = true`:
- Reuse stored emails
- Skip Hunter entirely

### Step 3 — Hunter Daily Guard
```python
if hunter_calls_today >= HUNTER_DAILY_LIMIT:
    mark internship as `hunter_limit_reached`
    stop
```

### Step 4 — Hunter Domain Search
Call Hunter once per new domain.  
Filter results:
- Roles: `hr@`, `hiring@`, `recruiter@`, `talent@`
- Confidence threshold: > 80%

Store in `company_domains`:
- emails (JSON array)
- confidence scores
- hunter_called = true
- last_checked timestamp

### Step 5 — Optional Verification
Only verify if confidence < 90% AND `hunter_calls_today` has budget remaining.  
(Verification costs a separate Hunter credit.)

**After Hunter → run email through Phase 5 validation before proceeding.**

---

## 🔹 PHASE 7 — FULL SCORING ENGINE

Now we have a validated email. Run the complete score.

Inputs:
- Role title + description (full text)
- Company name, type, size
- Location
- Resume keyword overlap (pre-parsed resume stored in config)
- Tech stack match
- Historical reply rate for similar company types ← NEW feedback signal

```python
full_score = (
    relevance_score * 0.35 +
    resume_overlap_score * 0.25 +
    tech_stack_score * 0.20 +
    location_score * 0.10 +
    historical_success_score * 0.10  # from reply feedback loop
)
```

**If full_score < 60 → mark `low_priority`, stop**  
**If full_score >= 60 → proceed to Groq**

---

## 🔹 PHASE 8 — GROQ PERSONALIZATION ENGINE

Only qualified, validated, scored leads reach here.

### Prompt Structure (Optimized for Caching)

**System Prompt (static — always identical string for cache hits):**
```
You are an expert cold email writer for internship outreach.
[Resume structured data]
[Tone: professional, concise, genuine]
[Format: subject line + 3-paragraph email + optional follow-up]
```

**User Prompt (dynamic per lead):**
```
Company: {company}
Role: {role}
Description: {description_summary}
Recruiter: {recruiter_name or "Hiring Team"}
Score: {full_score}
```

Groq generates:
- Subject line (A/B variant optional)
- Cold email body (150–200 words max)
- Follow-up template (scheduled for day 5 if no reply)

**Store in `email_drafts` → status = `generated`**

---

## 🔹 PHASE 9 — TWILIO HUMAN APPROVAL (WITH AUTO-APPROVE)

System sends SMS:

```
[INTERNSHIP ALERT]
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

### Webhook Response Handling:
- `YES` → status = `approved` → enters email queue
- `NO` → status = `rejected` → moved to quarantine queue ← NEW
- `PREVIEW` → system replies with full email text, awaits YES/NO

### Auto-Approve Rule ← NEW
```python
if no_response_after(hours=2):
    if full_score >= AUTO_APPROVE_THRESHOLD:  # 90+
        status = 'auto_approved'
        enter email queue
    else:
        status = 'approval_timeout'
        defer to next cycle
```

This prevents idle queues from blocking your 15/day limit.

---

## 🔹 PHASE 10 — QUARANTINE QUEUE ← NEW

All `NO` rejections go here, not into permanent discard.

```sql
CREATE TABLE quarantine (
  id UUID PRIMARY KEY,
  lead_id UUID REFERENCES leads(id),
  rejected_at TIMESTAMP,
  reason TEXT,
  re_evaluate_after DATE,  -- rejected_at + 14 days
  re_evaluated BOOLEAN DEFAULT FALSE
);
```

Every cycle, the scheduler checks:
```python
SELECT * FROM quarantine
WHERE re_evaluate_after <= TODAY
AND re_evaluated = FALSE
```

Re-runs scoring with updated weights. If score now >= 75 → re-enter pipeline at Phase 8.

Handles the case where your resume or target criteria evolve over time.

---

## 🔹 PHASE 11 — EMAIL QUEUE (STRICT 15/DAY WITH WARMUP)

### Warmup Schedule ← NEW
```
Days 1–3:   Max 5 emails/day
Days 4–7:   Max 8 emails/day
Days 8–11:  Max 12 emails/day
Days 12+:   Max 15 emails/day
```

Prevents Gmail from flagging a new sending account.

### Sending Rules
```python
if emails_sent_today >= daily_limit:
    stop all sending

# Space emails out
min_gap = 45 minutes + random(0, 10) minutes
```

### Gmail API Send
For each approved email:
1. Compose with subject + body
2. Attach resume PDF
3. Send via Gmail API (OAuth2)
4. Update status = `sent`, log `sent_at`
5. Increment `daily_usage_stats.emails_sent`

---

## 🔹 PHASE 12 — REPLY DETECTION LOOP ← NEW

Uses Gmail Push Notifications (not polling — zero cost, real-time).

### Setup
```python
# Register Gmail watch
gmail.users().watch(
    userId='me',
    body={'topicName': 'projects/YOUR_PROJECT/topics/gmail-replies'}
)
```

### On notification received:
1. Fetch new message thread
2. Match sender domain to `leads` table
3. Classify reply:
   - **Positive:** "interested", "let's connect", "can you send", "interview"
   - **Neutral:** auto-reply, out-of-office
   - **Negative:** "not hiring", "unsubscribe"

### Update lead status:
```
no_reply → replied_positive
no_reply → replied_neutral  
no_reply → replied_negative
```

### Feed back into scoring:
```python
# Update historical success weights
company_domain.reply_type = 'positive'
# Next time similar company/role scored → +10 historical_success_score
```

**This is what makes the system smarter over every cycle.**

---

## 🔹 PHASE 13 — ANALYTICS DASHBOARD

Next.js frontend connected to Supabase.

### Discovery Panel
- Internships discovered today / this week
- Scrapling success rate (Tier 1 vs Tier 2 vs Tier 3)
- Firecrawl calls used / remaining
- Pre-score kill rate (% stopped at Phase 3)

### Email Panel
- Emails found via regex vs Hunter
- Hunter calls today / remaining credits
- Email validation failure rate + reasons

### Outreach Panel
- Groq drafts generated today
- Approval rate (YES vs NO vs timeout)
- Auto-approvals triggered
- Emails sent today vs daily limit
- Warmup phase status

### Performance Panel
- Reply rate (total replies / sent)
- Positive reply rate
- Conversion funnel: discovered → scored → emailed → replied → interview
- Top performing company types
- Top performing role titles
- Historical score accuracy (predicted vs actual reply)

---

## 🗃️ FINAL DATABASE SCHEMA

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
  -- statuses: discovered, low_priority, processing, emailed, 
  --           replied_positive, replied_neutral, replied_negative
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validated leads with emails
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  recruiter_name TEXT,
  email TEXT NOT NULL,
  source TEXT,          -- regex | hunter | manual
  confidence INTEGER,
  verified BOOLEAN DEFAULT FALSE,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Domain-level Hunter cache
CREATE TABLE company_domains (
  domain TEXT PRIMARY KEY,
  emails JSONB,         -- [{email, confidence, role}]
  hunter_called BOOLEAN DEFAULT FALSE,
  last_checked TIMESTAMPTZ,
  reply_history JSONB,  -- {positive: N, negative: N, neutral: N}
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
  -- statuses: generated, approved, auto_approved, rejected, 
  --           sent, replied, quarantined
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
  daily_limit INTEGER DEFAULT 5,   -- increases with warmup
  hunter_calls INTEGER DEFAULT 0,
  firecrawl_calls INTEGER DEFAULT 0,
  groq_calls INTEGER DEFAULT 0,
  groq_tokens_used INTEGER DEFAULT 0,
  pre_score_kills INTEGER DEFAULT 0,   -- leads killed at Phase 3
  validation_fails INTEGER DEFAULT 0,  -- leads killed at Phase 5
  auto_approvals INTEGER DEFAULT 0
);

-- Full pipeline event log for funnel analysis
CREATE TABLE pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  event TEXT NOT NULL,
  -- events: discovered, deduplicated, pre_scored, email_found_regex,
  --         email_found_hunter, email_invalid, full_scored, draft_generated,
  --         approval_sent, approved, rejected, sent, replied_positive, etc.
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔁 COMPLETE FINAL FLOW

```
Scheduler (3x/day)
   ↓
Load daily counters + enforce global limits
   ↓
┌─────────────────────────────────┐
│   3-TIER SCRAPING               │
│   Tier 1: Scrapling HTTP        │
│   Tier 2: Scrapling Dynamic     │
│   Tier 3: Firecrawl (guarded)   │
└─────────────────────────────────┘
   ↓
Extract internship data
   ↓
Deduplication (DB check)
   ↓
PRE-SCORE (title + company only — no API) ← gate 1
   → low_priority → STOP
   ↓
Regex Email Extraction (free)
   ↓
MX + Format + SMTP Validation ← gate 2
   → invalid → STOP
   ↓
[If no email] Hunter Credit Shield
   → domain cache check
   → daily guard
   → Hunter API call (once per new domain)
   → validate result through gate 2
   ↓
Full Scoring Engine (resume + description + history) ← gate 3
   → score < 60 → STOP
   ↓
Groq Personalization (cached system prompt)
   → generate subject + body + followup
   ↓
Twilio Approval SMS
   → YES / NO / PREVIEW
   → 2hr timeout → auto-approve if score >= 90
   → NO → quarantine queue
   ↓
Email Queue
   → warmup-aware daily limit check
   → 45min+ spacing with jitter
   ↓
Gmail API Send (with resume attachment)
   ↓
Reply Detection (Gmail Push Notifications)
   → classify reply type
   → update lead status
   → feed signal back into scoring weights
   ↓
Analytics Dashboard
   ↓
Quarantine Re-evaluation (every cycle, 14-day lookback)
```

---

## 💰 COST CONTROL SUMMARY

| Component   | Control Mechanism                                      |
|-------------|--------------------------------------------------------|
| Scrapling   | Unlimited — always try first                           |
| Firecrawl   | Daily cap + per-domain weekly cap                      |
| Hunter      | Domain cache + daily cap + skip if regex finds email   |
| Groq        | Only for scored+validated leads + system prompt cache  |
| Gmail       | Warmup schedule + strict 15/day hard limit             |
| Twilio      | Low volume, approval only — ~15 SMS/day max            |

---

## ⚖️ ETHICAL + SAFETY DESIGN

- Respect robots.txt on all scraping tiers
- No LinkedIn private data scraping
- No login automation on any platform
- No bulk burst sending (warmup + spacing enforced)
- Human approval before every send (with transparent auto-approve rule)
- Quarantine instead of permanent discard — respects your evolving criteria
- Reply classification never auto-responds — human handles positive replies

---

*This system has 3 kill gates before any money is spent, a feedback loop that improves with every cycle, and full observability via pipeline_events. It is designed to run indefinitely without manual babysitting while keeping you in control of every send.*
