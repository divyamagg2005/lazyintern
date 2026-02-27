export type DashboardEnv = {
  url?: string;
  anonKey?: string;
};

// Placeholder: wire @supabase/supabase-js when you want live dashboard data.
export function getSupabaseEnv(): DashboardEnv {
  return {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  };
}

