# LazyIntern - Complete Work Plan

## 🎯 Project Goal
Build a fully functional automated internship outreach pipeline with:
- Email discovery & validation
- AI-powered personalization (Groq)
- WhatsApp approval workflow (Twilio)
- Automated sending (Gmail API)
- Feedback loop for continuous improvement

---

## 📋 PHASE 1: CRITICAL INTEGRATIONS

### 1.1 Groq API Integration ⚡ HIGH PRIORITY
**File:** `backend/pipeline/groq_client.py`

**Tasks:**
- [ ] Add Groq API key to `.env`
- [ ] Implement actual Groq API call in `generate_draft()`
- [ ] Use system prompt caching for cost optimization
- [ ] Parse JSON response: `{subject, body, followup}`
- [ ] Add error handling + retry queue integration
- [ ] Test with real resume.json + sample job description
- [ ] Track token usage in `daily_usage_stats.groq_tokens_used`

**Acceptance Criteria:**
- Generates personalized emails based on resume + JD
- Handles API failures gracefully with retry queue
- Costs < $0.01 per draft (with caching)

---

### 1.2 Email Validation - SMTP Ping ⚡ HIGH PRIORITY
**File:** `backend/pipeline/email_validator.py`

**Current Status:** Stub implementation, `enable_smtp_ping=false` by default

**Tasks:**
- [ ] Implement full SMTP handshake (EHLO → MAIL FROM → RCPT TO)
- [ ] Use `smtplib` for connection
- [ ] Extract MX host from DNS records
- [ ] Timeout: 10 seconds per check
- [ ] Only ping if confidence < 90% (to save time)
- [ ] Handle common SMTP response codes:
  - 250: Valid email
  - 550: Mailbox not found
  - 421/450: Temporary failure (retry)
  - 554: Blocked/spam
- [ ] Add rate limiting (max 10 pings/minute to avoid blacklisting)
- [ ] Log validation failures with reason codes
- [ ] Update `leads` table: `smtp_valid` column

**Acceptance Criteria:**
- Validates emails with 95%+ accuracy
- Doesn't get IP blacklisted
- Completes in < 15 seconds per email

---

### 1.3 Twilio WhatsApp Integration ⚡ HIGH PRIORITY
**Files:** 
- `backend/approval/twilio_sender.py`
- `backend/approval/webhook_handler.py`

**Current Status:** SMS-based, needs WhatsApp migration

**Tasks:**
- [ ] Update Twilio config to use WhatsApp sandbox/production number
- [ ] Change `twilio_from_number` format to `whatsapp:+14155238886`
- [ ] Change `approver_to_number` format to `whatsapp:+919811394884`
- [ ] Update SMS message format for WhatsApp:
  ```
  🎯 *LazyIntern - New Lead*
  
  Company: {company}
  Role: {role}
  Score: {score}%
  Email: {email}
  Source: {source}
  
  Reply:
  ✅ YES - Approve & send
  ❌ NO - Reject & quarantine
  👁️ PREVIEW - See full email
  
  DRAFT:{draft_id}
  ```
- [ ] Update webhook handler to parse WhatsApp responses
- [ ] Test with Twilio WhatsApp sandbox first
- [ ] Add rich media support (optional): send preview as formatted message
- [ ] Handle WhatsApp-specific status callbacks (delivered, read, failed)

**Acceptance Criteria:**
- Receives approval requests on WhatsApp
- YES/NO/PREVIEW responses work correctly
- Webhook signature validation passes
- Messages delivered within 5 seconds

---

### 1.4 Gmail API - Full Integration ⚡ HIGH PRIORITY
**File:** `backend/outreach/gmail_client.py`

**Current Status:** Basic OAuth2 setup, needs testing + attachment support

**Tasks:**
- [ ] Set up Google Cloud Project + enable Gmail API
- [ ] Download OAuth2 credentials → `secrets/gmail_oauth_client.json`
- [ ] Run first-time auth flow to generate `secrets/gmail_token.json`
- [ ] Test basic email sending
- [ ] Add resume.pdf attachment support:
  - Store resume at `data/resume.pdf`
  - Attach to all outreach emails
  - Use MIME multipart encoding
- [ ] Implement email threading (In-Reply-To header for follow-ups)
- [ ] Add email tracking (optional): read receipts, link tracking
- [ ] Handle Gmail API rate limits (250 emails/day for free tier)
- [ ] Add retry logic for 429 (rate limit) and 5xx errors
- [ ] Log sent emails to `pipeline_events`

**Acceptance Criteria:**
- Sends emails with resume attachment
- OAuth refresh works automatically
- Respects warmup schedule (5→15 emails/day)
- Follow-ups thread correctly

---

## 📋 PHASE 2: DASHBOARD BACKEND

### 2.1 Dashboard API Endpoint
**File:** `backend/api/routes/dashboard.py` (NEW)

**Tasks:**
- [ ] Create `/api/dashboard` GET endpoint
- [ ] Query all metrics from Supabase:
  - Discovery metrics (internships today/week, tier success rates, pre-score kills, Firecrawl usage)
  - Email metrics (regex vs Hunter split, Hunter calls, validation failures)
  - Outreach metrics (drafts generated, approval rate, auto-approvals, emails sent, warmup progress, pending follow-ups)
  - Performance metrics (reply rate, positive reply rate, funnel stages, top company types)
  - Retry metrics (active retries by phase, max-retry failures)
  - Scoring config (weights from DB)
- [ ] Calculate derived metrics:
  - Pre-score kill rate = (pre_score_kills / total_discovered) * 100
  - Approval rate = (approved + auto_approved) / total_drafts * 100
  - Warmup progress = (current_limit / 15) * 100
- [ ] Return JSON matching `DashboardData` type from frontend
- [ ] Add caching (5 minute TTL) to reduce DB load
- [ ] Add CORS headers for frontend access

**Acceptance Criteria:**
- Frontend connects to real backend API
- All metrics display correctly
- Response time < 500ms
- Updates every 5 minutes

---

### 2.2 Connect Frontend to Backend
**File:** `frontend/.env.local`

**Tasks:**
- [ ] Update `NEXT_PUBLIC_API_BASE_URL` to backend URL
- [ ] If backend runs on different port, set up CORS
- [ ] Remove mock API route (`frontend/app/api/dashboard/route.ts`)
- [ ] Test real-time data flow
- [ ] Add error handling for backend downtime
- [ ] Add loading states

---

## 📋 PHASE 3: GMAIL PUSH NOTIFICATIONS

### 3.1 Gmail Pub/Sub Setup
**File:** `backend/feedback/gmail_watcher.py`

**Current Status:** Polling-based, needs Pub/Sub

**Tasks:**
- [ ] Set up Google Cloud Pub/Sub topic
- [ ] Grant Gmail API publish permissions to topic
- [ ] Register Gmail watch with Pub/Sub topic
- [ ] Create Pub/Sub subscription
- [ ] Deploy webhook endpoint for Pub/Sub messages
- [ ] Parse notification payload → fetch actual email
- [ ] Extract reply body and classify (positive/negative/neutral)
- [ ] Update `company_domains.reply_history`
- [ ] Cancel follow-ups if positive reply
- [ ] Update draft status to `replied_positive` or `replied_negative`
- [ ] Re-register watch every 7 days (Gmail requirement)

**Acceptance Criteria:**
- Receives reply notifications within 30 seconds
- Classifies replies correctly (90%+ accuracy)
- Updates scoring feedback loop
- No polling needed

---

## 📋 PHASE 4: PRODUCTION DEPLOYMENT

### 4.1 Proxy Pool Setup
**File:** `backend/scraper/http_fetcher.py`

**Tasks:**
- [ ] Research proxy providers (Oxylabs, Brightdata, Smartproxy, or free rotating proxies)
- [ ] Add 5-10 proxy URLs to `PROXY_POOL`
- [ ] Test proxy rotation with real scraping
- [ ] Monitor for IP blocks
- [ ] Add proxy health checks
- [ ] Fallback to direct connection if all proxies fail

---

### 4.2 Scheduler Automation
**File:** `backend/scheduler/cron.py`

**Tasks:**
- [ ] Set up Windows Task Scheduler (or cloud cron)
- [ ] Schedule 3 runs per day: 08:00, 13:00, 18:00
- [ ] Command: `python -m scheduler.cycle_manager --once`
- [ ] Add logging to file for each run
- [ ] Set up email alerts for failures
- [ ] Monitor daily_usage_stats to ensure limits aren't hit

---

### 4.3 Environment & Secrets Management
**Files:** `backend/.env`, `frontend/.env.local`

**Tasks:**
- [ ] Create `.env` from `.env.example`
- [ ] Fill in all API keys:
  - Supabase URL + Service Role Key
  - Groq API Key
  - Hunter API Key
  - Firecrawl API Key
  - Twilio Account SID + Auth Token + Phone Numbers
  - Gmail OAuth credentials path
- [ ] Set `PUBLIC_BASE_URL` for Twilio webhooks (use ngrok for testing)
- [ ] Never commit `.env` to git
- [ ] Use environment variables in production (Railway, Render, etc.)

---

### 4.4 Database Setup
**File:** `backend/db/schema.sql`

**Tasks:**
- [ ] Create Supabase project
- [ ] Run schema.sql in Supabase SQL editor
- [ ] Verify all 10 tables created
- [ ] Seed `scoring_config` table with default weights
- [ ] Set up Row Level Security (RLS) policies if needed
- [ ] Create database backups schedule

---

## 📋 PHASE 5: TESTING & OPTIMIZATION

### 5.1 End-to-End Testing
**Tasks:**
- [ ] Test full pipeline with 1 internship:
  - Discovery → Dedup → Pre-score → Email extraction → Validation → Full score → Groq draft → WhatsApp approval → Gmail send
- [ ] Test retry queue for each phase
- [ ] Test follow-up sending after 5 days
- [ ] Test reply detection and feedback loop
- [ ] Test quarantine re-evaluation after 14 days
- [ ] Test auto-approver for 90+ scores
- [ ] Verify all daily limits enforced

---

### 5.2 Cost Optimization
**Tasks:**
- [ ] Monitor Groq token usage (target: < $5/month)
- [ ] Monitor Hunter API calls (target: < 15/day)
- [ ] Monitor Firecrawl usage (target: < 10/day)
- [ ] Optimize pre-score thresholds to reduce API waste
- [ ] Review scoring weights based on reply data
- [ ] Tune email validation to skip obvious invalids

---

### 5.3 Performance Monitoring
**Tasks:**
- [ ] Add execution time logging for each phase
- [ ] Track scraping success rates per source
- [ ] Monitor email deliverability (bounces, spam reports)
- [ ] Track reply rates by company type
- [ ] Set up alerts for:
  - Daily limit reached
  - API failures > 5 in 1 hour
  - Zero emails sent for 2 days
  - Validation failure rate > 50%

---

## 📋 PHASE 6: ADVANCED FEATURES

### 6.1 Account Warmup Tracking
**File:** `backend/scheduler/warmup.py`

**Tasks:**
- [ ] Add `account_created_date` to config or DB
- [ ] Calculate warmup progress dynamically
- [ ] Update `daily_usage_stats.daily_limit` based on account age
- [ ] Display warmup progress in dashboard

---

### 6.2 Scoring Weight Tuner (Dashboard)
**File:** `frontend/app/scoring/page.tsx` (NEW)

**Tasks:**
- [ ] Create admin page to edit scoring weights
- [ ] Add backend endpoint: `POST /api/scoring/weights`
- [ ] Update `scoring_config` table
- [ ] Show impact preview before saving
- [ ] Require authentication (optional)

---

### 6.3 Manual Lead Entry
**File:** `frontend/app/leads/page.tsx` (NEW)

**Tasks:**
- [ ] Form to manually add internship + email
- [ ] Skip discovery/extraction phases
- [ ] Jump directly to validation → scoring → draft
- [ ] Useful for referrals or direct applications

---

### 6.4 Email Template Customization
**File:** `backend/pipeline/groq_client.py`

**Tasks:**
- [ ] Allow multiple email templates
- [ ] A/B test different styles
- [ ] Track which templates get better reply rates
- [ ] Auto-select best-performing template

---

## 📋 PHASE 7: POLISH & LAUNCH

### 7.1 Documentation
**Tasks:**
- [ ] Update README with setup instructions
- [ ] Document all environment variables
- [ ] Create troubleshooting guide
- [ ] Add architecture diagram
- [ ] Write API documentation

---

### 7.2 Security Audit
**Tasks:**
- [ ] Review all API key storage
- [ ] Verify Twilio signature validation
- [ ] Check for SQL injection vulnerabilities
- [ ] Ensure no PII in logs
- [ ] Add rate limiting to API endpoints

---

### 7.3 Launch Checklist
**Tasks:**
- [ ] All API keys configured
- [ ] Database schema deployed
- [ ] Scheduler running 3x/day
- [ ] Dashboard accessible
- [ ] WhatsApp approval working
- [ ] Gmail sending working
- [ ] Reply detection working
- [ ] Monitor for 1 week before scaling

---

## 🎯 SUCCESS METRICS

After 1 month of operation:
- [ ] 500+ internships discovered
- [ ] 200+ emails validated
- [ ] 100+ emails sent
- [ ] 10+ positive replies (10% reply rate)
- [ ] 2+ interview invitations
- [ ] < $20 total API costs

---

## 🚨 CRITICAL PATH (Priority Order)

1. **Groq API Integration**
2. **SMTP Email Validation**
3. **Twilio WhatsApp Setup**
4. **Gmail API Testing**
5. **Dashboard Backend API**
6. **End-to-End Test**
7. **Deploy & Monitor**

---

## 📝 NOTES

- Start with Twilio WhatsApp sandbox for testing (free)
- Use ngrok for local webhook testing
- Keep daily limits low initially (5 emails/day) during warmup
- Monitor Gmail sender reputation closely
- Back up database weekly
- Review reply data weekly to tune scoring

---

**Next Step:** Start with Phase 1.1 (Groq API Integration) - it's the quickest win and unblocks draft generation!
