-- Migration: Add SMS tracking to daily_usage_stats
-- Run this on your Supabase database to add the new column

-- Add twilio_sms_sent column if it doesn't exist
ALTER TABLE daily_usage_stats 
ADD COLUMN IF NOT EXISTS twilio_sms_sent INTEGER DEFAULT 0;

-- Update existing rows to have default value
UPDATE daily_usage_stats 
SET twilio_sms_sent = 0 
WHERE twilio_sms_sent IS NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'daily_usage_stats' 
AND column_name = 'twilio_sms_sent';
