# LazyIntern Pipeline - Current Status

**Last Updated**: March 1, 2026  
**Status**: ✅ All fixes implemented and verified

---

## ✅ Completed Tasks

### 1. Platform Email Rejection (Regex Phase)
- **File**: `backend/pipeline/email_extractor.py`
- **Status**: ✅ Working
- **Details**: Regex extractor now rejects platform emails (e.g., ecombes@linkedin.com from LinkedIn pages). Added `_is_platform_email()` function that checks if email domain matches job board domain.

### 2. Hunter API Company Domain Extraction
- **File**: `backend/pipeline/hunter_client.py`
- **Status**: ✅ Working
- **Details**: Hunter now searches company domains extracted from company NAME instead of job board URL. Added `find_company_domain()` function that converts company names to domains (e.g., "Blitzenx" → "blitzenx.com").

### 3. Hunter Blocking for Job Board Domains
- **File**: `backend/scheduler/cycle_manager.py`
- **Status**: ✅ Working
- **Details**: Added `JOB_BOARD_DOMAINS` blocklist. Hunter API blocked if company domain matches any job board domain. Internship marked as 'no_email' when blocked.

### 4. Duplicate Lead Prevention
- **File**: `backend/core/supabase_db.py`
- **Status**: ✅ Working
- **Details**: `insert_lead()` now checks if lead already exists for internship_id before inserting. Returns None if duplicate found. Ensures one lead per internship.

### 5. India Region Filtering
- **Files**: `backend/data/job_source.json`, `backend/pipeline/pre_scorer.py`
- **Status**: ✅ Working
- **Details**: 
  - Updated job_source.json: Added `&location=India` to all LinkedIn and Wellfound URLs
  - Added region filter in pre_scorer.py that disqualifies non-India locations (USA, UK, Singapore, Canada, Australia, UAE, Europe, Germany, London, New York, San Francisco)
  - Exception: non-India locations that also mention "India" or "remote" are kept

### 6. Job Sources Cleanup
- **File**: `backend/data/job_source.json`
- **Status**: ✅ Working
- **Details**:
  - REMOVED 10 sources: Builtin, Greenhouse, Lever, Ashby, Handshake, Jobspresso, Otta, Pallet, Paraform, Contra
  - Changed 17 sources to monthly/low priority: 14 AI labs + 3 global job boards
  - KEPT 26 India-relevant sources
  - Updated total_sources: 60 → 43
  - Updated monthly_sources_limit: 5 → 15

### 7. Groq Drafting and Backfill
- **Files**: `backend/scheduler/cycle_manager.py`, `backend/backfill_drafts.py`
- **Status**: ✅ Working
- **Details**:
  - Groq draft generation connected in cycle_manager after full scoring (score >= 60)
  - Backfill script created to generate drafts for existing leads
  - 3 second delay between SMS to avoid rate limiting
  - Smart execution check (only runs if leads.count > email_drafts.count)

### 8. Email Validation Failure Handling
- **File**: `backend/scheduler/cycle_manager.py`
- **Status**: ✅ Working
- **Details**: Internships marked as 'email_invalid' after validation fails to prevent infinite re-processing loops.

---

## 🔧 Pipeline Flow (Current)

1. **Discovery** → Scrape job boards (43 sources, India-focused)
2. **Region Filter** → Disqualify non-India locations BEFORE scoring
3. **Pre-Score** → Cheap local scoring (title + company + location)
   - Score < 40: Mark as 'low_priority', skip
   - Score >= 40: Continue to regex extraction
4. **Regex Extraction** → Extract emails from description
   - Platform emails rejected (linkedin.com, internshala.com, etc.)
   - If found: Create lead, continue to validation
   - If not found AND score >= 60: Try Hunter
5. **Hunter API** → Search company domain for emails
   - Company domain extracted from company NAME (not job board URL)
   - Job board domains blocked (never call Hunter for linkedin.com, etc.)
   - If found: Create lead, continue to validation
6. **Duplicate Check** → Before inserting lead, check if internship_id already has a lead
   - If duplicate: Skip insert, log 'lead_duplicate_skipped'
7. **Email Validation** → MX + SMTP validation
   - If invalid: Mark internship as 'email_invalid', stop
   - If valid: Continue to full scoring
8. **Full Scoring** → Detailed scoring with resume overlap
   - Score < 60: Mark as 'low_priority', stop
   - Score >= 60: Continue to Groq drafting
9. **Groq Drafting** → Generate personalized email draft
10. **Twilio SMS** → Send approval request to user
11. **Human Approval** → Wait for YES/NO response or auto-approve after 2h if score >= 90
12. **Email Queue** → Send approved emails via Gmail API

---

## 📊 Key Metrics

- **Job Sources**: 43 (26 daily, 17 monthly)
- **Pre-Score Threshold (Regex)**: 40
- **Pre-Score Threshold (Hunter)**: 60
- **Full Score Threshold (Groq)**: 60
- **Auto-Approval Threshold**: 90 (after 2h timeout)
- **Hunter Daily Limit**: 15 calls
- **Email Daily Limit**: Configurable in daily_usage_stats

---

## 🚀 How to Run

### One-time backfill (for existing leads without drafts):
```bash
python backend/backfill_drafts.py
```

### Single cycle (test):
```bash
python -m backend.scheduler.cycle_manager --once
```

### 24/7 scheduler:
```bash
python backend/run_scheduler_24_7.py
```

---

## 📝 Notes

- All fixes verified and working as of March 1, 2026
- Pipeline optimized for India-focused internship discovery
- Duplicate prevention ensures one lead per internship
- Platform email rejection prevents false positives
- Hunter credit shield protects API quota
- Region filter reduces wasted scrape time on non-India roles
