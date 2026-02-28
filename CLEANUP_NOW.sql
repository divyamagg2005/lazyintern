-- ============================================================================
-- QUICK CLEANUP - Run this in Supabase SQL Editor
-- ============================================================================
-- This deletes all data from today's partial run
-- Takes 5 seconds to run
-- ============================================================================

-- Step 1: See what exists
SELECT 
  (SELECT COUNT(*) FROM internships WHERE created_at >= CURRENT_DATE) as internships,
  (SELECT COUNT(*) FROM leads WHERE created_at >= CURRENT_DATE) as leads,
  (SELECT COUNT(*) FROM email_drafts WHERE created_at >= CURRENT_DATE) as drafts,
  (SELECT COUNT(*) FROM pipeline_events WHERE created_at >= CURRENT_DATE) as events;

-- Step 2: Delete everything from today (CASCADE handles foreign keys)
DELETE FROM email_drafts WHERE created_at >= CURRENT_DATE;
DELETE FROM leads WHERE created_at >= CURRENT_DATE;
DELETE FROM internships WHERE created_at >= CURRENT_DATE;
DELETE FROM pipeline_events WHERE created_at >= CURRENT_DATE;
DELETE FROM retry_queue WHERE created_at >= CURRENT_DATE;
DELETE FROM daily_usage_stats WHERE date = CURRENT_DATE;

-- Step 3: Verify (should all be 0)
SELECT 
  (SELECT COUNT(*) FROM internships WHERE created_at >= CURRENT_DATE) as internships,
  (SELECT COUNT(*) FROM leads WHERE created_at >= CURRENT_DATE) as leads,
  (SELECT COUNT(*) FROM email_drafts WHERE created_at >= CURRENT_DATE) as drafts,
  (SELECT COUNT(*) FROM pipeline_events WHERE created_at >= CURRENT_DATE) as events;

-- Done! Database is clean and ready for fresh run ✅
