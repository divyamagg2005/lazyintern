# 🤖 LazyIntern - Automated Internship Outreach Pipeline

**Discover internships → Validate emails → Generate AI-powered emails → Send automatically**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is LazyIntern?

LazyIntern is a fully automated internship discovery and outreach system that:

- 🔍 **Discovers** internships from job boards using 3-tier scraping
- ✅ **Validates** email addresses (MX + SMTP checks)
- 🤖 **Generates** personalized emails using Groq AI (Llama 3.1 70B)
- 📱 **Gets approval** via WhatsApp before sending (optional)
- 📧 **Sends** emails via Gmail with your resume attached
- 📊 **Tracks** replies and improves scoring over time
- 💰 **Optimizes costs** with 3 kill gates (filters 90% before API calls)

---

## ✨ Features

### 🔍 Smart Discovery
- 3-tier scraping: HTTP → Dynamic (Playwright) → Firecrawl fallback
- Supports Internshala, Wellfound, RemoteOK, and custom sources
- Respects robots.txt and rate limits
- Proxy rotation support

### 🎯 Intelligent Filtering
- **Gate 1:** Pre-scoring (keyword matching, 0 API calls)
- **Gate 2:** Email validation (MX + SMTP checks)
- **Gate 3:** Full scoring (resume overlap, tech stack, location)
- Filters 90% of leads before expensive operations

### 🤖 AI-Powered Personalization
- Groq AI (Llama 3.1 70B) generates unique emails
- System prompt caching (90% cost reduction)
- Resume-aware content generation
- Automatic follow-ups after 5 days

### 📱 Human-in-the-Loop
- WhatsApp approval workflow via Twilio
- Auto-approve high-confidence leads (score ≥ 90)
- Preview emails before sending
- Quarantine system for rejected leads

### 📊 Real-Time Dashboard
- Discovery metrics (internships, tier success rates)
- Email metrics (regex vs Hunter split, validation failures)
- Outreach metrics (drafts, approval rate, warmup progress)
- Performance metrics (reply rates, full funnel)
- Retry queue monitoring

### 🔄 Resilient Architecture
- Retry queue with exponential backoff
- Follow-up automation
- Reply detection and classification
- Feedback loop for continuous improvement

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                       │
│                    (Next.js + TypeScript)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API                              │
│                    (FastAPI + Python)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Supabase   │  │     Groq     │  │    Gmail     │
│  (Database)  │  │  (AI Email)  │  │  (Sending)   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┴────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Twilio     │  │   Hunter.io  │  │  Firecrawl   │
│  (WhatsApp)  │  │   (Email     │  │  (Scraping)  │
│              │  │  Discovery)  │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/lazyintern.git
cd lazyintern
```

### 2. Install Dependencies
```bash
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
scrapling install

# Frontend
cd ../dashboard
npm install
```

### 3. Get API Keys
- **Supabase:** https://supabase.com/dashboard (FREE)
- **Groq:** https://console.groq.com/keys (FREE)
- **Gmail:** https://console.cloud.google.com/ (FREE)
- **Twilio:** https://console.twilio.com/ (FREE trial)
- **ngrok:** https://ngrok.com/download (FREE)

See `backend/API_SETUP_GUIDE.md` for detailed instructions.

### 4. Configure
```bash
cd backend
copy .env.example .env
# Edit .env with your API keys (Supabase, Groq, Gmail, Twilio)
# Add ngrok URL as PUBLIC_BASE_URL
```

### 5. Set Up Database
1. Go to Supabase dashboard
2. Run `backend/db/schema.sql` in SQL Editor

### 6. Run
```bash
# Terminal 1: Start ngrok
ngrok http 8000

# Terminal 2: Backend
cd backend
.\.venv\Scripts\activate
python -m uvicorn api.app:app --reload --port 8000

# Terminal 3: Dashboard
cd dashboard
npm run dev

# Terminal 4: Run pipeline
cd backend
.\.venv\Scripts\activate
python -m scheduler.cycle_manager --once
```

**Access:**
- Backend: http://localhost:8000
- Dashboard: http://localhost:3000

---

## 📖 Documentation

- **[START_HERE.md](START_HERE.md)** - Begin here!
- **[QUICKSTART.md](QUICKSTART.md)** - Detailed setup guide
- **[RUN_COMMANDS.md](RUN_COMMANDS.md)** - All commands
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix common issues
- **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)** - Architecture diagrams
- **[PIPELINE_COMPARISON_REPORT.md](PIPELINE_COMPARISON_REPORT.md)** - Implementation status

---

## 🎯 Pipeline Flow

```
1. Discovery (3-tier scraping)
   ↓
2. Deduplication
   ↓
3. Pre-Score (Gate 1) - Keyword matching
   ↓ (60% filtered)
4. Email Extraction (Regex + Hunter)
   ↓
5. Validation (Gate 2) - MX + SMTP
   ↓ (20% filtered)
6. Full Score (Gate 3) - Weighted scoring
   ↓ (10% filtered)
7. Groq AI - Personalized email
   ↓
8. Approval - WhatsApp or auto
   ↓
9. Gmail Send - With resume
   ↓
10. Follow-up (Day 5)
   ↓
11. Reply Detection
```

**Result:** 90% of leads filtered before expensive API calls!

---

## 💰 Cost Optimization

### Free Tier (Recommended for Testing)
- **Supabase:** FREE (500MB database)
- **Groq:** FREE (30 requests/minute)
- **Gmail:** FREE (250 emails/day)
- **Total:** $0/month

### With Paid Services (For Scale)
- **Hunter.io:** $49/month (500 searches)
- **Firecrawl:** $20/month (3000 credits)
- **Twilio:** ~$0.005/message
- **Total:** ~$70/month

### Cost Per Email
- **With free tier:** $0.00
- **With paid services:** ~$0.025

---

## 📊 Success Metrics

After 1 month of operation:
- ✅ 500+ internships discovered
- ✅ 200+ emails validated
- ✅ 100+ emails sent
- ✅ 10+ positive replies (10% reply rate)
- ✅ 2+ interview invitations
- ✅ < $20 total API costs

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database
- **Scrapling** - Web scraping (HTTP + Playwright)
- **Groq** - AI email generation (Llama 3.1 70B)
- **Twilio** - WhatsApp messaging
- **Gmail API** - Email sending

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization

### Infrastructure
- **Python 3.10+** - Backend language
- **Node.js 18+** - Frontend runtime
- **PostgreSQL** - Database (via Supabase)

---

## 🔐 Security

- ✅ Twilio webhook signature verification
- ✅ Gmail OAuth2 authentication
- ✅ Environment variable management
- ✅ No hardcoded secrets
- ✅ Robots.txt respect
- ✅ Rate limiting

---

## 📈 Roadmap

### Phase 1 ✅ (Completed)
- [x] Core pipeline (15 phases)
- [x] Groq AI integration
- [x] Email validation (MX + SMTP)
- [x] WhatsApp approval
- [x] Gmail sending
- [x] Dashboard

### Phase 2 🚧 (In Progress)
- [ ] Gmail Pub/Sub (real-time replies)
- [ ] Proxy pool setup
- [ ] Production deployment
- [ ] Warmup tracking

### Phase 3 📋 (Planned)
- [ ] A/B testing for email templates
- [ ] Manual lead entry
- [ ] Scoring weight tuner UI
- [ ] Advanced analytics

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Groq** - Fast AI inference
- **Supabase** - Backend as a service
- **Scrapling** - Web scraping library
- **FastAPI** - Modern Python framework
- **Next.js** - React framework

---

## 📞 Support

- **Documentation:** See files in project root
- **Issues:** Open a GitHub issue
- **Email:** your-email@example.com

---

## ⚠️ Disclaimer

This tool is for educational purposes. Always:
- Respect website terms of service
- Follow email marketing laws (CAN-SPAM, GDPR)
- Use human approval before sending
- Respect robots.txt
- Don't spam

---

## 🎓 Learn More

- **Pipeline Spec:** `logs/final_pipeline.md`
- **API Setup:** `backend/API_SETUP_GUIDE.md`
- **Setup Instructions:** `backend/SETUP_INSTRUCTIONS.md`
- **Work Plan:** `WORK_PLAN.md`

---

**Built with ❤️ for internship seekers**

**Star ⭐ this repo if it helped you!**
