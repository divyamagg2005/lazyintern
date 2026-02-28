# Setup Gmail API - Quick Start

## 🚀 Fast Track (10 minutes)

### Option 1: Automated Wizard (Recommended)

```bash
cd backend
python setup_gmail_complete.py
```

This wizard will guide you through everything step-by-step.

---

### Option 2: Manual Steps

#### 1. Get OAuth Credentials (5 min)

1. Go to https://console.cloud.google.com/
2. Create project: "LazyIntern"
3. Enable "Gmail API"
4. Create OAuth 2.0 credentials (Desktop app)
5. Download JSON file
6. Place at: `backend\secrets\client_secret_*.json`

#### 2. Authorize (2 min)

```bash
cd backend
python authorize_gmail.py
```

Browser opens → Sign in → Allow permissions

#### 3. Test (1 min)

```bash
python test_gmail_send.py
```

Check your inbox for test email.

#### 4. Send All 16 Emails (2 min)

```bash
python send_all_drafts.py
```

Type "yes" to confirm and send.

---

## 📋 What You Need

- Gmail account
- Google Cloud Console access
- 10 minutes

---

## 🎯 After Setup

Your pipeline will be 100% operational:

✅ Discover internships (43 sources)
✅ Extract & validate emails
✅ Score & filter (India-focused)
✅ Generate AI drafts (Groq)
✅ Send SMS approvals (Twilio)
✅ **Send emails (Gmail)** ← You're setting this up now
✅ Schedule follow-ups (day 5)

---

## 🆘 Need Help?

See detailed guide: `GMAIL_API_SETUP_GUIDE.md`

Or run the wizard: `python setup_gmail_complete.py`

---

## ⚡ Quick Commands

```bash
# Setup wizard (recommended)
python setup_gmail_complete.py

# Or manual steps:
python authorize_gmail.py      # Step 1: Authorize
python test_gmail_send.py      # Step 2: Test
python send_all_drafts.py      # Step 3: Send all

# Check status
python verify_webhook_setup.py  # Shows full pipeline status
```

---

## 🔒 Security

- Credentials stored in `backend/secrets/` (gitignored)
- Token auto-refreshes (expires after 7 days inactive)
- Revoke access anytime in Google Account settings

---

## ✨ You're Almost There!

Just need to:
1. Get OAuth credentials from Google Cloud
2. Run authorization (opens browser once)
3. Send those 16 emails!

Let's do this! 🚀
