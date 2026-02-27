# Quick Fix for OAuth Error

You got the error: **"Error 400: redirect_uri_mismatch"**

## Fastest Solution (5 minutes)

### Option 1: Add Redirect URI to Existing Credentials ⚡

1. **Open Google Cloud Console:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Project: **mailmind-471211**

2. **Click on your OAuth 2.0 Client ID:**
   - Look for: `491999044903-b38fuutfmg31n2kllhou9fpaiofe0tuv.apps.googleusercontent.com`
   - Click on it to edit

3. **Add These Redirect URIs:**
   Under "Authorized redirect URIs", click **"+ ADD URI"** and add:
   ```
   http://localhost:8080/
   http://localhost:8090/
   http://localhost/
   ```

4. **Click SAVE** at the bottom

5. **Wait 5 minutes** for Google to update

6. **Run this command:**
   ```bash
   python generate_gmail_token.py
   ```

---

### Option 2: Create Desktop App Credentials (Recommended) ✅

1. **Go to:** https://console.cloud.google.com/apis/credentials

2. **Click:** "+ CREATE CREDENTIALS" → "OAuth client ID"

3. **Select:** Application type = **"Desktop app"**

4. **Name it:** "LazyIntern Desktop"

5. **Click CREATE**

6. **Download JSON** and save as: `secrets/gmail_oauth_client.json`

7. **Update .env file:**
   ```env
   GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
   ```

8. **Run:**
   ```bash
   python generate_gmail_token.py
   ```

---

## Which Option Should I Choose?

| Option | Pros | Cons |
|--------|------|------|
| **Option 1** (Add URIs) | Quick, uses existing credentials | Not the intended use case |
| **Option 2** (Desktop App) | ✅ Proper solution, cleaner | Need to download new file |

**Recommendation:** Go with **Option 2** - it's the correct way and takes the same amount of time.

---

## After Fixing

Once you complete either option:
1. Run: `python generate_gmail_token.py`
2. Browser opens → Log in → Click "Allow"
3. Token saved to `secrets/gmail_token.json`
4. Done! ✅

---

## Still Having Issues?

Make sure:
- ✅ Gmail API is enabled in your project
- ✅ OAuth consent screen is configured
- ✅ Your email (divyamagg2005@gmail.com) is added as a test user
- ✅ You're using the correct Google account

Check these at: https://console.cloud.google.com/apis/dashboard?project=mailmind-471211
