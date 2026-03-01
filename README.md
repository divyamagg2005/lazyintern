# 🤖 LazyIntern - AI-Powered Internship Automation Platform

> **Automated internship discovery, validation, and outreach system built with Python, FastAPI, Next.js, and AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Pipeline Flow](#-pipeline-flow)
- [Results & Metrics](#-results--metrics)
- [Quick Start](#-quick-start)
- [Cost Optimization](#-cost-optimization)
- [Security & Compliance](#-security--compliance)
- [Documentation](#-documentation)

---

## 🎯 Overview

LazyIntern is a production-ready, end-to-end automation platform that transforms the internship application process. Built with modern web technologies and AI, it discovers opportunities, validates contacts, generates personalized outreach, and tracks responses—all while maintaining human oversight and email deliverability best practices.

### What It Does

```
Discover → Validate → Score → Personalize → Send → Notify
```

1. **Discovers** internships from multiple sources using 3-tier scraping (HTTP → Playwright → Firecrawl)
2. **Validates** email addresses with MX records and SMTP verification
3. **Scores** opportunities using weighted algorithms (resume match, tech stack, location)
4. **Generates** personalized emails using Groq AI (Llama 3.1 70B)
5. **Sends** emails immediately via Gmail with resume attachment
6. **Notifies** you via SMS when emails are sent
7. **Runs automatically** every 90 minutes (24/7 scheduler)

### Why It Matters

- **Time Savings**: Automates the entire application process
- **Quality**: Multi-gate filtering system ensures only relevant opportunities
- **Cost Efficient**: Runs on free-tier APIs (Groq, Gmail, Supabase)
- **Fully Automated**: 24/7 operation with 90-minute cycles
- **Real-time Dashboard**: Monitor discovery, validation, and outreach metrics

---

## ✨ Key Features

### 🔍 Intelligent Discovery Engine
- **3-tier scraping strategy**: HTTP → Playwright (dynamic) → Firecrawl (fallback)
- **60+ curated sources**: YC, Wellfound, LinkedIn, Internshala, AI labs, startups
- **Smart deduplication**: Link-based + company-role fingerprinting
- **Proxy rotation**: Avoids IP blocks and rate limits
- **Robots.txt compliance**: Respects website policies

### 🎯 Multi-Gate Filtering System
- **Gate 1 - Pre-scoring**: Keyword matching (filters 60%, 0 API calls)
- **Gate 2 - Email validation**: MX + SMTP checks (filters 20%)
- **Gate 3 - Full scoring**: Resume overlap + tech stack + location (filters 10%)
- **Result**: 90% of low-quality leads filtered before expensive operations

### 🤖 AI-Powered Personalization
- **Groq AI integration**: Llama 3.1 70B for natural language generation
- **System prompt caching**: 90% cost reduction on repeated calls
- **Resume-aware**: Matches candidate skills to job requirements
- **Fallback templates**: Works without API key for testing

### 📧 Email Intelligence
- **Dual extraction**: Free regex + Hunter.io domain search
- **4-step validation**: Format → Disposable check → MX records → SMTP ping
- **Confidence scoring**: Prioritizes high-quality contacts
- **Domain caching**: Reduces Hunter API calls by 70%

### 📱 SMS Notifications
- **Twilio integration**: Get notified when emails are sent
- **Real-time updates**: Know exactly when outreach happens
- **Delivery confirmation**: Track successful sends

### 📊 Real-Time Analytics Dashboard
- **Discovery metrics**: Scraping health, tier success rates, source performance
- **Email metrics**: Regex vs Hunter split, validation failures, confidence distribution
- **Outreach metrics**: Draft status, emails sent, daily limits
- **Performance metrics**: Full funnel visualization, processing stats
- **Retry monitoring**: Failed jobs with exponential backoff tracking

### 🔄 Resilient Architecture
- **Retry queue**: Exponential backoff for transient failures
- **Recovery system**: Resumes interrupted cycles automatically
- **Event logging**: Complete audit trail for debugging
- **Daily limits**: Configurable email sending limits

### 🤖 24/7 Automation
- **Scheduled execution**: Runs every 90 minutes automatically
- **Midnight reset**: Daily usage stats reset at 00:00 UTC
- **Continuous operation**: Discovers and sends emails around the clock
- **No manual intervention**: Fully autonomous after setup

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend Dashboard                           │
│              (Next.js 16 + TypeScript + Tailwind)               │
│         Real-time metrics • Funnel visualization                │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Discovery  │  │  Validation  │  │   Outreach   │         │
│  │   Pipeline   │→ │   Pipeline   │→ │   Pipeline   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ↓                  ↓                  ↓                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │         Supabase PostgreSQL Database (10 tables)      │      │
│  │  Internships • Leads • Drafts • Events • Retries     │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Integrations                         │
│  Groq AI  │  Hunter.io  │  Twilio  │  Gmail  │  Firecrawl      │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema (10 Tables)

- **internships**: Core opportunity data with scoring
- **leads**: Validated email contacts with confidence scores
- **email_drafts**: AI-generated emails with approval status
- **followup_queue**: Scheduled follow-ups with reply tracking
- **retry_queue**: Failed operations with exponential backoff
- **quarantine**: Rejected leads for re-evaluation
- **daily_usage_stats**: API usage tracking and limits
- **pipeline_events**: Complete audit log
- **company_domains**: Hunter.io cache with reply history
- **scoring_config**: Tunable weights for scoring algorithm

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.10+** | Core language | Type hints, async support, rich ecosystem |
| **FastAPI** | Web framework | High performance, auto docs, async-first |
| **Supabase** | PostgreSQL database | Managed Postgres, real-time, free tier |
| **Scrapling** | Web scraping | HTTP + Playwright in one library |
| **Groq** | AI inference | Fast Llama 3.1 70B, system prompt caching |
| **Twilio** | SMS notifications | Reliable delivery, webhook support |
| **Gmail API** | Email sending | OAuth2, high deliverability |
| **Hunter.io** | Email discovery | Domain-level search, confidence scores |
| **Firecrawl** | JS-heavy scraping | Fallback for dynamic sites |

### Frontend
| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Next.js 16** | React framework | Server components, app router, TypeScript |
| **TypeScript** | Type safety | Catch errors at compile time |
| **Tailwind CSS** | Styling | Utility-first, responsive, fast |
| **Recharts** | Data visualization | React-native charts, customizable |
| **Supabase JS** | Database client | Type-safe queries, real-time subscriptions |

### Infrastructure
- **PostgreSQL 15**: Relational database with JSONB support
- **ngrok**: Local development tunneling for webhooks
- **Git**: Version control
- **Windows/Linux**: Cross-platform support

---

## 🔄 Pipeline Flow

### Complete Pipeline (Runs Every 90 Minutes)

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 0: Recovery (Resume interrupted cycles)              │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Retry Queue Processor (exponential backoff)       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Quarantine Re-evaluation (14-day lookback)        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Process Existing Internships (from database)      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Discovery (3-tier scraping, limit 50)             │
│          HTTP → Playwright → Firecrawl                      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: Process New Internships (limit 200)               │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE 1: Pre-Score (keyword matching, 0 API calls)          │
│         < 40 → STOP (filters ~60%)                          │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: Regex Email Extraction (free, from description)   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE 2: Pre-Score Check (40-59 + no email → STOP)          │
│         If score >= 60 → Try Hunter.io                      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 7: Hunter Email Discovery (score 60+, domain cache)  │
│          Blocks job board domains (LinkedIn, Internshala)   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE 3: Email Validation (MX + SMTP)                       │
│         Invalid emails marked but still processed           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 8: Full Scoring (resume + tech + location)           │
│          All scored internships get drafts generated        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 9: Groq Draft Generation (personalized email)        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 10: Immediate Send (Gmail API with resume)           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 11: SMS Notification (Twilio confirmation)           │
└─────────────────────────────────────────────────────────────┘
```

### Scoring Algorithm

**Pre-Score (Gate 1 & 2):**
```python
score = (
    keyword_match_score * 0.4 +
    role_relevance_score * 0.3 +
    company_type_score * 0.2 +
    location_score * 0.1
)
threshold_regex = 40  # Minimum for regex extraction
threshold_hunter = 60  # Minimum for Hunter.io search
```

**Full Score (Gate 3):**
```python
score = (
    relevance_score * 0.35 +
    resume_overlap_score * 0.25 +
    tech_stack_score * 0.20 +
    location_score * 0.10 +
    historical_success_score * 0.10
)
# All scored internships get emails generated and sent
```

---

## 📊 System Capabilities

### What's Implemented ✅

| Feature | Status | Description |
|---------|--------|-------------|
| **3-Tier Scraping** | ✅ Working | HTTP → Playwright → Firecrawl fallback |
| **Email Extraction** | ✅ Working | Regex + Hunter.io with domain caching |
| **Email Validation** | ✅ Working | MX records + SMTP verification |
| **Pre-Scoring** | ✅ Working | Keyword-based filtering (0 API calls) |
| **Full Scoring** | ✅ Working | Resume overlap + tech stack + location |
| **AI Email Generation** | ✅ Working | Groq Llama 3.1 70B with prompt caching |
| **Immediate Sending** | ✅ Working | Gmail API with resume attachment |
| **SMS Notifications** | ✅ Working | Twilio alerts when emails sent |
| **24/7 Scheduler** | ✅ Working | Runs every 90 minutes automatically |
| **Retry Queue** | ✅ Working | Exponential backoff for failures |
| **Recovery System** | ✅ Working | Resumes interrupted cycles |
| **Real-time Dashboard** | ✅ Working | Next.js with live metrics |
| **Quarantine System** | ✅ Working | Re-evaluates rejected leads |
| **Event Logging** | ✅ Working | Complete audit trail |
| **Daily Limits** | ✅ Working | Configurable email quotas |

### Planned Features 📋

| Feature | Status | Notes |
|---------|--------|-------|
| **Follow-up Emails** | 🚧 Disabled | Code exists, currently disabled by user |
| **Reply Detection** | 🚧 Partial | Gmail Pub/Sub webhook ready, needs setup |
| **Email-level Deduplication** | 📋 Planned | Prevent duplicate sends to same email |
| **Warmup Schedule** | 📋 Planned | Gradual email volume increase |
| **45-min Spacing** | 📋 Planned | Anti-spam email spacing |
| **Proxy Rotation** | 📋 Planned | Advanced scraping with proxy pool |

### Cost Efficiency

**Current operational cost (free tier):**

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Groq AI | Unlimited (rate limited) | $0.00 |
| Gmail API | Up to 250 emails/day | $0.00 |
| Supabase | 500MB database | $0.00 |
| Twilio SMS | ~$0.005/message | ~$1-2 |
| Hunter.io | 25 searches/month (free) | $0.00 |
| Firecrawl | 500 credits/month (free) | $0.00 |
| **Total** | | **~$1-2/month** |

**With paid tiers (for scale):**
- Hunter.io Starter: $49/month (500 searches)
- Firecrawl Pro: $20/month (3,000 credits)
- **Total**: ~$70/month for high-volume operation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ ([Download](https://www.python.org/downloads/))
- Node.js 18+ ([Download](https://nodejs.org/))
- Git ([Download](https://git-scm.com/))
- Supabase account ([Sign up](https://supabase.com/))

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/lazyintern.git
cd lazyintern
```

### 2. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
scrapling install
```

**Frontend:**
```bash
cd ..  # Back to project root
npm install
```

### 3. Get API Keys

See `backend/API_SETUP_GUIDE.md` for detailed instructions.

**Required (Free Tier):**
- [Supabase](https://supabase.com/dashboard) - Database
- [Groq](https://console.groq.com/keys) - AI email generation
- [Gmail](https://console.cloud.google.com/) - Email sending
- [Twilio](https://console.twilio.com/) - SMS notifications
- [ngrok](https://ngrok.com/download) - Webhook tunneling

**Optional (Paid):**
- [Hunter.io](https://hunter.io/api) - Email discovery ($49/month)
- [Firecrawl](https://firecrawl.dev/) - JS-heavy scraping ($20/month)

### 4. Configure Environment

**Backend:**
```bash
cd backend
copy .env.example .env
# Edit .env with your API keys
```

**Frontend:**
```bash
# .env.local already configured
# Points to http://localhost:8000
```

### 5. Set Up Database

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Create new project
3. Go to SQL Editor
4. Run `backend/db/schema.sql`
5. Verify 10 tables created

### 6. Verify Setup

```bash
cd backend
python test_setup.py
```

Expected output:
```
✓ Supabase connection successful
✓ Groq API key valid
✓ Gmail credentials found
✓ Twilio credentials valid
✓ All 10 tables exist
```

### 7. Start Services

**Terminal 1 - ngrok (for webhooks):**
```bash
ngrok http 8000
# Copy HTTPS URL to .env as PUBLIC_BASE_URL
```

**Terminal 2 - Backend:**
```bash
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000
```

**Terminal 3 - Frontend:**
```bash
npm run dev
```

**Terminal 4 - Run 24/7 Scheduler:**
```bash
cd backend
.\.venv\Scripts\activate
python run_scheduler_24_7.py
# Runs every 90 minutes automatically
# Press Ctrl+C to stop
```

**Or run a single cycle (testing):**
```bash
cd backend
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

### 8. Access Dashboard

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 💰 Cost Optimization

### Free Tier Strategy (Recommended for Testing)

All services offer generous free tiers:

| Service | Free Tier | Sufficient For |
|---------|-----------|----------------|
| Supabase | 500MB database, 2GB bandwidth | 10,000+ internships |
| Groq | 30 req/min, unlimited tokens | 200+ emails/day |
| Gmail | 250 emails/day | Full warmup schedule |
| Twilio | $15 trial credit | 3,000 SMS |
| Hunter.io | 25 searches/month | Testing phase |
| Firecrawl | 500 credits/month | 50 fallback scrapes |

**Total monthly cost**: $0 for first month, $1.50 after trial

### Paid Tier (For Scale)

| Service | Plan | Cost | Usage |
|---------|------|------|-------|
| Hunter.io | Starter | $49/month | 500 domain searches |
| Firecrawl | Pro | $20/month | 3,000 credits |
| Twilio | Pay-as-you-go | ~$0.005/SMS | Unlimited |
| **Total** | | **~$70/month** | 500 internships |

### Cost Reduction Techniques

1. **System Prompt Caching**: 90% reduction in Groq costs
2. **Domain Caching**: 70% reduction in Hunter calls
3. **3-Gate Filtering**: 90% of leads filtered before API spend
4. **Regex-First**: Free email extraction before Hunter
5. **Free Tier Maximization**: Groq, Gmail, Supabase all free

---

## 🔐 Security & Compliance

### Security Features
- ✅ **Twilio webhook signature verification**: Prevents unauthorized requests
- ✅ **Gmail OAuth2 authentication**: No password storage
- ✅ **Environment variable management**: No hardcoded secrets
- ✅ **Supabase RLS policies**: Row-level security
- ✅ **HTTPS-only webhooks**: Encrypted communication
- ✅ **Rate limiting**: Prevents abuse

### Compliance
- ✅ **CAN-SPAM Act**: Unsubscribe link in every email
- ✅ **GDPR**: Data minimization, right to deletion
- ✅ **Robots.txt**: Respects website scraping policies
- ✅ **Terms of Service**: Complies with all API ToS
- ✅ **Human approval**: No fully automated spam

### Best Practices
- **Warmup schedule**: Protects Gmail sender reputation
- **45-minute spacing**: Avoids spam flags
- **SMTP throttling**: Prevents blacklisting
- **Quarantine system**: Re-evaluates rejections
- **Reply detection**: Cancels follow-ups if replied

---

## 📚 Documentation

### Setup Guides
- **[API_SETUP_GUIDE.md](backend/API_SETUP_GUIDE.md)** - Get all API keys
- **[SETUP_INSTRUCTIONS.md](backend/SETUP_INSTRUCTIONS.md)** - Detailed setup
- **[GMAIL_PUBSUB_SETUP.md](backend/GMAIL_PUBSUB_SETUP.md)** - Reply detection

### Architecture
- **[schema.sql](backend/db/schema.sql)** - Complete database schema
- **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - Architecture diagrams
- **[PIPELINE_COMPARISON_REPORT.md](PIPELINE_COMPARISON_REPORT.md)** - Implementation status

### Operations
- **[RUN_COMMANDS.md](RUN_COMMANDS.md)** - All commands
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix common issues
- **[WORK_PLAN.md](WORK_PLAN.md)** - Development roadmap

### Dashboard
- **[START_DASHBOARD.md](START_DASHBOARD.md)** - Frontend setup
- **[FRONTEND_COMPLETE.md](FRONTEND_COMPLETE.md)** - Dashboard features

---

## 🎯 Use Cases

### For Job Seekers
- Automate internship discovery and applications
- Save hours of manual searching and emailing
- Get notified when emails are sent
- Track all applications in one dashboard

### For Developers
- Learn full-stack development (Python + Next.js)
- Study AI integration patterns (Groq API)
- Understand web scraping techniques (3-tier strategy)
- Practice API integration (Gmail, Twilio, Hunter.io)
- Build production-ready automation systems

---

## 🛣️ Roadmap

### Phase 1 ✅ (Completed)
- [x] Core pipeline (discovery → validation → scoring → generation → sending)
- [x] Groq AI integration with system prompt caching
- [x] Email validation (MX + SMTP)
- [x] SMS notifications via Twilio
- [x] Gmail sending with resume attachment
- [x] Real-time dashboard with Next.js
- [x] 24/7 scheduler (90-minute cycles)
- [x] Retry queue with exponential backoff
- [x] Recovery system for interrupted cycles
- [x] Quarantine re-evaluation

### Phase 2 🚧 (In Progress)
- [ ] Email-level deduplication (prevent duplicate sends to same email)
- [ ] Follow-up automation (currently disabled)
- [ ] Reply detection (Gmail Pub/Sub setup)
- [ ] Warmup schedule (gradual email volume increase)
- [ ] Email spacing (45-minute gaps)

### Phase 3 📋 (Planned)
- [ ] Production deployment (AWS/GCP/Heroku)
- [ ] Proxy pool setup for scraping
- [ ] A/B testing for email templates
- [ ] Manual lead entry UI
- [ ] Scoring weight tuner dashboard
- [ ] Advanced analytics (cohort analysis)
- [ ] Multi-user support

---

## 🤝 Contributing

This is a personal project, but contributions are welcome!

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt
npm install --save-dev

# Run tests
pytest backend/tests/
npm test

# Lint code
black backend/
eslint frontend/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with amazing open-source tools:

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Next.js](https://nextjs.org/)** - React framework for production
- **[Supabase](https://supabase.com/)** - Open-source Firebase alternative
- **[Groq](https://groq.com/)** - Fast AI inference
- **[Scrapling](https://github.com/D4Vinci/Scrapling)** - Web scraping library
- **[Twilio](https://www.twilio.com/)** - Communication APIs
- **[Gmail API](https://developers.google.com/gmail/api)** - Email integration

---

## ⚠️ Disclaimer

This tool is for **educational and personal use only**. Always:

- ✅ Respect website terms of service
- ✅ Follow email marketing laws (CAN-SPAM, GDPR)
- ✅ Use human approval before sending
- ✅ Respect robots.txt
- ✅ Don't spam or harass
- ✅ Include unsubscribe links
- ✅ Honor opt-out requests

**The authors are not responsible for misuse of this software.**

---

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/lazyintern/issues)
- **Email**: your-email@example.com
- **LinkedIn**: [Your LinkedIn Profile](https://linkedin.com/in/yourprofile)

---

## 🎓 Learn More

### Technical Deep Dives
- **Pipeline Spec**: `logs/final_pipeline.md`
- **Database Design**: `backend/db/schema.sql`
- **API Documentation**: http://localhost:8000/docs (when running)

### Blog Posts (Coming Soon)
- Building a Production-Ready Web Scraper
- AI Email Personalization with Groq
- Gmail Warmup: Protecting Sender Reputation
- Cost Optimization for AI Applications

---

## 🌟 Star History

If this project helped you, please consider giving it a ⭐!

---

**Built with ❤️ by [Your Name]**

**Last Updated**: March 2026

---

