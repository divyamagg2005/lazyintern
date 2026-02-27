import { createClient, type SupabaseClient } from "@supabase/supabase-js";

type Json = string | number | boolean | null | { [key: string]: Json } | Json[];

export type Database = {
  public: {
    Tables: {
      internships: { Row: Record<string, Json> };
      leads: { Row: Record<string, Json> };
      email_drafts: { Row: Record<string, Json> };
      daily_usage_stats: { Row: Record<string, Json> };
      pipeline_events: { Row: Record<string, Json> };
      retry_queue: { Row: Record<string, Json> };
      company_domains: { Row: Record<string, Json> };
      followup_queue: { Row: Record<string, Json> };
    };
  };
};

function readEnv(name: string): string | null {
  const value = process.env[name];
  return value && value.trim() ? value : null;
}

export function createSupabaseServerClient(): SupabaseClient<Database> | null {
  const url = readEnv("SUPABASE_URL") ?? readEnv("NEXT_PUBLIC_SUPABASE_URL");
  const key =
    readEnv("SUPABASE_SERVICE_ROLE_KEY") ?? readEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY");

  if (!url || !key) {
    return null;
  }

  return createClient<Database>(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

