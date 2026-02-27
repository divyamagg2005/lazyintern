-- LazyIntern schema (from logs/final_pipeline.md)

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

-- Validated leads with emails
CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  recruiter_name TEXT,
  email TEXT NOT NULL,
  source TEXT,
  confidence INTEGER,
  verified BOOLEAN DEFAULT FALSE,
  mx_valid BOOLEAN,
  smtp_valid BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

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
  lead_id UUID REFERENCES leads(id),
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  followup_body TEXT,
  status TEXT DEFAULT 'generated',
  approval_sent_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quarantine for rejected leads
CREATE TABLE IF NOT EXISTS quarantine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id),
  draft_id UUID REFERENCES email_drafts(id),
  rejected_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  re_evaluate_after DATE,
  re_evaluated BOOLEAN DEFAULT FALSE,
  re_evaluation_score INTEGER
);

-- Daily API usage tracking
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
  auto_approvals INTEGER DEFAULT 0
);

-- Full pipeline event log
CREATE TABLE IF NOT EXISTS pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  internship_id UUID REFERENCES internships(id),
  event TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

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

-- Follow-up email queue
CREATE TABLE IF NOT EXISTS followup_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES email_drafts(id),
  lead_id UUID REFERENCES leads(id),
  send_after DATE,
  sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tunable scoring weights
CREATE TABLE IF NOT EXISTS scoring_config (
  key TEXT PRIMARY KEY,
  weight FLOAT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
