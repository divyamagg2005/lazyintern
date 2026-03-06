# Bugfix Requirements Document

## Introduction

The email outreach system is running without crashes and successfully scraping internships (42 jobs discovered today), but no emails are being sent because the `list_discovered_internships()` function has a logic bug that prevents new internships from being processed. The function queries for internships with status="discovered" but does NOT filter out internships that have already been pre-scored. This causes it to return the same 200 already-processed internships on every cycle, while the 157 newly discovered internships with NULL pre_score are never returned and therefore never processed. This breaks the entire outreach workflow as new internships never enter the processing pipeline.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the system calls `list_discovered_internships()` THEN the function queries for internships WHERE status='discovered' without checking if pre_score IS NULL

1.2 WHEN internships are pre-scored THEN their status remains "discovered" (not changed to another status)

1.3 WHEN `list_discovered_internships()` executes THEN it returns the same 200 already-processed internships (with pre_score values) on every cycle

1.4 WHEN new internships are scraped and stored with status="discovered" and pre_score=NULL THEN they are NOT returned by `list_discovered_internships()` because the query limit is filled by old processed internships

1.5 WHEN `_process_discovered_internships()` receives the list THEN it processes internships that have already been processed, wasting cycles and never reaching new internships

1.6 WHEN the cycle completes THEN new internships remain unprocessed with NULL pre_score, no emails are extracted, and no emails are sent

### Expected Behavior (Correct)

2.1 WHEN the system calls `list_discovered_internships()` THEN the function SHALL query for internships WHERE status='discovered' AND pre_score IS NULL

2.2 WHEN new internships are scraped and stored with status="discovered" and pre_score=NULL THEN they SHALL be returned by `list_discovered_internships()`

2.3 WHEN `_process_discovered_internships()` receives the list THEN it SHALL process only unprocessed internships (those with NULL pre_score)

2.4 WHEN internships are pre-scored THEN they SHALL be excluded from future `list_discovered_internships()` queries

2.5 WHEN the cycle completes THEN new internships SHALL be pre-scored, processed through the pipeline, and emails SHALL be sent

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the system runs the recovery phase THEN the system SHALL CONTINUE TO process pending approved drafts before starting new discovery

3.2 WHEN internships have pre_score < 40 THEN the system SHALL CONTINUE TO mark them as "low_priority" and skip email extraction

3.3 WHEN internships have pre_score between 40-59 THEN the system SHALL CONTINUE TO attempt regex extraction but skip Hunter API

3.4 WHEN internships have pre_score >= 60 THEN the system SHALL CONTINUE TO attempt both regex extraction and Hunter API search

3.5 WHEN a company domain is a job board THEN the system SHALL CONTINUE TO block Hunter API calls and log "hunter_blocked_job_board"

3.6 WHEN a domain was already contacted THEN the system SHALL CONTINUE TO skip Hunter API calls and log "hunter_skipped_domain_contacted"

3.7 WHEN emails are found and validated THEN the system SHALL CONTINUE TO create leads, generate drafts, and send emails immediately

3.8 WHEN daily email limits are reached THEN the system SHALL CONTINUE TO stop sending emails and respect the limit

3.9 WHEN the query limit is reached THEN the system SHALL CONTINUE TO respect the limit parameter and return at most that many internships
