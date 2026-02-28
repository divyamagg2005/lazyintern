-- LazyIntern Complete Database Schema
-- Run this fresh after truncating existing database

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Core internship data
CREATE TABLE IF NOT EXISTS internships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company TEXT NOT NULL,
  role TEXT NOT NULL,
  link TEXT UNIQUE NOT NULL,
  description TEXT,
  location TEXT,
  posted_date DATE,
  source_url TEXT,
  pre_score INTEGER,
  full_score INTEGER,
  status TEXT DEFAULT 'discovered',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_internships_status ON internships(status);
CREATE INDEX IF NOT EXISTS idx_internships_created_at ON internships(created_at);

-- Validated leads with emails
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id) ON DELETE CASCADE,
  recruiter_name TEXT,
  email TEXT NOT NULL,
  source TEXT,
  confidence INTEGER,
  verified BOOLEAN DEFAULT FALSE,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on internship_id for duplicate checking
CREATE INDEX IF NOT EXISTS idx_leads_internship_id ON leads(internship_id);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- Domain-level Hunter cache
CREATE TABLE IF NOT EXISTS company_domains (
  domain TEXT PRIMARY KEY,
  emails JSONB,
  hunter_called BOOLEAN DEFAULT FALSE,
  last_checked TIMESTAMPTZ,
  reply_history JSONB,
  firecrawl_calls_this_week INTEGER DEFAULT 0,
  week_start DATE
);

-- Generated email drafts
CREATE TABLE IF NOT EXISTS email_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  followup_body TEXT,
  status TEXT DEFAULT 'generated',
  approval_sent_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for email queue processing
CREATE INDEX IF NOT EXISTS idx_email_drafts_status ON email_drafts(status);
CREATE INDEX IF NOT EXISTS idx_email_drafts_approved_at ON email_drafts(approved_at);
CREATE INDEX IF NOT EXISTS idx_email_drafts_sent_at ON email_drafts(sent_at);

-- Quarantine for rejected leads
CREATE TABLE IF NOT EXISTS quarantine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  draft_id UUID REFERENCES email_drafts(id) ON DELETE CASCADE,
  rejected_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  re_evaluate_after DATE,
  re_evaluated BOOLEAN DEFAULT FALSE,
  re_evaluation_score INTEGER
);

-- ============================================================================
-- USAGE TRACKING & LIMITS
-- ============================================================================

-- Daily API usage tracking (UPDATED with twilio_sms_sent)
CREATE TABLE IF NOT EXISTS daily_usage_stats (
  date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
  emails_sent INTEGER DEFAULT 0,
  daily_limit INTEGER DEFAULT 5,
  hunter_calls INTEGER DEFAULT 0,
  firecrawl_calls INTEGER DEFAULT 0,
  groq_calls INTEGER DEFAULT 0,
  groq_tokens_used INTEGER DEFAULT 0,
  pre_score_kills INTEGER DEFAULT 0,
  validation_fails INTEGER DEFAULT 0,
  auto_approvals INTEGER DEFAULT 0,
  twilio_sms_sent INTEGER DEFAULT 0
);

-- Create index on date for faster queries
CREATE INDEX IF NOT EXISTS idx_daily_usage_stats_date ON daily_usage_stats(date);

-- ============================================================================
-- LOGGING & EVENTS
-- ============================================================================

-- Full pipeline event log
CREATE TABLE IF NOT EXISTS pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id) ON DELETE CASCADE,
  event TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on event and created_at for analytics
CREATE INDEX IF NOT EXISTS idx_pipeline_events_event ON pipeline_events(event);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_created_at ON pipeline_events(created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_internship_id ON pipeline_events(internship_id);

-- ============================================================================
-- RETRY & QUEUE MANAGEMENT
-- ============================================================================

-- Retry queue
CREATE TABLE IF NOT EXISTS retry_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phase TEXT NOT NULL,
  payload JSONB NOT NULL,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  next_retry_at TIMESTAMPTZ,
  last_error TEXT,
  resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on resolved and next_retry_at for processing
CREATE INDEX IF NOT EXISTS idx_retry_queue_resolved ON retry_queue(resolved);
CREATE INDEX IF NOT EXISTS idx_retry_queue_next_retry_at ON retry_queue(next_retry_at);

-- Follow-up email queue
CREATE TABLE IF NOT EXISTS followup_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES email_drafts(id) ON DELETE CASCADE,
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  send_after DATE,
  sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on send_after and sent for processing
CREATE INDEX IF NOT EXISTS idx_followup_queue_send_after ON followup_queue(send_after);
CREATE INDEX IF NOT EXISTS idx_followup_queue_sent ON followup_queue(sent);

-- ============================================================================
-- CONFIGURATION
-- ============================================================================

-- Tunable scoring weights
CREATE TABLE IF NOT EXISTS scoring_config (
  key TEXT PRIMARY KEY,
  weight FLOAT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default scoring weights
INSERT INTO scoring_config (key, weight, description) VALUES
  ('relevance_score', 0.35, 'Role/title keyword match'),
  ('resume_overlap_score', 0.25, 'Resume keyword overlap with JD'),
  ('tech_stack_score', 0.20, 'Tech stack alignment'),
  ('location_score', 0.10, 'Location preference match'),
  ('historical_success_score', 0.10, 'Past reply rate for similar companies')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- HELPFUL VIEWS (Optional but useful)
-- ============================================================================

-- View: Active pipeline summary
CREATE OR REPLACE VIEW pipeline_summary AS
SELECT 
  COUNT(*) FILTER (WHERE status = 'discovered') as discovered,
  COUNT(*) FILTER (WHERE status = 'low_priority') as low_priority,
  COUNT(*) FILTER (WHERE status = 'no_email') as no_email,
  COUNT(*) FILTER (WHERE status = 'email_invalid') as email_invalid,
  COUNT(*) FILTER (WHERE pre_score IS NOT NULL) as pre_scored,
  COUNT(*) FILTER (WHERE full_score IS NOT NULL) as full_scored,
  COUNT(*) FILTER (WHERE full_score >= 60) as high_quality
FROM internships;

-- View: Email draft status summary
CREATE OR REPLACE VIEW draft_summary AS
SELECT 
  COUNT(*) FILTER (WHERE status = 'generated') as pending_approval,
  COUNT(*) FILTER (WHERE status = 'approved') as approved,
  COUNT(*) FILTER (WHERE status = 'auto_approved') as auto_approved,
  COUNT(*) FILTER (WHERE status = 'sent') as sent,
  COUNT(*) FILTER (WHERE status = 'rejected') as rejected
FROM email_drafts;

-- View: Today's usage stats
CREATE OR REPLACE VIEW todays_usage AS
SELECT * FROM daily_usage_stats 
WHERE date = CURRENT_DATE;

-- ============================================================================
-- USEFUL FUNCTIONS
-- ============================================================================

-- Function: Get pending auto-approvals
CREATE OR REPLACE FUNCTION get_pending_auto_approvals(timeout_hours INTEGER DEFAULT 2)
RETURNS TABLE (
  draft_id UUID,
  internship_id UUID,
  company TEXT,
  role TEXT,
  email TEXT,
  full_score INTEGER,
  hours_waiting FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ed.id as draft_id,
    i.id as internship_id,
    i.company,
    i.role,
    l.email,
    i.full_score,
    EXTRACT(EPOCH FROM (NOW() - ed.approval_sent_at))/3600 as hours_waiting
  FROM email_drafts ed
  JOIN leads l ON ed.lead_id = l.id
  JOIN internships i ON l.internship_id = i.id
  WHERE ed.status = 'generated'
    AND ed.approval_sent_at < NOW() - (timeout_hours || ' hours')::INTERVAL
  ORDER BY ed.approval_sent_at;
END;
$$ LANGUAGE plpgsql;

-- Function: Get email spacing violations
CREATE OR REPLACE FUNCTION check_email_spacing(min_gap_minutes INTEGER DEFAULT 45)
RETURNS TABLE (
  draft_id UUID,
  sent_at TIMESTAMPTZ,
  prev_sent_at TIMESTAMPTZ,
  gap_minutes FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    id as draft_id,
    sent_at,
    LAG(sent_at) OVER (ORDER BY sent_at) as prev_sent_at,
    EXTRACT(EPOCH FROM (sent_at - LAG(sent_at) OVER (ORDER BY sent_at)))/60 as gap_minutes
  FROM email_drafts
  WHERE status = 'sent'
    AND sent_at IS NOT NULL
  ORDER BY sent_at DESC
  LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE internships IS 'Core internship opportunities discovered from job boards';
COMMENT ON TABLE leads IS 'Extracted and validated email contacts for internships';
COMMENT ON TABLE email_drafts IS 'AI-generated email drafts awaiting approval or sent';
COMMENT ON TABLE daily_usage_stats IS 'Daily API usage tracking and limits enforcement';
COMMENT ON TABLE pipeline_events IS 'Complete audit log of all pipeline events';
COMMENT ON TABLE retry_queue IS 'Failed operations queued for retry';
COMMENT ON TABLE followup_queue IS 'Scheduled follow-up emails';
COMMENT ON TABLE scoring_config IS 'Tunable weights for scoring algorithm';
COMMENT ON TABLE quarantine IS 'Rejected leads for future re-evaluation';
COMMENT ON TABLE company_domains IS 'Cached Hunter.io results and reply history';

COMMENT ON COLUMN daily_usage_stats.twilio_sms_sent IS 'Number of SMS sent today (limit: 15/day)';
COMMENT ON COLUMN email_drafts.approved_at IS 'Timestamp when approved (includes random delay for auto-approvals)';
COMMENT ON COLUMN email_drafts.approval_sent_at IS 'Timestamp when SMS approval request was sent';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these after schema creation to verify everything is set up correctly

-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check scoring_config is seeded
SELECT * FROM scoring_config ORDER BY key;

-- Check indexes exist
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check views exist
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check functions exist
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_type = 'FUNCTION'
ORDER BY routine_name;
