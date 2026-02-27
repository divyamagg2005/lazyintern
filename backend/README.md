# LazyIntern - Automated Internship Outreach Pipeline

> AI-powered internship discovery, personalized outreach, and intelligent follow-up system

## 🎯 What It Does

LazyIntern automates the entire internship application process:

1. **Discovers** internships from 60+ sources (YC, Wellfound, LinkedIn, Internshala, etc.)
2. **Validates** emails using MX records and SMTP pings
3. **Scores** opportunities based on your resume and preferences
4. **Generates** personalized emails using Groq AI
5. **Requests approval** via WhatsApp before sending
6. **Sends** emails with your resume attached via Gmail
7. **Tracks replies** and learns from feedback
8. **Follows up** automatically after 5 days

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Dashboard                       │
│              (Next.js + TailwindCSS + TypeScript)           │
│         Real-time metrics, funnel visualization             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Discovery  │  │  Validation  │  │   Outreach   │     │
│  │   Pipeline   │→ │   Pipeline   │→ │   Pipeline   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓              │
│  ┌──────────────────────────────────────────────────┐      │
│  │           Supabase PostgreSQL Database            │      │
│  │  (Internships, Leads, Drafts, Events, Retries)  │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Integrations                     │
│  Groq AI  │  Hunter.io  │  Twilio  │  Gmail  │  Firecrawl  │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Discovery Engine
- **3-tier scraping**: HTTP → Dynamic (Playwright) → Firecrawl fallback
- **60+ curated sources**: YC, Wellfound, LinkedIn, Internshala, AI labs
- **Smart deduplication**: Prevents reprocessing
- **Proxy rotation**: Avoids IP blocks

### Email Intelligence
- **Free regex extraction**: Finds emails in job descriptions
- **Hunter.io integration**: Domain-level email discovery with caching
- **4-step validation**: Format → Disposable check → MX records → SMTP ping
- **Confidence scoring**: Prioritizes high-quality leads

### AI Personalization
- **Groq-powered drafts**: Uses Llama 3.1 70B for natural emails
- **Resume-aware**: Matches your skills to job requirements
- **System prompt caching**: Reduces API costs by 90%
- **Fallback templates**: Works without API key

### Smart Scoring
- **3 kill gates**: Filters low-quality leads before API spend
- **Tunable weights**: Adjust scoring from dashboard
- **Historical learning**: Tracks reply rates per company
- **Pre-score threshold**: 40 for regex, 60 for Hunter

### Human-in-the-Loop
- **WhatsApp approval**: Review drafts before sending
- **Auto-approve**: High-scoring leads (90+) after 2hr timeout
- **Preview mode**: See full email before deciding
- **Quarantine system**: Re-evaluates rejections after 14 days

### Reliable Delivery
- **Gmail warmup**: 5→15 emails/day over 11 days
- **45min spacing**: Avoids spam flags
- **Resume attachment**: Auto-attaches PDF
- **Retry queue**: Exponential backoff for failures

### Feedback Loop
- **Reply detection**: Gmail Push Notifications
- **Sentiment analysis**: Positive/negative/neutral classification
- **Auto-cancel follow-ups**: If positive reply received
- **Scoring updates**: Learns from reply patterns

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account (free)
- API keys (see setup guide)

### 1. Clone & Install

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
scrapling install

# Frontend (from project root)
npm install
```

### 2. Set Up API Keys

See `backend/API_SETUP_GUIDE.md` for detailed instructions.

Required:
- Supabase (database)
- Groq (email generation)
- Twilio (WhatsApp approval)
- Gmail (sending)

Optional:
- Hunter.io (email discovery)
- Firecrawl (JS-heavy sites)

### 3. Configure Environment

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your API keys

# Frontend (from root)
# .env.local already configured to point to backend
```

### 4. Set Up Database

1. Create Supabase project
2. Run `backend/db/schema.sql` in SQL Editor
3. Verify 10 tables created

### 5. Run Setup Verification

```bash
cd backend
python test_setup.py
```

### 6. Start Services

```bash
# Terminal 1: Backend
cd backend
./start.bat  # Windows
# ./start.sh  # Mac/Linux

# Terminal 2: Frontend (from root)
npm run dev

# Terminal 3: Run one cycle (testing)
cd backend
python -m scheduler.cycle_manager --once
```

Open http://localhost:3000 for dashboard

## 📊 Dashboard

Real-time metrics across 6 panels:

1. **Overview**: Today's stats, reply rate, active retries
2. **Discovery**: Scraping health, tier success rates
3. **Email**: Regex vs Hunter split, validation failures
4. **Outreach**: Drafts, approvals, warmup progress
5. **Performance**: Full funnel, top company types
6. **Retries**: Failed jobs needing attention

## 🔄 Pipeline Flow

```
Scheduler (3x/day: 08:00, 13:00, 18:00)
   ↓
Retry Queue Processor (exponential backoff)
   ↓
Follow-up Queue (day 5 follow-ups)
   ↓
Quarantine Re-evaluation (14-day lookback)
   ↓
Discovery (3-tier scraping + proxy rotation)
   ↓
Deduplication (link + company+role)
   ↓
Pre-Score Gate 1 (< 40 → STOP)
   ↓
Regex Email Extraction (free)
   ↓
Pre-Score Gate 2 (40-59 + no email → STOP)
   ↓
Hunter Email Discovery (score 60+, domain cache)
   ↓
Email Validation Gate 3 (MX + SMTP → STOP if invalid)
   ↓
Full Scoring (resume overlap + tech stack + location + history)
   ↓
Full Score Gate 4 (< 60 → STOP)
   ↓
Groq Draft Generation (personalized email + follow-up)
   ↓
WhatsApp Approval (YES/NO/PREVIEW)
   ↓
Email Queue (warmup-aware, 45min spacing)
   ↓
Gmail Send (with resume attachment)
   ↓
Reply Detection (Gmail Push → classify → update history)
   ↓
Follow-up (day 5, auto-cancel if replied)
```

## 💰 Cost Breakdown

Monthly costs for 500 internships discovered:

| Service | Usage | Cost |
|---------|-------|------|
| Groq | ~200 drafts × 500 tokens | $0.50 |
| Hunter.io | ~50 domains | $0 (free tier) |
| Firecrawl | ~30 fallbacks | $0 (free tier) |
| Twilio WhatsApp | ~200 approvals | $1.00 |
| Gmail | ~150 emails | $0 (free) |
| Supabase | Database + storage | $0 (free tier) |
| **Total** | | **~$1.50/month** |

## 🛡️ Safety Features

- **Warmup schedule**: Protects Gmail sender reputation
- **Rate limiting**: Respects API limits
- **Robots.txt**: Honors scraping rules
- **SMTP throttling**: Avoids blacklisting
- **Retry queue**: Handles failures gracefully
- **Webhook verification**: Twilio signature validation
- **No spam**: Human approval required

## 📈 Success Metrics

After 1 month of operation:
- 500+ internships discovered
- 200+ emails validated
- 100+ emails sent
- 10+ positive replies (10% reply rate)
- 2+ interview invitations
- < $20 total API costs

## 🔧 Configuration

### Scoring Weights (tunable from dashboard)
- Relevance: 35%
- Resume overlap: 25%
- Tech stack: 20%
- Location: 10%
- Historical success: 10%

### Daily Limits
- Emails: 5→15 (warmup)
- Hunter calls: 15
- Firecrawl: 10
- Groq: Unlimited (rate limited)

### Thresholds
- Pre-score regex: 40
- Pre-score Hunter: 60
- Full score: 60
- Auto-approve: 90

## 📚 Documentation

- `backend/API_SETUP_GUIDE.md` - API key setup
- `backend/SETUP_INSTRUCTIONS.md` - Detailed setup
- `backend/db/schema.sql` - Database schema
- `WORK_PLAN.md` - Development roadmap
- `logs/final_pipeline.md` - Complete pipeline spec

## 🐛 Troubleshooting

See `backend/SETUP_INSTRUCTIONS.md` for common issues.

Quick checks:
```bash
# Verify setup
cd backend
python test_setup.py

# Check API health
curl http://localhost:8000/healthz

# View logs
# Backend: Terminal output
# Frontend: Browser console (F12)
```

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt!

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Built with:
- FastAPI (backend)
- Next.js (frontend)
- Supabase (database)
- Groq (AI)
- Scrapling (scraping)
- Twilio (WhatsApp)
- Gmail API (sending)

---

**Status**: Phase 1 & 2 Complete ✅  
**Next**: Get API keys and start discovering internships!

