# Bugfix Requirements Document

## Introduction

The lead processing pipeline has multiple critical failures preventing automated email outreach. After an 8-hour run, the system found 11 leads but only sent 1 email due to a broken auto-approval mechanism. Additionally, the SMS approval flow relies on Twilio's paid tier features (yes/no replies) which are unavailable, blocking the entire approval process. The system needs to transition to a fully automated immediate-send pipeline with notification-only messages and proper error alerting.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the system finds multiple leads (e.g., 11 leads) THEN only 1 email is sent instead of all qualifying leads receiving emails

1.2 WHEN the auto-approval mechanism is triggered THEN it fails to approve and send emails for subsequent leads after the first one

1.3 WHEN Twilio attempts to send yes/no approval SMS messages THEN the messages fail because the feature requires a paid Twilio tier that is not available

1.4 WHEN API errors or script failures occur during lead processing THEN no notifications are sent to alert the user of the failure

### Expected Behavior (Correct)

2.1 WHEN a lead is inserted into the leads table THEN the system SHALL immediately generate a draft email and send it without requiring approval

2.2 WHEN the auto-approval mechanism processes leads THEN the system SHALL successfully send emails to all qualifying leads found during the run

2.3 WHEN Twilio sends messages THEN the system SHALL send notification-only messages (e.g., "Email sent to [person]") without requiring yes/no replies

2.4 WHEN API errors or script failures occur THEN the system SHALL send notification messages via Twilio alerting the user of the specific error

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a lead is scored and validated THEN the system SHALL CONTINUE TO insert the lead into the leads table with all required fields

3.2 WHEN an email draft is generated THEN the system SHALL CONTINUE TO use the existing draft generation logic and templates

3.3 WHEN Twilio credentials are configured THEN the system SHALL CONTINUE TO authenticate and connect to the Twilio API successfully

3.4 WHEN the system processes leads in batches THEN the system SHALL CONTINUE TO maintain the existing batch processing logic and timing
