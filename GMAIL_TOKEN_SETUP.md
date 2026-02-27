# Gmail Token Setup Guide

This guide will help you generate the Gmail OAuth token needed for LazyIntern to send emails.

## Prerequisites

✅ You already have:
- Gmail OAuth credentials file in `secrets/` folder
- `.env` file configured with correct paths

## Step 1: Install Required Packages

Make sure you have the Google Auth libraries installed:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or if you already installed `requirements.txt`:
```bash
pip install -r backend/requirements.txt
```

## Step 2: Run the Token Generator

Run the token generation script:

```bash
python generate_gmail_token.py
```

## What Happens Next

1. **Browser Opens**: A browser window will automatically open
2. **Login**: Log into your Gmail account (the one you want to send emails from)
3. **Grant Permissions**: Click "Allow" when asked to grant permissions
4. **Confirmation**: The script will confirm when the token is saved

## Expected Output

```
============================================================
Gmail OAuth Token Generator
============================================================
✓ Found credentials file: secrets/client_secret_...json

🔐 Starting OAuth flow...
A browser window will open. Please:
  1. Log into your Gmail account
  2. Click 'Allow' to grant permissions
  3. Wait for confirmation

✅ Token saved successfully to: secrets/gmail_token.json

✓ You can now use the Gmail API!
✓ This token will auto-refresh when needed.
✓ You don't need to run this script again unless you revoke access.
```

## Verify Token Was Created

Check that the token file exists:

```bash
# Windows
dir secrets\gmail_token.json

# Linux/Mac
ls -la secrets/gmail_token.json
```

## Troubleshooting

### "No credentials file found"
- Make sure your OAuth credentials file is in the `secrets/` folder
- The script will automatically find files named:
  - `gmail_oauth_client.json`
  - `credentials.json`
  - `client_secret_*.json`

### "Access blocked: This app's request is invalid"
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Make sure Gmail API is enabled
3. Check that OAuth consent screen is configured
4. Add your email as a test user if the app is in testing mode

### "The browser opened but nothing happened"
1. Make sure you're logged into the correct Gmail account
2. Try using an incognito/private window
3. Check if popup blockers are preventing the authorization

### "Token expired" or "Invalid token"
Just run the script again - it will generate a fresh token.

## Security Notes

⚠️ **Important**: 
- Never commit `gmail_token.json` to git (it's already in `.gitignore`)
- Keep your credentials file secure
- The token has access to send and read emails from your Gmail account

## What This Token Does

The token grants LazyIntern permission to:
- ✅ Send emails from your Gmail account
- ✅ Read emails (for reply detection)
- ✅ Modify labels (mark emails as read)

## Next Steps

Once the token is generated:
1. ✅ Token is saved to `secrets/gmail_token.json`
2. ✅ Your `.env` already points to the correct path
3. ✅ LazyIntern can now send emails via Gmail API
4. ✅ The token will auto-refresh when it expires

You're all set! 🚀
