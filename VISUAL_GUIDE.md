# 📊 LazyIntern - Visual Architecture Guide

A visual representation of how everything connects.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (You)                              │
│  - Configures .env                                              │
│  - Monitors dashboard                                           │
│  - Approves emails via WhatsApp                                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND DASHBOARD                           │
│                    (Next.js - Port 3000)                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │Discovery │  Email   │ Outreach │Performance│ Retries  │      │
│  │  Panel   │  Panel   │  Panel   │  Panel    │  Panel   │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
└────────────┬────────────────────────────────────────────────────┘
             │ HTTP GET /dashboard
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API                                  │
│                  (FastAPI - Port 8000)                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  /healthz        - Health check                      │      │
│  │  /dashboard      - Metrics endpoint                  │      │
│  │  /twilio/webhook - WhatsApp approval handler         │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SCHEDULER                                    │
│              (Runs 3x daily: 8am, 1pm, 6pm)                     │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  1. Process retry queue                              │      │
│  │  2. Process follow-ups                               │      │
│  │  3. Re-evaluate quarantine                           │      │
│  │  4. Run discovery cycle                              │      │
│  │  5. Process email queue                              │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE (15 Phases)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Flow (Detailed)

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1-2: DISCOVERY & DEDUPLICATION                           │
│                                                                 │
│  Job Sources (job_source.json)                                 │
│       │                                                         │
│       ├─► Tier 1: HTTP Fetch (Scrapling)                       │
│       │        │                                                │
│       │        ├─ Success? ──► Extract internships             │
│       │        │                                                │
│       │        └─ Failed? ──► Tier 2: Dynamic (Playwright)     │
│       │                 │                                       │
│       │                 ├─ Success? ──► Extract internships    │
│       │                 │                                       │
│       │                 └─ Failed? ──► Tier 3: Firecrawl       │
│       │                          │                              │
│       │                          └─ Success? ──► Extract        │
│       │                                                         │
│       └─► Deduplication (by link, company+role)                │
│                │                                                │
│                └─► Store in DB (status: discovered)            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: PRE-SCORING (Gate 1) 💰                               │
│                                                                 │
│  Keyword matching (role, company, location)                    │
│       │                                                         │
│       ├─► Score < 40? ──► KILLED (pre_score_kills++)           │
│       │                                                         │
│       ├─► Score 40-59? ──► Try regex extraction only           │
│       │                                                         │
│       └─► Score ≥ 60? ──► Eligible for Hunter API              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: EMAIL EXTRACTION (Free)                               │
│                                                                 │
│  Regex pattern matching on description                         │
│       │                                                         │
│       ├─► Found? ──► Store lead (source: regex) ──► Phase 5    │
│       │                                                         │
│       └─► Not found? ──► Phase 6 (Hunter)                      │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: HUNTER CREDIT SHIELD                                  │
│                                                                 │
│  Check pre_score ≥ 60?                                         │
│       │                                                         │
│       ├─► No? ──► KILLED (no_email_low_score)                  │
│       │                                                         │
│       └─► Yes? ──► Check domain cache                          │
│                │                                                │
│                ├─► Cached? ──► Use cached email                │
│                │                                                │
│                └─► Not cached? ──► Check daily limit           │
│                         │                                       │
│                         ├─► Limit hit? ──► KILLED              │
│                         │                                       │
│                         └─► Call Hunter API                    │
│                                  │                              │
│                                  └─► Store lead (source: hunter)│
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: EMAIL VALIDATION (Gate 2) 🛡️                         │
│                                                                 │
│  1. RFC format check                                           │
│       │                                                         │
│       ├─► Invalid? ──► KILLED (format_invalid)                 │
│       │                                                         │
│       └─► Valid? ──► 2. Disposable domain check                │
│                │                                                │
│                ├─► Disposable? ──► KILLED (disposable_domain)  │
│                │                                                │
│                └─► OK? ──► 3. MX record check                  │
│                         │                                       │
│                         ├─► No MX? ──► KILLED (mx_failure)     │
│                         │                                       │
│                         └─► Has MX? ──► 4. SMTP ping?          │
│                                  │                              │
│                                  ├─► Confidence ≥ 90? ──► Skip │
│                                  │                              │
│                                  └─► Confidence < 90? ──► Ping │
│                                           │                     │
│                                           └─► Valid? ──► Phase 7│
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: FULL SCORING (Gate 3) 🎯                              │
│                                                                 │
│  Weighted scoring:                                             │
│    - Relevance (35%)                                           │
│    - Resume overlap (25%)                                      │
│    - Tech stack (20%)                                          │
│    - Location (10%)                                            │
│    - Historical success (10%)                                  │
│       │                                                         │
│       ├─► Score < 60? ──► KILLED (low_priority)                │
│       │                                                         │
│       └─► Score ≥ 60? ──► Phase 8                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 8: GROQ PERSONALIZATION 🤖                               │
│                                                                 │
│  Generate with Groq AI:                                        │
│    - Subject line                                              │
│    - Email body (150-200 words)                                │
│    - 5-day follow-up                                           │
│       │                                                         │
│       ├─► Success? ──► Store draft (status: generated)         │
│       │                      │                                  │
│       │                      └─► Create follow-up queue entry  │
│       │                                                         │
│       └─► Failed? ──► Retry queue                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 9: APPROVAL 📱                                           │
│                                                                 │
│  Twilio configured?                                            │
│       │                                                         │
│       ├─► Yes? ──► Send WhatsApp approval request              │
│       │        │                                                │
│       │        ├─► User replies "YES" ──► Approved             │
│       │        │                                                │
│       │        ├─► User replies "NO" ──► Quarantine            │
│       │        │                                                │
│       │        └─► No reply after 2h + score ≥ 90? ──► Auto   │
│       │                                                         │
│       └─► No? ──► Auto-approve if score ≥ 90                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 11: EMAIL QUEUE & SENDING 📧                             │
│                                                                 │
│  Check daily limit                                             │
│       │                                                         │
│       ├─► Limit reached? ──► Wait for next day                 │
│       │                                                         │
│       └─► Under limit? ──► Check warmup schedule               │
│                │                                                │
│                ├─► Day 1-3: Max 5 emails/day                   │
│                ├─► Day 4-7: Max 8 emails/day                   │
│                ├─► Day 8-11: Max 12 emails/day                 │
│                └─► Day 12+: Max 15 emails/day                  │
│                         │                                       │
│                         └─► Send via Gmail (with resume.pdf)   │
│                                  │                              │
│                                  ├─► Success? ──► Mark sent    │
│                                  │                              │
│                                  └─► Failed? ──► Retry queue   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 12: FOLLOW-UPS (Day 5)                                   │
│                                                                 │
│  Check follow-up queue                                         │
│       │                                                         │
│       └─► Send after 5 days? ──► Check if replied              │
│                │                                                │
│                ├─► Replied? ──► Skip follow-up                 │
│                │                                                │
│                └─► No reply? ──► Send follow-up                │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 13: REPLY DETECTION 💬                                   │
│                                                                 │
│  Gmail watcher (polling or Pub/Sub)                            │
│       │                                                         │
│       └─► New reply? ──► Classify sentiment                    │
│                │                                                │
│                ├─► Positive? ──► Update reply_history          │
│                │             └─► Cancel follow-up              │
│                │                                                │
│                ├─► Negative? ──► Update reply_history          │
│                │                                                │
│                └─► Neutral? ──► Update reply_history           │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
                   END
```

---

## 💾 Database Schema Relationships

```
┌──────────────┐
│ internships  │
│──────────────│
│ id (PK)      │◄─────────┐
│ company      │          │
│ role         │          │
│ link (UNIQUE)│          │
│ pre_score    │          │
│ full_score   │          │
│ status       │          │
└──────────────┘          │
                          │
                          │ internship_id (FK)
                          │
┌──────────────┐          │
│    leads     │          │
│──────────────│          │
│ id (PK)      │◄─────────┤
│ internship_id├──────────┘
│ email        │
│ source       │◄─────────┐
│ verified     │          │
│ mx_valid     │          │
│ smtp_valid   │          │
└──────┬───────┘          │
       │                  │
       │ lead_id (FK)     │
       │                  │
       ▼                  │
┌──────────────┐          │
│email_drafts  │          │
│──────────────│          │
│ id (PK)      │          │
│ lead_id      ├──────────┘
│ subject      │
│ body         │
│ followup_body│
│ status       │◄─────────┐
│ sent_at      │          │
└──────┬───────┘          │
       │                  │
       │ draft_id (FK)    │
       │                  │
       ├──────────────────┤
       │                  │
       ▼                  │
┌──────────────┐          │
│ quarantine   │          │
│──────────────│          │
│ id (PK)      │          │
│ lead_id      │          │
│ draft_id     ├──────────┘
│ re_evaluate  │
│ after        │
└──────────────┘

┌──────────────┐
│followup_queue│
│──────────────│
│ id (PK)      │
│ draft_id     │
│ lead_id      │
│ send_after   │
│ sent         │
└──────────────┘

┌──────────────┐
│retry_queue   │
│──────────────│
│ id (PK)      │
│ phase        │
│ payload      │
│ attempts     │
│ next_retry_at│
└──────────────┘

┌──────────────┐
│company_domains│
│──────────────│
│ domain (PK)  │
│ emails       │
│ hunter_called│
│ reply_history│
│ firecrawl_   │
│ calls_week   │
└──────────────┘

┌──────────────┐
│daily_usage_  │
│    stats     │
│──────────────│
│ date (PK)    │
│ emails_sent  │
│ daily_limit  │
│ hunter_calls │
│ groq_calls   │
│ pre_score_   │
│ kills        │
└──────────────┘

┌──────────────┐
│pipeline_     │
│  events      │
│──────────────│
│ id (PK)      │
│ internship_id│
│ event        │
│ metadata     │
│ created_at   │
└──────────────┘

┌──────────────┐
│scoring_config│
│──────────────│
│ key (PK)     │
│ weight       │
│ description  │
└──────────────┘
```

---

## 🔐 API Integrations

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Supabase   │     │     Groq     │     │    Gmail     │
│  (Database)  │     │  (AI Email)  │     │  (Sending)   │
│              │     │              │     │              │
│ PostgreSQL   │     │ Llama 3.1    │     │ OAuth2 API   │
│ REST API     │     │ 70B Model    │     │ SMTP Send    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ CRUD ops           │ Generate draft     │ Send email
       │                    │                    │
       └────────────────────┴────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Backend     │
                    │   (FastAPI)   │
                    └───────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Twilio     │     │   Hunter.io  │     │  Firecrawl   │
│  (WhatsApp)  │     │   (Email     │     │  (Scraping)  │
│              │     │  Discovery)  │     │              │
│ Approval SMS │     │ Domain Search│     │ JS Rendering │
│ Webhook      │     │ API          │     │ API          │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 📊 Data Flow Example

```
Example: Processing "AI Intern at OpenAI"

1. DISCOVERY
   ├─ Scrape internshala.com
   ├─ Extract: company="OpenAI", role="AI Intern"
   └─ Store in DB: status="discovered"

2. PRE-SCORE
   ├─ Keywords: "AI" (40 pts), "OpenAI" (20 pts)
   ├─ Score: 60
   └─ Pass Gate 1 ✅

3. EMAIL EXTRACTION
   ├─ Regex search in description
   ├─ Found: "careers@openai.com"
   └─ Store lead: source="regex"

4. VALIDATION
   ├─ Format: ✅ Valid
   ├─ Disposable: ✅ Not disposable
   ├─ MX: ✅ Has MX records
   ├─ SMTP: ✅ Mailbox exists
   └─ Pass Gate 2 ✅

5. FULL SCORE
   ├─ Relevance: 100 (AI intern matches)
   ├─ Resume overlap: 85 (Python, ML mentioned)
   ├─ Tech stack: 90 (PyTorch, TensorFlow)
   ├─ Location: 100 (Remote)
   ├─ Historical: 50 (no past data)
   ├─ Weighted: 87.5
   └─ Pass Gate 3 ✅

6. GROQ DRAFT
   ├─ Generate personalized email
   ├─ Subject: "AI Intern Application - ML Experience"
   ├─ Body: 180 words, mentions specific projects
   └─ Store draft: status="generated"

7. APPROVAL
   ├─ Score 87.5 ≥ 90? No
   ├─ Send WhatsApp: "OpenAI - AI Intern - 87%"
   ├─ User replies: "YES DRAFT:abc-123"
   └─ Update: status="approved"

8. SENDING
   ├─ Check daily limit: 3/5 ✅
   ├─ Attach resume.pdf
   ├─ Send via Gmail
   └─ Update: status="sent", sent_at=now

9. FOLLOW-UP (Day 5)
   ├─ Check if replied: No
   ├─ Send follow-up email
   └─ Mark: sent=true

10. REPLY (Day 7)
    ├─ Detect reply: "Thanks for applying..."
    ├─ Classify: Positive ✅
    ├─ Update company_domains.reply_history
    └─ Cancel any pending follow-ups
```

---

## 🎯 Cost Optimization Flow

```
100 Internships Discovered
        │
        ▼
┌───────────────────┐
│   Gate 1: Pre-    │
│   Score < 40      │
│   (Keyword only)  │
└────────┬──────────┘
         │
         ├─► 60 KILLED (60% filtered) 💰 $0 spent
         │
         └─► 40 Pass to Email Extraction
                  │
                  ▼
         ┌────────────────────┐
         │  Regex Extraction  │
         │  (Free)            │
         └────────┬───────────┘
                  │
                  ├─► 20 Found (50% success) 💰 $0 spent
                  │
                  └─► 20 Need Hunter
                           │
                           ▼
                  ┌────────────────────┐
                  │  Gate 1.5: Score   │
                  │  < 60 for Hunter   │
                  └────────┬───────────┘
                           │
                           ├─► 10 KILLED (50% filtered) 💰 $0 spent
                           │
                           └─► 10 Call Hunter 💰 $0.10 spent
                                    │
                                    ▼
                           ┌────────────────────┐
                           │  Gate 2: Email     │
                           │  Validation        │
                           └────────┬───────────┘
                                    │
                                    ├─► 5 Invalid (50% filtered) 💰 $0 spent
                                    │
                                    └─► 25 Valid (20 regex + 5 hunter)
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  Gate 3: Full      │
                                    │  Score < 60        │
                                    └────────┬───────────┘
                                             │
                                             ├─► 10 KILLED (40% filtered) 💰 $0 spent
                                             │
                                             └─► 15 Pass to Groq 💰 $0.15 spent
                                                      │
                                                      ▼
                                             ┌────────────────────┐
                                             │  Human Approval    │
                                             └────────┬───────────┘
                                                      │
                                                      ├─► 5 Rejected (33% filtered)
                                                      │
                                                      └─► 10 Approved
                                                               │
                                                               ▼
                                                      ┌────────────────────┐
                                                      │  Gmail Send        │
                                                      └────────────────────┘

TOTAL COST: $0.25 for 100 internships
EMAILS SENT: 10
COST PER EMAIL: $0.025
```

---

## 🔄 Retry Queue Flow

```
API Call Failed
     │
     ▼
┌─────────────────────────────────────────┐
│  Insert into retry_queue                │
│  - phase: "groq" / "twilio" / "gmail"   │
│  - payload: {original_data}             │
│  - attempts: 0                          │
│  - next_retry_at: now + 5 min           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Retry Processor (runs every cycle)    │
└────────────┬────────────────────────────┘
             │
             ├─► Attempt 1 (5 min later)
             │        │
             │        ├─► Success? ──► Mark resolved ✅
             │        │
             │        └─► Failed? ──► Attempt 2 (10 min later)
             │                 │
             │                 ├─► Success? ──► Mark resolved ✅
             │                 │
             │                 └─► Failed? ──► Attempt 3 (20 min later)
             │                          │
             │                          ├─► Success? ──► Mark resolved ✅
             │                          │
             │                          └─► Failed? ──► Alert admin ⚠️
             │
             └─► Max attempts reached ──► Manual intervention needed
```

---

This visual guide should help you understand how all the pieces fit together! 🎨
