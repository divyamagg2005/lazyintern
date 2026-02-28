# Gmail API Setup - Quick Checklist

## Prerequisites
- [ ] Google account with Gmail
- [ ] Access to Google Cloud Console

---

## Setup Steps

### 1. Google Cloud Console Setup (5 minutes)

- [ ] Go to https://console.cloud.google.com/
- [ ] Create new project: "LazyIntern Email Sender"
- [ ] Enable Gmail API
- [ ] Configure OAuth consent screen:
  - [ ] User Type: External
  - [ ] App name: "LazyIntern"
  - [ ] Add your email as test user
- [ ] Create OAuth 2.0 credentials:
  - [ ] Application type: Desktop app
  - [ ] Download JSON file

### 2. Place Credentials (1 minute)

- [ ] Create folder: `backend\secrets`
- [ ] Copy downloaded JSON to: `backend\secrets\client_secret_*.json`
- [ ] Verify path in `.env`: `GMAIL_OAUTH_CLIENT_PATH="secrets/client_secret_*.json"`

### 3. Authorize Gmail (2 minutes)

```bash
cd backend
python authorize_gmail.py
```

- [ ] Browser opens automatically
- [ ] Sign in to Gmail
- [ ] Click "Advanced" → "Go to LazyIntern (unsafe)"
- [ ] Click "Allow"
- [ ] Token saved to `backend\secrets\gmail_token.json`

### 4. Test Email Sending (1 minute)

```bash
python test_gmail_send.py
```

- [ ] Test email sent successfully
- [ ] Check your Gmail inbox
- [ ] Verify email received

### 5. Send All 16 Drafts (2 minutes)

```bash
python send_all_drafts.py
```

- [ ] Review recipients list
- [ ] Type "yes" to confirm
- [ ] Wait for all emails to send
- [ ] Check Gmail "Sent" folder

---

## Optional: Add Resume Attachment

- [ ] Place your resume PDF at: `backend\data\resume.pdf`
- [ ] Emails will automatically include it as attachment

---

## Verification

After setup, verify:
- [ ] Token file exists: `backend\secrets\gmail_token.json`
- [ ] Test email received in your inbox
- [ ] All 16 emails sent successfully
- [ ] Emails appear in Gmail "Sent" folder

---

## Troubleshooting

### "File not found" error
→ Check `GMAIL_OAUTH_CLIENT_PATH` in `.env` matches actual filename

### "Access blocked" during authorization
→ Add your email as test user in OAuth consent screen

### "Invalid grant" error
→ Delete `gmail_token.json` and re-authorize

### Emails not sending
→ Check Gmail API is enabled in Google Cloud Console

---

## Security

✓ Credentials are in `.gitignore` (not committed to git)
✓ Token expires after 7 days of inactivity (auto-refreshes)
✓ You can revoke access anytime in Google Account settings

---

## Next Steps After Setup

1. ✅ Gmail API working
2. ✅ 16 emails sent
3. ✅ Follow-ups scheduled (day 5)
4. ✅ Pipeline fully operational

You can now:
- Run the pipeline to discover new internships
- Approve drafts via SMS (YES/NO with short codes)
- Emails send automatically on approval
- Monitor replies in Gmail
