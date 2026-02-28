# 🚀 START HERE - Gmail Setup & Send 16 Emails

## You're Almost Done! (10 minutes remaining)

Your LazyIntern pipeline is 95% complete. Just need to setup Gmail API to send those 16 emails.

---

## 📋 What You Have

✅ 16 leads discovered
✅ 16 AI-generated email drafts
✅ SMS approval system working
✅ Twilio webhook configured
✅ Everything ready to go

---

## 🎯 What You Need

Just Gmail API credentials to send emails.

---

## 🚀 Quick Start (Choose One)

### Option 1: Automated Wizard (Recommended)

```bash
cd backend
python setup_gmail_complete.py
```

This wizard will:
1. Check if you have OAuth credentials
2. Guide you to get them if needed
3. Authorize Gmail access (opens browser)
4. Test email sending
5. Send all 16 emails

**Time**: 10 minutes (mostly waiting for Google Cloud setup)

---

### Option 2: Manual Steps

#### Step 1: Get OAuth Credentials (5 min)

1. Go to https://console.cloud.google.com/
2. Create new project: "LazyIntern"
3. Enable "Gmail API"
4. Create OAuth 2.0 credentials:
   - Application type: **Desktop app**
   - Name: "LazyIntern Desktop"
5. Download JSON file
6. Save to: `backend\secrets\client_secret_*.json`

#### Step 2: Authorize (2 min)

```bash
cd backend
python authorize_gmail.py
```

- Browser opens
- Sign in to Gmail
- Click "Advanced" → "Go to LazyIntern (unsafe)"
- Click "Allow"
- Done!

#### Step 3: Test (1 min)

```bash
python test_gmail_send.py
```

Check your inbox for test email.

#### Step 4: Send All 16 Emails (2 min)

```bash
python send_all_drafts.py
```

Type "yes" to confirm.

---

## 📖 Detailed Guides

- **Complete Guide**: `GMAIL_API_SETUP_GUIDE.md`
- **Checklist**: `GMAIL_SETUP_CHECKLIST.md`
- **Quick Start**: `SETUP_GMAIL_NOW.md`
- **Full Summary**: `FINAL_SETUP_SUMMARY.md`

---

## 🎊 After Setup

You'll have a fully automated system:

1. **Discover** internships (43 sources, India-focused)
2. **Extract** emails (regex + Hunter.io)
3. **Score** leads (AI-powered)
4. **Generate** drafts (Groq AI)
5. **Approve** via SMS (YES/NO with short codes)
6. **Send** emails automatically (Gmail)
7. **Follow-up** automatically (day 5)

---

## ⚡ Let's Do This!

Run the wizard now:

```bash
cd backend
python setup_gmail_complete.py
```

Or follow manual steps above.

---

## 🆘 Need Help?

The wizard will guide you through everything. If you get stuck:

1. Check `GMAIL_API_SETUP_GUIDE.md` for detailed instructions
2. Make sure you're signed in to Google Cloud Console
3. Make sure Gmail API is enabled
4. Make sure you added your email as a test user

---

## 🏁 You're So Close!

10 minutes from now, you'll have:
- ✅ Gmail API working
- ✅ 16 emails sent
- ✅ Fully operational pipeline
- ✅ Automated internship outreach machine

Let's finish this! 🚀

```bash
cd backend
python setup_gmail_complete.py
```
