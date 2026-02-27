# Fix Gmail OAuth Error: redirect_uri_mismatch

## The Problem

Your current credentials file is configured as a **Web Application**, but LazyIntern needs **Desktop Application** credentials for the OAuth flow.

## Solution: Download Desktop Application Credentials

### Step 1: Go to Google Cloud Console

1. Open: https://console.cloud.google.com/apis/credentials
2. Make sure you're in the correct project: **mailmind-471211**

### Step 2: Create Desktop Application Credentials

1. Click **"+ CREATE CREDENTIALS"** at the top
2. Select **"OAuth client ID"**
3. For "Application type", select **"Desktop app"**
4. Give it a name like: **"LazyIntern Desktop"**
5. Click **"CREATE"**

### Step 3: Download the Credentials

1. After creation, a dialog will show your Client ID and Secret
2. Click **"DOWNLOAD JSON"**
3. Save the downloaded file to your `secrets/` folder
4. Rename it to: **`gmail_oauth_client.json`**

### Step 4: Update Your .env File

Update the path in your `.env` file:

```env
# Change this line:
GMAIL_OAUTH_CLIENT_PATH="secrets/client_secret_491999044903-b38fuutfmg31n2kllhou9fpaiofe0tuv.apps.googleusercontent.com.json"

# To this:
GMAIL_OAUTH_CLIENT_PATH="secrets/gmail_oauth_client.json"
```

### Step 5: Run Token Generator Again

```bash
python generate_gmail_token.py
```

This time it should work! ✅

---

## Alternative: Fix Existing Web Credentials

If you want to keep using web credentials, you need to add the correct redirect URIs:

### Step 1: Edit Your OAuth Client

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your existing OAuth client ID
3. Under **"Authorized redirect URIs"**, add these URIs:
   - `http://localhost:8080/`
   - `http://localhost:8090/`
   - `http://localhost:8000/`
   - `http://localhost/`
   - `urn:ietf:wg:oauth:2.0:oob`

### Step 2: Save Changes

Click **"SAVE"** at the bottom

### Step 3: Wait 5 Minutes

Google takes a few minutes to propagate the changes.

### Step 4: Try Again

```bash
python generate_gmail_token.py
```

---

## Why This Happens

- **Web Application**: Used for web servers, requires specific redirect URIs
- **Desktop Application**: Used for local scripts, uses dynamic localhost ports
- The `InstalledAppFlow` in the script expects Desktop Application credentials

## Recommended Approach

✅ **Create new Desktop Application credentials** - This is cleaner and designed for this use case.

❌ **Modifying web credentials** - Works but not the intended use case.

---

## After Fixing

Once you have the correct credentials:
1. ✅ Run `python generate_gmail_token.py`
2. ✅ Browser opens and you authorize
3. ✅ Token saved to `secrets/gmail_token.json`
4. ✅ LazyIntern can send emails!

Need help? Check the error message and make sure:
- Gmail API is enabled
- OAuth consent screen is configured
- Your email is added as a test user (if app is in testing mode)
