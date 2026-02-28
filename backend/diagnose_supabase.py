"""
Quick diagnostic script to check Supabase connection and permissions
"""

from core.config import settings
from supabase import create_client

def diagnose():
    print("=" * 60)
    print("SUPABASE DIAGNOSTIC")
    print("=" * 60)
    print()
    
    # Check config
    print("1. Configuration Check:")
    print(f"   URL: {settings.supabase_url}")
    print(f"   Service Role Key: {settings.supabase_service_role_key[:20]}...")
    print()
    
    # Try to connect
    print("2. Connection Test:")
    try:
        client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        print("   ✓ Client created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create client: {e}")
        return
    print()
    
    # Check if tables exist
    print("3. Tables Check:")
    try:
        # Try to list tables by querying information_schema
        result = client.rpc('get_tables').execute()
        print(f"   Tables found: {result.data}")
    except Exception as e:
        print(f"   Note: RPC call failed (expected if function doesn't exist)")
        print(f"   Error: {e}")
    print()
    
    # Try to query scoring_config
    print("4. Scoring Config Table Test:")
    try:
        result = client.table("scoring_config").select("*").limit(1).execute()
        print(f"   ✓ Table exists, rows: {len(result.data)}")
        if result.data:
            print(f"   Sample: {result.data[0]}")
    except Exception as e:
        print(f"   ✗ Failed to query scoring_config: {e}")
        print()
        print("   This means either:")
        print("   a) Table doesn't exist (need to run fresh_setup_quick.sql)")
        print("   b) Permission issue (check RLS policies)")
    print()
    
    # Try to query internships
    print("5. Internships Table Test:")
    try:
        result = client.table("internships").select("*").limit(1).execute()
        print(f"   ✓ Table exists, rows: {len(result.data)}")
    except Exception as e:
        print(f"   ✗ Failed to query internships: {e}")
    print()
    
    # Try to insert a test row
    print("6. Write Permission Test:")
    try:
        result = client.table("daily_usage_stats").select("*").eq("date", "2026-03-01").execute()
        if result.data:
            print(f"   ✓ Can read daily_usage_stats")
        else:
            print(f"   Table exists but empty for today")
    except Exception as e:
        print(f"   ✗ Failed to query daily_usage_stats: {e}")
    print()
    
    print("=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print()
    print("If tables don't exist:")
    print("  1. Go to Supabase SQL Editor")
    print("  2. Copy contents of backend/db/fresh_setup_quick.sql")
    print("  3. Paste and run in SQL Editor")
    print()
    print("If permission denied:")
    print("  1. Go to Supabase Dashboard > Authentication > Policies")
    print("  2. Disable RLS on all tables (for service role)")
    print("  3. Or add policy: service_role can do everything")
    print()

if __name__ == "__main__":
    diagnose()
