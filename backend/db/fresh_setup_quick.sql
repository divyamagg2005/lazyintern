-- ============================================================================
-- LAZYINTERN FRESH DATABASE SETUP - QUICK VERSION
-- ============================================================================
-- Run this in Supabase SQL Editor after dropping all tables
-- This is the complete schema with all latest changes
-- ============================================================================

-- STEP 1: Drop everything (if exists)
-- ============================================================================

DROP TABLE IF EXISTS pipeline_events CASCADE;
DROP TABLE IF EXISTS retry_queue CASCADE;
DROP TABLE IF EXISTS followup_queue CASCADE;
DROP TABLE IF EXISTS quarantine CASCADE;
DROP TABLE IF EXISTS email_drafts CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS company_domains CASCADE;
DROP TABLE IF EXISTS internships CASCADE;
DROP TABLE IF EXISTS daily_usage_stats CASCADE;
DROP TABLE IF EXISTS scoring_config CASCADE;
DROP VIEW IF EXISTS pipeline_summary CASCADE;
DROP VIEW IF EXISTS draft_summary CASCADE;
DROP VIEW IF EXISTS todays_usage CASCADE;
DROP FUNCTION IF EXISTS get_pending_auto_approvals(INTEGER);
DROP FUNCTION IF EXISTS check_email_spacing(INTEGER);

-- STEP 2: Create all tables
-- ============================================================================

-- Internships
CREATE TABLE internships (
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

CREATE INDEX idx_internships_status ON internships(status);
CREATE INDEX idx_internships_created_at ON internships(created_at);

-- Leads
CREATE TABLE leads (
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

CREATE INDEX idx_leads_internship_id ON leads(internship_id);
CREATE INDEX idx_leads_email ON leads(email);

-- Company Domains
CREATE TABLE company_domains (
  domain TEXT PRIMARY KEY,
  emails JSONB,
  hunter_called BOOLEAN DEFAULT FALSE,
  last_checked TIMESTAMPTZ,
  reply_history JSONB,
  firecrawl_calls_this_week INTEGER DEFAULT 0,
  week_start DATE
);

-- Email Drafts
CREATE TABLE email_drafts (
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

CREATE INDEX idx_email_drafts_status ON email_drafts(status);
CREATE INDEX idx_email_drafts_approved_at ON email_drafts(approved_at);
CREATE INDEX idx_email_drafts_sent_at ON email_drafts(sent_at);

-- Quarantine
CREATE TABLE quarantine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  draft_id UUID REFERENCES email_drafts(id) ON DELETE CASCADE,
  rejected_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  re_evaluate_after DATE,
  re_evaluated BOOLEAN DEFAULT FALSE,
  re_evaluation_score INTEGER
);

-- Daily Usage Stats (WITH twilio_sms_sent column)
CREATE TABLE daily_usage_stats (
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

CREATE INDEX idx_daily_usage_stats_date ON daily_usage_stats(date);

-- Pipeline Events
CREATE TABLE pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id) ON DELETE CASCADE,
  event TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_events_event ON pipeline_events(event);
CREATE INDEX idx_pipeline_events_created_at ON pipeline_events(created_at);
CREATE INDEX idx_pipeline_events_internship_id ON pipeline_events(internship_id);

-- Retry Queue
CREATE TABLE retry_queue (
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

CREATE INDEX idx_retry_queue_resolved ON retry_queue(resolved);
CREATE INDEX idx_retry_queue_next_retry_at ON retry_queue(next_retry_at);

-- Followup Queue
CREATE TABLE followup_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES email_drafts(id) ON DELETE CASCADE,
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  send_after DATE,
  sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_followup_queue_send_after ON followup_queue(send_after);
CREATE INDEX idx_followup_queue_sent ON followup_queue(sent);

-- Scoring Config
CREATE TABLE scoring_config (
  key TEXT PRIMARY KEY,
  weight FLOAT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- STEP 3: Seed scoring config
-- ============================================================================

INSERT INTO scoring_config (key, weight, description) VALUES
  ('relevance_score', 0.35, 'Role/title keyword match'),
  ('resume_overlap_score', 0.25, 'Resume keyword overlap with JD'),
  ('tech_stack_score', 0.20, 'Tech stack alignment'),
  ('location_score', 0.10, 'Location preference match'),
  ('historical_success_score', 0.10, 'Past reply rate for similar companies');

-- STEP 4: Create views
-- ============================================================================

CREATE VIEW pipeline_summary AS
SELECT 
  COUNT(*) FILTER (WHERE status = 'discovered') as discovered,
  COUNT(*) FILTER (WHERE status = 'low_priority') as low_priority,
  COUNT(*) FILTER (WHERE status = 'no_email') as no_email,
  COUNT(*) FILTER (WHERE status = 'email_invalid') as email_invalid,
  COUNT(*) FILTER (WHERE pre_score IS NOT NULL) as pre_scored,
  COUNT(*) FILTER (WHERE full_score IS NOT NULL) as full_scored,
  COUNT(*) FILTER (WHERE full_score >= 60) as high_quality
FROM internships;

CREATE VIEW draft_summary AS
SELECT 
  COUNT(*) FILTER (WHERE status = 'generated') as pending_approval,
  COUNT(*) FILTER (WHERE status = 'approved') as approved,
  COUNT(*) FILTER (WHERE status = 'auto_approved') as auto_approved,
  COUNT(*) FILTER (WHERE status = 'sent') as sent,
  COUNT(*) FILTER (WHERE status = 'rejected') as rejected
FROM email_drafts;

CREATE VIEW todays_usage AS
SELECT * FROM daily_usage_stats 
WHERE date = CURRENT_DATE;

-- STEP 5: Create functions
-- ============================================================================

CREATE FUNCTION get_pending_auto_approvals(timeout_hours INTEGER DEFAULT 2)
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

CREATE FUNCTION check_email_spacing(min_gap_minutes INTEGER DEFAULT 45)
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
-- VERIFICATION - Run these to confirm setup
-- ============================================================================

-- Should return 10 tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Should return 5 rows
SELECT * FROM scoring_config ORDER BY key;

-- Should return twilio_sms_sent column
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
  AND column_name = 'twilio_sms_sent';

-- Should return 3 views
SELECT table_name FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should return 2 functions
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
ORDER BY routine_name;

-- ============================================================================
-- SUCCESS! Your database is ready to use.
-- ============================================================================
