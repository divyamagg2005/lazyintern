-- ============================================================================
-- CLEANUP PARTIAL RUN DATA
-- ============================================================================
-- Use this to delete data from a partial/incomplete pipeline run
-- Run this in Supabase SQL Editor
-- ============================================================================

-- STEP 1: Check what data exists (run this first to see what will be deleted)
-- ============================================================================

SELECT 'internships' as table_name, COUNT(*) as count FROM internships
UNION ALL
SELECT 'leads', COUNT(*) FROM leads
UNION ALL
SELECT 'email_drafts', COUNT(*) FROM email_drafts
UNION ALL
SELECT 'pipeline_events', COUNT(*) FROM pipeline_events
UNION ALL
SELECT 'daily_usage_stats', COUNT(*) FROM daily_usage_stats
UNION ALL
SELECT 'company_domains', COUNT(*) FROM company_domains
UNION ALL
SELECT 'retry_queue', COUNT(*) FROM retry_queue
UNION ALL
SELECT 'followup_queue', COUNT(*) FROM followup_queue
UNION ALL
SELECT 'quarantine', COUNT(*) FROM quarantine;

-- ============================================================================
-- STEP 2: Delete all data from today (CAREFUL - this deletes everything!)
-- ============================================================================

-- Delete in correct order (respecting foreign keys)
-- CASCADE will handle related records automatically

-- Delete followup queue
DELETE FROM followup_queue 
WHERE created_at >= CURRENT_DATE;

-- Delete quarantine
DELETE FROM quarantine 
WHERE rejected_at >= CURRENT_DATE;

-- Delete retry queue
DELETE FROM retry_queue 
WHERE created_at >= CURRENT_DATE;

-- Delete email drafts (CASCADE will handle followup_queue references)
DELETE FROM email_drafts 
WHERE created_at >= CURRENT_DATE;

-- Delete leads (CASCADE will handle email_drafts references)
DELETE FROM leads 
WHERE created_at >= CURRENT_DATE;

-- Delete pipeline events
DELETE FROM pipeline_events 
WHERE created_at >= CURRENT_DATE;

-- Delete internships (CASCADE will handle leads references)
DELETE FROM internships 
WHERE created_at >= CURRENT_DATE;

-- Reset daily usage stats for today
DELETE FROM daily_usage_stats 
WHERE date = CURRENT_DATE;

-- Clear company domains (optional - only if you want fresh start)
-- TRUNCATE company_domains;

-- ============================================================================
-- STEP 3: Verify cleanup (should show 0 for all except scoring_config)
-- ============================================================================

SELECT 'internships' as table_name, COUNT(*) as count FROM internships
UNION ALL
SELECT 'leads', COUNT(*) FROM leads
UNION ALL
SELECT 'email_drafts', COUNT(*) FROM email_drafts
UNION ALL
SELECT 'pipeline_events', COUNT(*) FROM pipeline_events
UNION ALL
SELECT 'daily_usage_stats', COUNT(*) FROM daily_usage_stats
UNION ALL
SELECT 'scoring_config (should be 5)', COUNT(*) FROM scoring_config;

-- ============================================================================
-- ALTERNATIVE: Delete only last 5 minutes of data (safer)
-- ============================================================================

-- If you only want to delete data from the last 5 minutes:
/*
DELETE FROM followup_queue WHERE created_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM quarantine WHERE rejected_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM retry_queue WHERE created_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM email_drafts WHERE created_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM leads WHERE created_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM pipeline_events WHERE created_at >= NOW() - INTERVAL '5 minutes';
DELETE FROM internships WHERE created_at >= NOW() - INTERVAL '5 minutes';
*/

-- ============================================================================
-- NUCLEAR OPTION: Delete EVERYTHING (complete fresh start)
-- ============================================================================

-- Only use this if you want to completely reset the database
-- This keeps the table structure but deletes all data
/*
TRUNCATE TABLE followup_queue CASCADE;
TRUNCATE TABLE quarantine CASCADE;
TRUNCATE TABLE retry_queue CASCADE;
TRUNCATE TABLE email_drafts CASCADE;
TRUNCATE TABLE leads CASCADE;
TRUNCATE TABLE pipeline_events CASCADE;
TRUNCATE TABLE internships CASCADE;
TRUNCATE TABLE daily_usage_stats CASCADE;
TRUNCATE TABLE company_domains CASCADE;

-- Re-seed scoring config
INSERT INTO scoring_config (key, weight, description) VALUES
  ('relevance_score', 0.35, 'Role/title keyword match'),
  ('resume_overlap_score', 0.25, 'Resume keyword overlap with JD'),
  ('tech_stack_score', 0.20, 'Tech stack alignment'),
  ('location_score', 0.10, 'Location preference match'),
  ('historical_success_score', 0.10, 'Past reply rate for similar companies')
ON CONFLICT (key) DO NOTHING;
*/

-- ============================================================================
-- SUCCESS! Database cleaned up and ready for fresh run
-- ============================================================================
