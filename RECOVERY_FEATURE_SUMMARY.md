# Recovery Feature Summary

## Overview

The LazyIntern pipeline now includes an automatic recovery mechanism that ensures continuity when the program is restarted after being terminated. This feature processes any pending approved email drafts before starting new discovery.

## How It Works

### Recovery Phase (Phase 0)

When you run `./START_HERE.ps1` in mode 1 (Full Stack 24/7), the system now:

1. **Checks for Pending Drafts**: Before starting scraping, the system queries the database for any email drafts with status `approved` or `auto_approved`

2. **Processes Pending Emails**: If pending drafts are found, the system:
   - Sends them one by one (respecting email spacing of 45-55 minutes)
   - Respects daily email limits (default 15 emails/day)
   - Shows progress in console: `✓ Sent pending email X [Y/Z]`
   - Stops if daily limit is reached or spacing constraint is active

3. **Continues to Scraping**: After processing pending drafts (or if none found), the system proceeds with normal operations:
   - Process retry queue
   - Process follow-ups
   - Process existing discovered internships
   - Start new discovery/scraping
   - Process newly discovered internships

## Console Output Example

```
======================================================================
RECOVERY PHASE: Checking for pending approved drafts...
======================================================================
Found 5 pending approved draft(s) from previous run
Processing pending drafts before starting new discovery...
✓ Sent pending email 1 [1/15]
✓ Sent pending email 2 [2/15]
✓ Sent pending email 3 [3/15]
Spacing constraint active - will resume in next cycle
✓ Recovery complete: 3 pending email(s) sent
======================================================================
```

## Benefits

1. **Continuity**: No emails are lost if you terminate the program mid-cycle
2. **Automatic**: No manual intervention needed - just restart the program
3. **Respects Limits**: Still follows daily email limits and spacing rules
4. **Transparent**: Clear console output shows what's happening

## Technical Details

### Location
- File: `backend/scheduler/cycle_manager.py`
- Function: `run_cycle()`
- Phase: 0 (before all other phases)

### Database Query
```python
pending_drafts = (
    db.client.table("email_drafts")
    .select("id", count="exact")
    .in_("status", ["approved", "auto_approved"])
    .execute()
)
```

### Email Sending
- Uses existing `process_email_queue()` function
- Respects 45-55 minute spacing between emails
- Respects daily email limit (default 15/day)
- Sends one email per iteration until:
  - All pending drafts are sent, OR
  - Daily limit is reached, OR
  - Spacing constraint prevents sending

## Integration with Immediate Send Fix

This recovery feature works seamlessly with the immediate send fix:

1. **Immediate Approval**: Drafts are created with status='approved' immediately (no 2-hour delay)
2. **Recovery**: If program terminates before emails are sent, recovery phase picks them up on restart
3. **Notification SMS**: User gets notified when emails are queued (not when sent during recovery)

## Use Cases

### Scenario 1: Program Terminated During Discovery
- System found 11 leads and created 11 approved drafts
- Only 1 email was sent before termination
- On restart: Recovery phase sends remaining 10 emails (respecting spacing/limits)

### Scenario 2: Daily Limit Reached
- System has 5 pending drafts
- Daily limit already at 14/15
- On restart: Recovery phase sends 1 email, then stops (limit reached)
- Remaining 4 drafts will be sent in next day's cycle

### Scenario 3: Spacing Constraint Active
- System has 3 pending drafts
- Last email was sent 20 minutes ago
- On restart: Recovery phase waits (spacing constraint)
- Will retry in next cycle (2 hours later)

## Testing

To test the recovery feature:

1. Start the program: `./START_HERE.ps1` → Option 1
2. Wait for some drafts to be created (status='approved')
3. Terminate the program (Ctrl+C)
4. Restart: `./START_HERE.ps1` → Option 1
5. Observe recovery phase in console output

## Related Features

- **Immediate Send Fix**: Drafts are approved immediately (no 2-hour delay)
- **Notification SMS**: User gets SMS when emails are queued
- **Error Notifications**: User gets SMS when API errors occur
- **Email Spacing**: 45-55 minute gaps between emails
- **Daily Limits**: Maximum 15 emails per day (configurable)

## Configuration

No additional configuration needed - the recovery feature is automatic and always active.

## Troubleshooting

### Recovery Phase Shows 0 Pending Drafts
- This is normal if all drafts were already sent
- Or if no drafts were created in previous run

### Recovery Phase Sends 0 Emails
- Check if daily limit is already reached
- Check if spacing constraint is active (last email sent < 45 min ago)
- Check console output for specific reason

### Pending Drafts Not Being Sent
- Verify drafts have status='approved' or 'auto_approved' in database
- Check if email_sent count is below daily_limit in daily_usage table
- Verify Gmail credentials are configured correctly

## Future Enhancements

Potential improvements for the recovery feature:

1. **Priority Queue**: Send higher-scored drafts first
2. **Batch Recovery**: Send multiple emails in parallel (if spacing allows)
3. **Recovery Report**: Email summary of recovered drafts to user
4. **Configurable Recovery**: Option to skip recovery phase if desired
