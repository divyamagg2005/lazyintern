# Gmail Pub/Sub Push Notifications Setup

This guide explains how to set up real-time Gmail push notifications using Google Cloud Pub/Sub.

## Overview

Instead of polling Gmail every few minutes, Pub/Sub sends instant notifications when new emails arrive. This enables:
- ✅ Zero-latency reply detection
- ✅ Immediate follow-up cancellation
- ✅ Real-time company history updates
- ✅ No wasted API quota on polling

## Prerequisites

1. Google Cloud Project with billing enabled
2. Gmail API enabled
3. Public HTTPS endpoint (ngrok, Render, Railway, etc.)
4. LazyIntern backend running

## Step 1: Create Pub/Sub Topic

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create Pub/Sub topic
gcloud pubsub topics create gmail-push

# Grant Gmail permission to publish to this topic
gcloud pubsub topics add-iam-policy-binding gmail-push \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## Step 2: Create Pub/Sub Subscription

```bash
# Create push subscription pointing to your backend
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-push \
  --push-endpoint=https://YOUR_DOMAIN/gmail/push \
  --ack-deadline=30
```

Replace `YOUR_DOMAIN` with your public endpoint (e.g., `lazyintern.example.com` or ngrok URL).

## Step 3: Update Backend Configuration

Add to your `.env` file:

```env
# Google Cloud Project ID
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Public base URL for webhooks
PUBLIC_BASE_URL=https://your-domain.com
```

## Step 4: Start Gmail Watch

Once your backend is running with a public HTTPS endpoint:

```bash
# Call the setup endpoint
curl -X GET https://YOUR_DOMAIN/gmail/watch/setup
```

Or visit in browser: `https://YOUR_DOMAIN/gmail/watch/setup`

**Response**:
```json
{
  "status": "success",
  "response": {
    "historyId": "123456",
    "expiration": "1234567890000"
  }
}
```

## Step 5: Verify It Works

1. Send a test email to yourself from another account
2. Reply to one of your LazyIntern outreach emails
3. Check backend logs for:
   ```
   Gmail push notification received: your@email.com, historyId: 123456
   Reply classified as positive from recruiter@company.com
   Processed reply from recruiter@company.com: positive
   ```

## How It Works

### 1. Gmail Detects New Email
When someone replies to your outreach email, Gmail immediately notifies Pub/Sub.

### 2. Pub/Sub Pushes to Backend
Pub/Sub sends HTTP POST to `https://YOUR_DOMAIN/gmail/push` with:
```json
{
  "message": {
    "data": "base64_encoded_notification",
    "messageId": "123456",
    "publishTime": "2025-01-01T12:00:00Z"
  }
}
```

### 3. Backend Processes Reply
- Decodes Pub/Sub message
- Fetches new emails from Gmail API
- Extracts email body
- Classifies as positive/negative/neutral
- Updates company history in Supabase
- Cancels follow-up if positive
- Marks email as read

### 4. Follow-up Cancelled
If reply is positive:
```sql
UPDATE followup_queue 
SET sent = true 
WHERE lead_id = '...' AND sent = false;
```

## Watch Expiration

Gmail watch expires after 7 days. You need to renew it:

### Option 1: Manual Renewal
Call `/gmail/watch/setup` every 7 days.

### Option 2: Automatic Renewal (Recommended)
Add to your scheduler cycle:

```python
# In scheduler/cycle_manager.py
from datetime import timedelta

def renew_gmail_watch_if_needed():
    # Check last renewal time
    last_renewal = db.get_config("gmail_watch_last_renewal")
    if not last_renewal or (utcnow() - last_renewal) > timedelta(days=6):
        # Renew watch
        # ... call Gmail API watch()
        db.set_config("gmail_watch_last_renewal", utcnow())
```

## Troubleshooting

### Push notifications not arriving

1. **Check Pub/Sub subscription**:
   ```bash
   gcloud pubsub subscriptions describe gmail-push-sub
   ```

2. **Verify endpoint is public**:
   ```bash
   curl -X POST https://YOUR_DOMAIN/gmail/push \
     -H "Content-Type: application/json" \
     -d '{"message":{"data":"test"}}'
   ```

3. **Check Gmail watch status**:
   ```bash
   # In Python
   service.users().getProfile(userId='me').execute()
   ```

### Pub/Sub authentication errors

Ensure the Gmail service account has publisher role:
```bash
gcloud pubsub topics get-iam-policy gmail-push
```

Should show:
```yaml
bindings:
- members:
  - serviceAccount:gmail-api-push@system.gserviceaccount.com
  role: roles/pubsub.publisher
```

### Endpoint returns 404

Make sure:
1. Backend is running
2. `gmail_webhook` router is imported in `api/app.py`
3. Route is `/gmail/push` (not `/api/gmail/push`)

## Development with ngrok

For local development:

```bash
# Start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)

# Update Pub/Sub subscription
gcloud pubsub subscriptions update gmail-push-sub \
  --push-endpoint=https://abc123.ngrok.io/gmail/push

# Setup Gmail watch
curl -X GET https://abc123.ngrok.io/gmail/watch/setup
```

## Cost

- **Pub/Sub**: First 10GB free per month, then $0.40 per GB
- **Gmail API**: 1 billion quota units/day (free)
- **Typical usage**: ~1-5 MB/month for 100 replies = FREE

## Security

Pub/Sub messages are sent over HTTPS and include:
- Message ID for deduplication
- Publish timestamp
- Subscription verification

For additional security, you can verify the JWT token in the `Authorization` header.

## Stopping Push Notifications

To stop receiving notifications:

```bash
curl -X POST https://YOUR_DOMAIN/gmail/watch/stop
```

Or:
```bash
gcloud pubsub subscriptions delete gmail-push-sub
```

## Alternative: Polling (Current Implementation)

If you can't set up Pub/Sub, the system falls back to polling:

```python
# In scheduler/cycle_manager.py
from db.feedback.gmail_watcher import list_recent_messages

def check_for_replies():
    messages = list_recent_messages(max_results=10)
    # Process messages...
```

**Polling limitations**:
- 5-15 minute delay
- Uses more API quota
- Less efficient

**Pub/Sub advantages**:
- Instant notifications (< 1 second)
- Zero polling overhead
- Scales better
