# Auto-Approval System Guide

## 🎯 Overview

The auto-approval system automatically approves and sends high-quality email drafts after a 2-hour timeout, with built-in delays to avoid spam detection.

---

## ⚙️ Configuration

### Current Settings

```python
AUTO_APPROVE_THRESHOLD = 90          # Only drafts with score >= 90%
TIMEOUT_HOURS = 2                    # Wait 2 hours for manual approval
AUTO_APPROVE_MIN_DELAY_MINUTES = 10  # Min delay after auto-approval
AUTO_APPROVE_MAX_DELAY_MINUTES = 30  # Max delay after auto-approval
EMAIL_SPACING_MINUTES = 45-55        # Random spacing between emails
```

### What Gets Auto-Approved?

✅ **Auto-approved:**
- Draft with `full_score >= 90`
- SMS sent 2+ hours ago
- No manual approval received

❌ **NOT auto-approved:**
- Draft with `full_score < 90` (requires manual approval)
- SMS sent < 2 hours ago (still waiting)
- Already manually approved/rejected

---

## 📊 Complete Flow

### Timeline Example

```
00:00 - Draft Created
        ├─ status: 'generated'
        ├─ SMS sent to approver
        └─ approval_sent_at: 2026-03-01T00:00:00Z

        ⏳ Waiting for manual approval...

02:00 - Auto-Approver Runs (2h timeout passed)
        ├─ Checks: full_score >= 90? ✓
        ├─ status: 'auto_approved'
        ├─ Random delay: 23 minutes (10-30 min range)
        └─ approved_at: 2026-03-01T02:23:00Z

        ⏳ Waiting for delay to pass...

02:23 - Email Queue Checks
        ├─ approved_at <= now? ✓
        ├─ Last email sent 50 min ago? ✓
        ├─ Daily limit not reached? ✓
        └─ ✉️  Email sent!

02:24 - Email Sent
        ├─ status: 'sent'
        ├─ sent_at: 2026-03-01T02:24:00Z
        └─ Follow-up scheduled for day 5

        ⏳ Next email can send after 45-55 min...

03:15 - Next Email Ready
        └─ Earliest next send time (45 min spacing)
```

---

## 🔄 System Components

### 1. Auto-Approver (`auto_approver.py`)

**Runs:** Every cycle (every 2 hours)

**Logic:**
```python
for draft in pending_drafts:
    if approval_sent_at < (now - 2 hours):
        if full_score >= 90:
            # Auto-approve with random delay
            delay = random(10, 30) minutes
            approved_at = now + delay
            status = 'auto_approved'
```

**Logs:**
```
Auto-approved draft abc123 (score: 92) - will send after 23 min delay
```

### 2. Email Queue (`queue_manager.py`)

**Runs:** Every cycle (every 2 hours)

**Logic:**
```python
for draft in approved_drafts:
    # Check if delay has passed
    if approved_at <= now:
        # Check spacing from last email
        if time_since_last >= 45 minutes:
            # Check daily limit
            if emails_sent < 15:
                send_email(draft)
                break  # Only one per cycle
```

**Logs:**
```
Email sent (auto approval) to recruiter@company.com [5/15]
```

### 3. Delay Mechanisms

**Three layers of delays:**

1. **2-hour timeout** - Wait for manual approval
2. **10-30 min random delay** - After auto-approval
3. **45-55 min spacing** - Between consecutive emails

**Total delay range:** 2h 55min to 3h 25min from SMS sent to email sent

---

## 🛡️ Spam Prevention

### Why Multiple Delays?

**Problem:** Sending emails too quickly looks like spam
- Gmail/Outlook flag automated patterns
- Consistent timing = bot behavior
- Burst sending = spam signal

**Solution:** Randomized delays at multiple stages
- ✅ Variable approval time (2h + 10-30 min)
- ✅ Variable spacing (45-55 min)
- ✅ One email per cycle (not bursts)
- ✅ Daily limit (15 emails max)

### Delay Breakdown

```
Manual Approval:
├─ SMS sent → Email sent
└─ Delay: User-controlled (instant to hours)

Auto-Approval:
├─ SMS sent → Auto-approved
│  └─ Delay: 2 hours (fixed)
├─ Auto-approved → Ready to send
│  └─ Delay: 10-30 minutes (random)
└─ Ready to send → Email sent
   └─ Delay: 0-55 minutes (depends on last email)

Total: 2h 10min to 3h 25min (highly variable)
```

---

## 📈 Monitoring

### Check Auto-Approval Status

```sql
-- Drafts pending auto-approval (waiting for 2h timeout)
SELECT id, approval_sent_at, 
       NOW() - approval_sent_at as time_waiting
FROM email_drafts 
WHERE status = 'generated'
  AND approval_sent_at < NOW() - INTERVAL '2 hours';

-- Auto-approved drafts waiting to send
SELECT id, approved_at,
       approved_at - NOW() as time_until_send
FROM email_drafts 
WHERE status = 'auto_approved'
ORDER BY approved_at;

-- Recently sent auto-approved emails
SELECT id, sent_at, approved_at,
       sent_at - approved_at as actual_delay
FROM email_drafts 
WHERE status = 'sent'
  AND approved_at IS NOT NULL
ORDER BY sent_at DESC
LIMIT 10;
```

### Check Email Spacing

```sql
-- Verify 45+ minute spacing between emails
SELECT 
    id,
    sent_at,
    LAG(sent_at) OVER (ORDER BY sent_at) as prev_sent_at,
    EXTRACT(EPOCH FROM (sent_at - LAG(sent_at) OVER (ORDER BY sent_at)))/60 as gap_minutes
FROM email_drafts
WHERE status = 'sent'
ORDER BY sent_at DESC
LIMIT 10;
```

### Log Messages to Watch

```bash
# Auto-approval
Auto-approved draft abc123 (score: 92) - will send after 23 min delay

# Delay not passed yet
Skipping draft abc123 - delay not passed yet (approved_at: 2026-03-01T02:23:00Z)

# Email sent
Email sent (auto approval) to recruiter@company.com [5/15]

# Manual approval (for comparison)
Email sent (manual approval) to recruiter@company.com [6/15]
```

---

## 🧪 Testing

### Run Test Suite

```bash
cd backend
python test_auto_approval.py
```

**Expected output:**
```
======================================================================
AUTO-APPROVAL SYSTEM VERIFICATION
======================================================================

AUTO-APPROVAL CONFIGURATION TEST
======================================================================

✓ Auto-approval threshold: 90%
✓ Timeout before auto-approval: 2 hours
✓ Additional delay after auto-approval: 10-30 minutes
✓ Email spacing: 45-55 minutes between sends

✅ Configuration looks good!

...

✅ ALL AUTO-APPROVAL TESTS COMPLETE
```

### Manual Testing

**Test 1: Create a high-score draft**
```python
# In Python shell
from core.supabase_db import db, utcnow
from datetime import timedelta

# Create a test draft (score >= 90)
draft = db.insert_email_draft({
    "lead_id": "your-lead-id",
    "subject": "Test",
    "body": "Test",
    "status": "generated"
})

# Set approval_sent_at to 2 hours ago
past = utcnow() - timedelta(hours=2, minutes=5)
db.client.table("email_drafts").update({
    "approval_sent_at": past.isoformat()
}).eq("id", draft["id"]).execute()

# Wait for next cycle (or run manually)
from approval.auto_approver import run_auto_approver
run_auto_approver()

# Check if auto-approved
result = db.get_email_draft(draft["id"])
print(f"Status: {result['status']}")  # Should be 'auto_approved'
print(f"Approved at: {result['approved_at']}")  # Should be future time
```

**Test 2: Verify delay enforcement**
```python
# Check if email sends immediately or waits for delay
from outreach.queue_manager import process_email_queue

# This should skip the draft if approved_at is in the future
process_email_queue()

# Check logs for "Skipping draft - delay not passed yet"
```

---

## ⚙️ Configuration Options

### Adjust Auto-Approval Threshold

```python
# In backend/approval/auto_approver.py
AUTO_APPROVE_THRESHOLD = 85  # Lower = more auto-approvals
AUTO_APPROVE_THRESHOLD = 95  # Higher = fewer auto-approvals
```

**Recommended:** 90 (only very high-quality leads)

### Adjust Timeout Duration

```python
# In backend/approval/auto_approver.py
TIMEOUT_HOURS = 1   # Faster auto-approval (less time to review)
TIMEOUT_HOURS = 4   # Slower auto-approval (more time to review)
```

**Recommended:** 2 hours (balance between speed and review time)

### Adjust Delay Range

```python
# In backend/approval/auto_approver.py
AUTO_APPROVE_MIN_DELAY_MINUTES = 5   # Shorter delays
AUTO_APPROVE_MAX_DELAY_MINUTES = 15  # Shorter delays

AUTO_APPROVE_MIN_DELAY_MINUTES = 20  # Longer delays
AUTO_APPROVE_MAX_DELAY_MINUTES = 60  # Longer delays
```

**Recommended:** 10-30 minutes (good balance for spam prevention)

### Adjust Email Spacing

```python
# In backend/outreach/queue_manager.py
min_gap = timedelta(minutes=30 + random.randint(0, 10))  # Faster (30-40 min)
min_gap = timedelta(minutes=60 + random.randint(0, 20))  # Slower (60-80 min)
```

**Recommended:** 45-55 minutes (safe for most email providers)

---

## 🚨 Troubleshooting

### Issue: Drafts not auto-approving

**Check:**
1. Is `full_score >= 90`?
   ```sql
   SELECT id, full_score FROM internships WHERE id = 'your-internship-id';
   ```

2. Has 2 hours passed since SMS sent?
   ```sql
   SELECT id, approval_sent_at, NOW() - approval_sent_at as age
   FROM email_drafts WHERE id = 'your-draft-id';
   ```

3. Is auto-approver running?
   ```bash
   # Check scheduler logs for:
   # "Auto-approved draft..."
   ```

### Issue: Auto-approved emails not sending

**Check:**
1. Has `approved_at` timestamp passed?
   ```sql
   SELECT id, approved_at, NOW() > approved_at as ready
   FROM email_drafts WHERE status = 'auto_approved';
   ```

2. Is email spacing enforced?
   ```bash
   # Check logs for:
   # "Not enough time has passed, skip this cycle"
   ```

3. Is daily limit reached?
   ```sql
   SELECT emails_sent, daily_limit 
   FROM daily_usage_stats 
   WHERE date = CURRENT_DATE;
   ```

### Issue: Emails sending too fast

**Check:**
1. Verify spacing logic in `queue_manager.py`
2. Check `min_gap` calculation
3. Review sent_at timestamps:
   ```sql
   SELECT id, sent_at, 
          sent_at - LAG(sent_at) OVER (ORDER BY sent_at) as gap
   FROM email_drafts WHERE status = 'sent'
   ORDER BY sent_at DESC LIMIT 5;
   ```

---

## 📊 Statistics

### Auto-Approval Rate

```sql
-- Calculate auto-approval rate
SELECT 
    COUNT(*) FILTER (WHERE status = 'auto_approved' OR 
                     (status = 'sent' AND approved_at IS NOT NULL)) as auto_approved,
    COUNT(*) FILTER (WHERE status = 'approved' OR 
                     (status = 'sent' AND approved_at IS NULL)) as manual_approved,
    COUNT(*) as total
FROM email_drafts
WHERE status IN ('approved', 'auto_approved', 'sent');
```

### Average Delays

```sql
-- Average time from SMS to auto-approval
SELECT AVG(EXTRACT(EPOCH FROM (approved_at - approval_sent_at))/3600) as avg_hours
FROM email_drafts
WHERE status IN ('auto_approved', 'sent')
  AND approved_at IS NOT NULL;

-- Average time from approval to send
SELECT AVG(EXTRACT(EPOCH FROM (sent_at - approved_at))/60) as avg_minutes
FROM email_drafts
WHERE status = 'sent'
  AND approved_at IS NOT NULL;
```

---

## ✅ Best Practices

1. **Monitor auto-approval rate** - Should be 20-40% of total approvals
2. **Check email spacing** - Should always be >= 45 minutes
3. **Review spam complaints** - If any, increase delays
4. **Adjust threshold** - Based on reply rates for auto-approved emails
5. **Test changes** - Always test in staging before production

---

## 🔐 Security Notes

- Auto-approval only for high-quality leads (score >= 90)
- Multiple delay layers prevent bot-like behavior
- Daily limits prevent abuse
- Manual approval always available for review
- Logs track all auto-approvals for audit

---

## 📞 Support

If auto-approval isn't working:
1. Run `python backend/test_auto_approval.py`
2. Check scheduler logs
3. Query database for pending drafts
4. Verify configuration values
5. Review this guide's troubleshooting section
