# Auto-Approval Immediate Send Fix - Bugfix Design

## Overview

The lead processing pipeline has multiple critical failures preventing automated email outreach. The system found 11 leads but only sent 1 email due to a broken auto-approval mechanism that introduces a 2-hour delay plus 10-30 minute random delay before emails can be sent. Additionally, the SMS approval flow relies on Twilio's paid tier features (yes/no replies) which are unavailable, blocking the entire approval process. The fix will transition to a fully automated immediate-send pipeline that generates drafts and sends them directly without approval delays, while converting SMS to notification-only messages and adding error alerting.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when leads are inserted into the database but emails are not sent immediately due to approval delays
- **Property (P)**: The desired behavior - emails should be generated and sent immediately after lead insertion without approval delays
- **Preservation**: Existing lead scoring, email generation, and batch processing logic that must remain unchanged by the fix
- **send_approval_sms**: The function in `backend/approval/twilio_sender.py` that sends SMS messages requesting yes/no approval
- **run_auto_approver**: The function in `backend/approval/auto_approver.py` that auto-approves drafts after a 2-hour timeout
- **process_email_queue**: The function in `backend/outreach/queue_manager.py` that sends approved emails with 45-55 minute spacing
- **approval_sent_at**: Timestamp when approval SMS was sent, used to calculate 2-hour timeout
- **approved_at**: Timestamp when draft was approved (includes 10-30 minute delay for auto-approved drafts)

## Bug Details

### Fault Condition

The bug manifests when a lead is inserted into the leads table and an email draft is generated. The current system requires a 2-hour wait for auto-approval plus an additional 10-30 minute random delay before the email can be sent. This means emails are delayed by 2.5-3 hours minimum, and if the scheduler doesn't run at the right time, the delay can extend to 8+ hours. Additionally, the SMS approval mechanism fails because it requires Twilio paid tier features for yes/no replies.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LeadProcessingEvent
  OUTPUT: boolean
  
  RETURN input.lead_inserted = true
         AND input.draft_generated = true
         AND (input.approval_sent_at IS NOT NULL OR input.twilio_configured = false)
         AND input.email_sent = false
         AND (currentTime - input.draft_created_at) > 2 hours
END FUNCTION
```

### Examples

- **Example 1**: System finds 11 leads during an 8-hour run. First lead gets processed and email sent after 2+ hour delay. Remaining 10 leads wait in queue with status='generated', never progressing to auto-approved because the 2-hour timeout hasn't elapsed yet. Result: Only 1/11 emails sent.

- **Example 2**: Draft is generated at 10:00 AM, approval SMS sent at 10:00 AM. Auto-approver runs at 12:05 PM (2h 5min later), sets status='auto_approved' and approved_at=12:25 PM (adds 20 min delay). Email queue processes at 12:30 PM, but approved_at hasn't passed yet. Email finally sent at 12:45 PM. Total delay: 2h 45min.

- **Example 3**: Twilio SMS approval message sent with "Reply: YES {code} or NO {code}". User replies "YES {code}" but Twilio free tier doesn't support receiving SMS replies, so webhook never fires. Draft stays in status='generated' forever, never approved.

- **Edge Case**: API error occurs during Groq draft generation (rate limit, network failure). No notification sent to user. System logs error to retry_queue but user has no visibility into the failure until manually checking logs or database.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Lead scoring (pre_score and full_score) must continue to work exactly as before
- Email draft generation using Groq must continue to use existing templates and logic
- Batch processing of discovered internships must remain unchanged
- 45-55 minute spacing between sent emails must be preserved
- Daily email limit enforcement must remain unchanged
- Twilio authentication and connection logic must remain unchanged

**Scope:**
All inputs that do NOT involve the approval flow should be completely unaffected by this fix. This includes:
- Lead discovery and insertion
- Email validation (MX/SMTP checks)
- Scoring algorithms and thresholds
- Draft generation prompts and templates
- Gmail OAuth and sending logic
- Follow-up scheduling and processing

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Approval Delay Architecture**: The system uses a multi-stage approval flow:
   - Stage 1: Draft created with status='generated'
   - Stage 2: SMS sent, approval_sent_at timestamp set
   - Stage 3: Auto-approver waits 2 hours, then sets status='auto_approved' and approved_at with 10-30 min delay
   - Stage 4: Email queue checks if approved_at <= now before sending
   - This creates a minimum 2.5-3 hour delay between draft generation and email sending

2. **Twilio Paid Tier Dependency**: The SMS approval flow sends messages like "Reply: YES {code} or NO {code}" which requires:
   - Twilio webhook configuration to receive replies
   - Paid Twilio tier to support two-way SMS messaging
   - Without paid tier, replies are never received and drafts stay in 'generated' status forever

3. **Missing Error Notifications**: When API errors occur (Groq rate limits, Hunter failures, network issues):
   - Errors are logged to retry_queue table
   - No SMS/notification sent to alert user
   - User has no visibility into failures without checking logs/database manually

4. **Scheduler Timing Issues**: The auto-approver only runs during scheduler cycles (every 2 hours):
   - If drafts are created just after a cycle, they wait nearly 4 hours before auto-approval
   - Combined with the 10-30 minute delay, total wait time can exceed 4.5 hours
   - This explains why only 1/11 emails were sent in an 8-hour run

## Correctness Properties

Property 1: Fault Condition - Immediate Email Sending

_For any_ lead insertion event where a draft is successfully generated, the fixed system SHALL immediately send the email without requiring approval delays, SMS confirmation, or auto-approval timeouts, ensuring all qualifying leads receive emails within one scheduler cycle.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Existing Pipeline Behavior

_For any_ pipeline operation that does NOT involve the approval flow (lead scoring, email validation, draft generation, email spacing, daily limits), the fixed system SHALL produce exactly the same behavior as the original system, preserving all existing functionality for non-approval operations.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `backend/scheduler/cycle_manager.py`

**Function**: `_process_discovered_internships`

**Specific Changes**:
1. **Remove Approval Flow**: After draft generation, immediately mark draft as 'approved' instead of 'generated'
   - Change: `"status": "generated"` → `"status": "approved"`
   - Set `approved_at` to current timestamp (no delay)
   - Remove call to `send_approval_sms()`

2. **Update Status Transition**: Change internship status from 'pending_approval' to 'email_queued'
   - This reflects the new immediate-send flow

3. **Add Notification SMS**: After email is queued, send notification-only SMS
   - Message format: "LazyIntern: Email queued for {role} at {company} ({email})"
   - No yes/no reply required

**File**: `backend/approval/twilio_sender.py`

**Function**: `send_approval_sms` (rename to `send_notification_sms`)

**Specific Changes**:
1. **Remove Yes/No Reply Logic**: Change SMS body to notification-only format
   - Remove: "Reply: YES {short_code}\nor NO {short_code}"
   - Add: "Email queued for sending"

2. **Remove approval_sent_at Update**: This timestamp is no longer needed
   - Delete the database update that sets approval_sent_at

3. **Simplify Message**: Focus on informing user, not requesting action
   - Keep: Company, role, email, score
   - Add: "Email will send automatically"

**File**: `backend/approval/auto_approver.py`

**Function**: `run_auto_approver`

**Specific Changes**:
1. **Deprecate Auto-Approver**: This function is no longer needed since drafts are immediately approved
   - Option A: Delete the function entirely
   - Option B: Keep as no-op for backward compatibility, add comment explaining deprecation

2. **Remove from Scheduler**: Delete call to `run_auto_approver()` in `cycle_manager.py`

**File**: `backend/core/guards.py`

**Function**: `_retry_twilio` and error handling

**Specific Changes**:
1. **Add Error Notification Function**: Create new function `send_error_notification(error_type, error_message, context)`
   - Sends SMS to approver_to_number with error details
   - Format: "LazyIntern ERROR: {error_type} - {error_message}"

2. **Integrate Error Notifications**: Call `send_error_notification` in all error handlers
   - Groq API failures
   - Hunter API failures
   - Gmail sending failures
   - Twilio sending failures
   - Database errors

**File**: `backend/outreach/queue_manager.py`

**Function**: `process_email_queue`

**Specific Changes**:
1. **Remove approved_at Delay Check**: Delete the logic that skips drafts where approved_at > now
   - This delay was only needed for auto-approved drafts with random delays
   - With immediate approval, approved_at will always be <= now

2. **Simplify Query**: Remove the approved_at comparison logic since all approved drafts are ready to send

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (2-hour delays, only 1/11 emails sent), then verify the fix works correctly (all emails sent immediately) and preserves existing behavior (scoring, spacing, limits).

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Insert multiple test leads (e.g., 5 leads) into the database and observe how many emails are sent within one scheduler cycle. Run on UNFIXED code to observe the 2-hour delay and confirm only 1 email is sent.

**Test Cases**:
1. **Multiple Leads Test**: Insert 5 leads, run scheduler once, verify only 1 email sent (will fail on unfixed code - expect 0 or 1 emails)
2. **Approval Delay Test**: Insert 1 lead, check draft status immediately after generation, verify status='generated' not 'approved' (will fail on unfixed code)
3. **Auto-Approval Timing Test**: Insert 1 lead, wait 2 hours, run auto-approver, verify approved_at is set to future time (10-30 min delay) (will fail on unfixed code)
4. **Twilio Reply Test**: Send approval SMS, reply "YES {code}", verify webhook never fires on free tier (will fail on unfixed code)

**Expected Counterexamples**:
- Only 1 out of N leads gets email sent in first cycle
- Drafts remain in status='generated' for 2+ hours
- approved_at timestamp is set to future time (current time + 10-30 minutes)
- Twilio yes/no replies don't work on free tier

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (leads inserted, drafts generated), the fixed function produces the expected behavior (immediate email sending).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := process_lead_fixed(input)
  ASSERT result.draft_status = "approved"
  ASSERT result.approved_at <= currentTime
  ASSERT result.email_sent_within_one_cycle = true
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (scoring, validation, spacing, limits), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT process_pipeline_original(input) = process_pipeline_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-approval inputs

**Test Plan**: Observe behavior on UNFIXED code first for scoring, validation, and email spacing, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Scoring Preservation**: Observe that pre_score and full_score calculations work correctly on unfixed code, then verify same scores after fix
2. **Email Spacing Preservation**: Observe that 45-55 minute spacing is enforced on unfixed code, then verify same spacing after fix
3. **Daily Limit Preservation**: Observe that daily email limit is enforced on unfixed code, then verify same limit after fix
4. **Draft Generation Preservation**: Observe that Groq draft generation produces same output on unfixed code, then verify same output after fix

### Unit Tests

- Test immediate approval: draft status should be 'approved' immediately after generation
- Test approved_at timestamp: should be set to current time, not future time
- Test notification SMS: should not include yes/no reply instructions
- Test error notifications: should send SMS when API errors occur
- Test multiple leads: all leads should get emails sent (not just first one)

### Property-Based Tests

- Generate random sets of leads (1-20 leads) and verify all get emails sent within expected timeframe
- Generate random API error scenarios and verify error notifications are sent
- Generate random internship data and verify scoring produces same results before/after fix
- Test email spacing across many scenarios with different approval times

### Integration Tests

- Test full pipeline flow: discover → score → validate → draft → send (no approval delay)
- Test error recovery: simulate Groq failure, verify error notification sent, verify retry works
- Test notification SMS: verify message format is correct and doesn't request yes/no reply
- Test daily limit: send emails up to limit, verify next email waits for next day
- Test email spacing: send multiple emails, verify 45-55 minute gaps maintained
