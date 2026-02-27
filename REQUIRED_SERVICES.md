# 🔐 LazyIntern - Required Services

## ✅ All 5 Services Are Required

LazyIntern needs these 5 services to function properly:

---

## 1. 🗄️ Supabase (Database)

**Purpose:** Stores all data (internships, leads, drafts, events)

**Cost:** FREE (500MB database, 2GB bandwidth)

**Setup:**
1. Go to https://supabase.com/dashboard
2. Create new project
3. Wait for provisioning (~2 min)
4. Copy Project URL and Service Role Key
5. Run `db/schema.sql` in SQL Editor

**In .env:**
```bash
SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="YOUR_SERVICE_ROLE_KEY"
```

---

## 2. 🤖 Groq (AI Email Generation)

**Purpose:** Generates personalized emails using Llama 3.1 70B

**Cost:** FREE (30 requests/minute, generous limits)

**Setup:**
1. Go to https://console.groq.com/keys
2. Sign up with Google
3. Create API Key
4. Copy key (starts with `gsk_`)

**In .env:**
```bash
GROQ_API_KEY="gsk_YOUR_KEY_HERE"
GROQ_MODEL="llama-3.1-70b-versatile"
```

---

## 3. 📧 Gmail (Email Sending)

**Purpose:** Sends emails with resume attachment

**Cost:** FREE (250 emails/day)

**Setup:**
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download JSON file
6. Save as `backend/secrets/gmail_oauth_client.json`

**In .env:**
```bash
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
GMAIL_TOKEN_PATH="secrets/gmail_token.json"
GMAIL_SENDER="me"
```

**First run:** Opens browser for OAuth consent

---

## 4. 📱 Twilio (WhatsApp Approval)

**Purpose:** Sends approval requests via WhatsApp, receives YES/NO responses

**Cost:** FREE trial ($15 credit, ~3000 messages)

**Setup:**
1. Go to https://console.twilio.com/
2. Sign up (free trial)
3. Get Account SID and Auth Token from dashboard
4. Go to WhatsApp sandbox: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
5. Send join message to Twilio's WhatsApp number
6. Note the sandbox number (e.g., +14155238886)

**In .env:**
```bash
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token_here"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"  # Your WhatsApp
```

---

## 5. 🌐 ngrok (Webhook Tunnel)

**Purpose:** Exposes local backend to internet for Twilio webhooks

**Cost:** FREE (basic plan)

**Setup:**
1. Download from https://ngrok.com/download
2. Extract and run: `ngrok http 8000`
3. Copy HTTPS URL (e.g., `https://abc123.ngrok-free.app`)
4. Add to .env as PUBLIC_BASE_URL
5. Configure Twilio webhook with this URL

**In .env:**
```bash
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"
```

**Configure Twilio webhook:**
1. Go to https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Set "When a message comes in" to: `https://abc123.ngrok-free.app/twilio/webhook`
3. Save

**Important:** ngrok URL changes every time you restart it (unless you have a paid plan)

---

## 🎯 Why Each Service Is Required

### Supabase
- Stores all pipeline data
- Tracks daily usage limits
- Maintains audit log
- **Cannot be skipped:** System won't work without database

### Groq
- Generates personalized emails
- Uses AI to match resume with job description
- Creates follow-up templates
- **Cannot be skipped:** No emails without AI generation

### Gmail
- Sends emails to recruiters
- Attaches resume PDF
- Handles OAuth authentication
- **Cannot be skipped:** No outreach without email sending

### Twilio
- Human-in-the-loop approval
- Quality control before sending
- Prevents spam/mistakes
- **Cannot be skipped:** Core feature for quality assurance

### ngrok
- Enables Twilio webhooks
- Receives YES/NO responses
- Required for local development
- **Cannot be skipped:** Twilio can't reach localhost without it

---

## 💰 Total Cost

### Free Tier (Recommended)
- Supabase: $0
- Groq: $0
- Gmail: $0
- Twilio: $0 (free trial)
- ngrok: $0
- **Total: $0/month**

### After Free Trial
- Twilio: ~$0.005/message (~$15/month for 3000 messages)
- Everything else: Still FREE
- **Total: ~$15/month**

---

## 🚀 Setup Order

1. **Supabase** (5 min) - Set up database first
2. **Groq** (2 min) - Quick API key
3. **Gmail** (5 min) - OAuth setup
4. **Twilio** (10 min) - WhatsApp sandbox
5. **ngrok** (3 min) - Start tunnel and configure webhook

**Total time: ~25 minutes**

---

## 🔄 Production Deployment

For production (not local development):

### Replace ngrok with:
- Deploy backend to cloud (Railway, Render, Heroku)
- Use public URL directly
- No need for ngrok tunnel

### Example:
```bash
# Local development
PUBLIC_BASE_URL="https://abc123.ngrok-free.app"

# Production
PUBLIC_BASE_URL="https://lazyintern-backend.railway.app"
```

---

## ❓ FAQ

**Q: Can I skip Twilio and use auto-approval?**
A: No, WhatsApp approval is a core feature for quality control. Auto-approval is only a fallback for high-confidence leads (score ≥ 90) when you don't respond within 2 hours.

**Q: Can I use a different email service instead of Gmail?**
A: Not currently. The system is built specifically for Gmail API. You could modify the code to support other services.

**Q: Do I need ngrok in production?**
A: No, only for local development. In production, deploy backend to cloud and use the public URL.

**Q: Can I use Twilio production WhatsApp instead of sandbox?**
A: Yes, but you need to apply for WhatsApp Business API access. Sandbox is fine for testing.

**Q: What if ngrok URL changes?**
A: You need to update .env and reconfigure Twilio webhook. Consider ngrok paid plan for static URL.

---

## 🎯 Quick Checklist

Before running the system, verify:

- [ ] Supabase project created
- [ ] Database schema executed (10 tables)
- [ ] Groq API key obtained
- [ ] Gmail OAuth JSON downloaded
- [ ] Twilio account created
- [ ] WhatsApp sandbox joined
- [ ] ngrok installed and running
- [ ] All 5 services configured in .env
- [ ] Twilio webhook configured with ngrok URL

---

**All 5 services are essential for LazyIntern to work properly!** 🚀
