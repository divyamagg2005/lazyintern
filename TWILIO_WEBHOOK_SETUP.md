# Twilio Webhook Setup Guide

## Overview

The Twilio webhook handles SMS replies for email draft approvals. When you receive an approval SMS, you can reply with YES or NO to approve or reject the draft.

## Features

✅ **Short Codes**: Each draft gets a 6-character code (e.g., D604CD) for easy replies
✅ **Immediate Email Sending**: Approved drafts trigger Gmail to send emails immediately
✅ **Quarantine on Rejection**: Rejected drafts are moved to quarantine for re-evaluation
✅ **Fallback Matching**: If no code provided, matches most recent pending draft
✅ **UUID Support**: Backward compatible with full UUID format

## SMS Format

### Outgoing (Approval Request):
```
LazyIntern (75%)
AI ML Intern at BlitzenX
samratk@blitzenx.com
Reply: YES D604CD
or NO D604CD
```

### Incoming (Your Reply):
```
YES D604CD
```
or
```
NO D604CD
```

You can also reply with just `YES` or `NO` (without the code) and it will match the most recent pending draft.

## Webhook Endpoint

**URL**: `/twilio/reply`

**Full URL**: `{PUBLIC_BASE_URL}/twilio/reply`

Example: `https://brennan-nongeneralized-hunter.ngrok-free.dev/twilio/reply`

## Twilio Console Configuration

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to: **Phone Numbers** → **Manage** → **Active Numbers**
3. Click on your Twilio phone number
4. Scroll to **Messaging Configuration**
5. Under "A message comes in":
   - Set to: **Webhook**
   - URL: `{YOUR_PUBLIC_BASE_URL}/twilio/reply`
   - HTTP Method: **POST**
6. Click **Save**

## How It Works

### YES Response Flow:
1. User replies: `YES D604CD`
2. Webhook receives SMS and parses short code
3. Finds matching draft in database
4. Updates draft status to `approved`
5. **Sends email immediately via Gmail API**
6. Schedules follow-up for day 5
7. Replies: `Email sent to samratk@blitzenx.com at BlitzenX`

### NO Response Flow:
1. User replies: `NO D604CD`
2. Webhook receives SMS and parses short code
3. Finds matching draft in database
4. Updates draft status to `rejected`
5. Moves lead to quarantine (re-evaluation in 14 days)
6. Replies: `Skipped BlitzenX. Moved to quarantine.`

## Short Code Generation

Short codes are generated deterministically from draft IDs using MD5 hash:
```python
import hashlib
short_code = hashlib.md5(draft_id.encode()).hexdigest()[:6].upper()
```

This means:
- Same draft ID always generates same short code
- No database storage needed
- Can be computed on-the-fly

## Testing

### 1. Check Pending Drafts:
```bash
cd backend
python test_twilio_webhook.py
```

This will show you:
- Draft ID
- Short code
- Email address
- Test commands

### 2. Test Locally (with ngrok):
```bash
# Start the API server
uvicorn api.app:app --reload --port 8000

# In another terminal, start ngrok
ngrok http 8000

# Update PUBLIC_BASE_URL in .env with ngrok URL
PUBLIC_BASE_URL="https://your-ngrok-url.ngrok-free.app"

# Send test SMS to your Twilio number
# Or use curl to simulate:
curl -X POST http://localhost:8000/twilio/reply \
  -d 'Body=YES D604CD' \
  -d 'From=+1234567890'
```

### 3. Test in Production:
1. Ensure API server is running
2. Ensure ngrok is running (or use permanent domain)
3. Configure Twilio webhook URL
4. Run pipeline to generate drafts
5. Reply to approval SMS with `YES {code}` or `NO {code}`

## Troubleshooting

### "No pending draft found"
- Check if there are any drafts with status='generated'
- Run: `python -c "from core.supabase_db import db; print(db.client.table('email_drafts').select('*').eq('status', 'generated').execute().data)"`

### "Invalid Twilio signature"
- Ensure PUBLIC_BASE_URL in .env matches the actual webhook URL
- Ensure TWILIO_AUTH_TOKEN is correct
- Check ngrok is forwarding to correct port

### "Email send failed"
- Check Gmail OAuth token is valid
- Run: `python -c "from outreach.gmail_client import _load_credentials; _load_credentials()"`
- Check resume.pdf exists at `backend/data/resume.pdf`

### Short code not working
- Ensure you're using the exact code from the SMS (case-insensitive)
- Try replying with just `YES` or `NO` (will match most recent draft)
- Check logs: `tail -f logs/app.log`

## API Response Examples

### Success (YES):
```
Email sent to samratk@blitzenx.com at BlitzenX
```

### Success (NO):
```
Skipped BlitzenX. Moved to quarantine.
```

### Error (No draft found):
```
No pending draft found. Please include the code from the approval SMS.
```

### Error (Unrecognized):
```
Reply YES or NO (with the code from the approval SMS)
```

## Files Modified

1. **backend/approval/twilio_sender.py**
   - Added `_generate_short_code()` function
   - Updated SMS format to include short codes
   - Removed metadata storage (compute on-the-fly)

2. **backend/api/routes/twilio_webhook.py**
   - Complete rewrite of webhook handler
   - Added short code parsing and matching
   - Added immediate Gmail sending on approval
   - Added quarantine on rejection
   - Added fallback to most recent draft

3. **backend/test_twilio_webhook.py**
   - Test script to check pending drafts and get short codes

## Next Steps

1. ✅ Configure Twilio webhook URL in console
2. ✅ Test with a real SMS reply
3. ✅ Monitor logs for any errors
4. ✅ Verify emails are sent immediately on approval
5. ✅ Verify rejected drafts move to quarantine

## Security Notes

- Webhook validates Twilio signature to prevent spoofing
- Only processes drafts with status='generated'
- Requires valid TWILIO_AUTH_TOKEN and PUBLIC_BASE_URL
- Gmail OAuth token must be valid for email sending
