# 🔑 API Keys Setup Guide

## ⚡ REQUIRED API KEYS - Set these up NOW

### 1. Groq API Key ✅ COMPLETED
**Website:** https://console.groq.com/keys

**Steps:**
1. Go to https://console.groq.com/keys
2. Sign up / Log in with Google
3. Click "Create API Key"
4. Copy the key (starts with `gsk_...`)
5. Add to `backend/.env`:
   ```
   GROQ_API_KEY="gsk_your_key_here"
   GROQ_MODEL="llama-3.1-70b-versatile"
   ```

**Cost:** FREE - 30 requests/minute, generous free tier

---

### 2. Twilio WhatsApp ✅ COMPLETED
**Website:** https://console.twilio.com/

**Steps:**
1. Go to https://console.twilio.com/
2. Sign up / Log in
3. Get your Account SID and Auth Token from dashboard
4. **For Testing (WhatsApp Sandbox):**
   - Go to https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - Send "join <your-sandbox-code>" to the Twilio WhatsApp number
   - Use sandbox number as `TWILIO_FROM_NUMBER`
5. **For Production:**
   - Request WhatsApp Business API access
   - Get approved WhatsApp number

6. Add to `backend/.env`:
   ```
   TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxx"
   TWILIO_AUTH_TOKEN="your_auth_token"
   TWILIO_FROM_NUMBER="whatsapp:+14155238886"  # Sandbox number
   APPROVER_TO_NUMBER="whatsapp:+919811394884"  # Your WhatsApp
   PUBLIC_BASE_URL="https://your-ngrok-url.ngrok-free.app"  # For webhooks
   ```

**Cost:** 
- Sandbox: FREE for testing
- Production: ~$0.005 per message

---

### 3. Gmail API ✅ COMPLETED
**Website:** https://console.cloud.google.com/

**Steps:**
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Download JSON file
5. Save the JSON file as `backend/secrets/gmail_oauth_client.json`
6. Add to `backend/.env`:
   ```
   GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
   GMAIL_TOKEN_PATH="secrets/gmail_token.json"
   GMAIL_SENDER="me"
   ```
7. First run will open browser for OAuth consent

**Cost:** FREE - 250 emails/day for free Gmail accounts

---

### 4. Supabase Database ⚠️ REQUIRED
**Website:** https://supabase.com/dashboard

**Steps:**
1. Go to https://supabase.com/dashboard
2. Create new project
3. Wait for database to provision (~2 minutes)
4. Go to "Project Settings" > "API"
5. Copy:
   - Project URL
   - Service Role Key (secret, for server-side)
6. Add to `backend/.env`:
   ```
   SUPABASE_URL="https://xxxxx.supabase.co"
   SUPABASE_SERVICE_ROLE_KEY="eyJhbGc..."
   ```
7. Run database schema:
   - Go to "SQL Editor"
   - Copy contents of `backend/db/schema.sql`
   - Execute

**Cost:** FREE tier - 500MB database, 2GB bandwidth

---

### 5. Hunter.io API (Optional but Recommended)
**Website:** https://hunter.io/api-keys

**Steps:**
1. Go to https://hunter.io/api-keys
2. Sign up / Log in
3. Copy your API key
4. Add to `backend/.env`:
   ```
   HUNTER_API_KEY="your_hunter_key"
   ```

**Cost:** 
- FREE: 25 searches/month
- Paid: $49/month for 500 searches

---

### 6. Firecrawl API (Optional)
**Website:** https://www.firecrawl.dev/

**Steps:**
1. Go to https://www.firecrawl.dev/
2. Sign up for API access
3. Get API key from dashboard
4. Add to `backend/.env`:
   ```
   FIRECRAWL_API_KEY="fc-your_key"
   ```

**Cost:** 
- FREE: 500 credits/month
- Paid: $20/month for 3000 credits

---

## 📝 Complete .env Template

Create `backend/.env` with this template:

```bash
############################
# LazyIntern backend config #
############################

# Supabase (REQUIRED)
SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="YOUR_SERVICE_ROLE_KEY"

# Groq (REQUIRED for email generation)
GROQ_API_KEY="gsk_YOUR_KEY"
GROQ_MODEL="llama-3.1-70b-versatile"

# Hunter (Optional - for email discovery)
HUNTER_API_KEY=""

# Firecrawl (Optional - for JS-heavy sites)
FIRECRAWL_API_KEY=""

# Twilio WhatsApp (REQUIRED for approval)
TWILIO_ACCOUNT_SID="ACxxxxx"
TWILIO_AUTH_TOKEN="your_token"
TWILIO_FROM_NUMBER="whatsapp:+14155238886"
APPROVER_TO_NUMBER="whatsapp:+919811394884"
PUBLIC_BASE_URL="https://your-ngrok-url.ngrok-free.app"

# Gmail API (REQUIRED for sending)
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
GMAIL_TOKEN_PATH="secrets/gmail_token.json"
GMAIL_SENDER="me"

# Email validation
ENABLE_SMTP_PING="true"
```

---

## 🚀 Quick Start Checklist

- [ ] Create Groq account → Get API key
- [ ] Create Twilio account → Set up WhatsApp sandbox
- [ ] Create Google Cloud project → Enable Gmail API → Download OAuth JSON
- [ ] Create Supabase project → Run schema.sql
- [ ] (Optional) Create Hunter.io account → Get API key
- [ ] (Optional) Create Firecrawl account → Get API key
- [ ] Create `backend/.env` file with all keys
- [ ] Create `backend/secrets/` folder
- [ ] Place Gmail OAuth JSON in `secrets/gmail_oauth_client.json`
- [ ] Add resume PDF to `backend/data/resume.pdf`

---

## 🧪 Testing Setup

After adding all keys, test each integration:

```bash
# Test Groq
python -c "from pipeline.groq_client import generate_draft; print('Groq OK')"

# Test Gmail (will open browser for OAuth)
python -c "from outreach.gmail_client import _build_service; _build_service(); print('Gmail OK')"

# Test Twilio
python -c "from approval.twilio_sender import _twilio_client; print('Twilio OK' if _twilio_client() else 'Twilio not configured')"

# Test Supabase
python -c "from core.supabase_db import db; db.get_or_create_daily_usage(); print('Supabase OK')"
```

---

## ⚠️ IMPORTANT NOTES

1. **Never commit `.env` to git** - it's already in `.gitignore`
2. **Gmail OAuth**: First run opens browser for consent
3. **Twilio Webhook**: Use ngrok for local testing: `ngrok http 8000`
4. **Resume PDF**: Must be at `backend/data/resume.pdf` for attachments
5. **SMTP Ping**: Set `ENABLE_SMTP_PING="true"` only after testing (can get IP blocked)

---

## 🆘 Need Help?

- Groq: https://console.groq.com/docs
- Twilio: https://www.twilio.com/docs/whatsapp
- Gmail API: https://developers.google.com/gmail/api
- Supabase: https://supabase.com/docs
