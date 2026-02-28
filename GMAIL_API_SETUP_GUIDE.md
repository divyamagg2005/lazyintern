# Gmail API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it: "LazyIntern Email Sender"
4. Click "Create"

## Step 2: Enable Gmail API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: "LazyIntern"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip (click "Save and Continue")
   - Test users: Add your Gmail address
   - Click "Save and Continue"

4. Back to "Create OAuth client ID":
   - Application type: **Desktop app**
   - Name: "LazyIntern Desktop Client"
   - Click "Create"

5. Download the JSON file:
   - Click "Download JSON" button
   - Save the file (it will be named something like `client_secret_*.json`)

## Step 4: Place Credentials in Project

1. Create the secrets folder:
   ```bash
   mkdir backend\secrets
   ```

2. Copy the downloaded JSON file to:
   ```
   backend\secrets\client_secret_*.json
   ```
   (Keep the original filename)

3. Update `.env` file with the correct path:
   ```
   GMAIL_OAUTH_CLIENT_PATH="secrets/client_secret_YOUR_FILE_NAME.json"
   ```

## Step 5: Authorize Gmail Access

Run the authorization script:
```bash
cd backend
python authorize_gmail.py
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Show a warning "Google hasn't verified this app" - Click "Advanced" → "Go to LazyIntern (unsafe)"
4. Click "Allow" to grant Gmail send permissions
5. Save the token to `backend/secrets/gmail_token.json`

## Step 6: Test Gmail Sending

```bash
cd backend
python test_gmail_send.py
```

This will send a test email to verify everything works.

## Step 7: Send All 16 Pending Emails

```bash
cd backend
python send_all_drafts.py
```

This will send all 16 pending drafts with resume attachments.

---

## Troubleshooting

### "File not found" error
- Make sure the JSON file is in `backend/secrets/`
- Check the filename in `.env` matches the actual file

### "Access blocked" during authorization
- Make sure you added your email as a test user in OAuth consent screen
- Try using an incognito browser window

### "Invalid grant" error
- Delete `backend/secrets/gmail_token.json`
- Run authorization again

### "Resume not found" warning
- Place your resume PDF at: `backend/data/resume.pdf`
- Or emails will be sent without attachment

---

## Security Notes

- Keep `client_secret_*.json` and `gmail_token.json` private
- These files are already in `.gitignore`
- Token expires after 7 days of inactivity (will auto-refresh)
- You can revoke access anytime in Google Account settings
