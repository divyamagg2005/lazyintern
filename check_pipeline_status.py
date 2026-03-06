#!/usr/bin/env python3
"""Quick diagnostic script to check LazyIntern pipeline status"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from core.supabase_db import db

def main():
    print("=" * 60)
    print("LazyIntern Pipeline Status Check")
    print("=" * 60)
    print()
    
    # Check logs directory
    logs_dir = Path("backend/logs")
    print(f"1. Logs directory exists: {logs_dir.exists()}")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"   Log files found: {len(log_files)}")
        if log_files:
            latest = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"   Latest log: {latest.name}")
            print(f"   Last modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
    else:
        print("   ⚠️  Logs directory missing - pipeline may not have run yet")
    print()
    
    # Check Supabase for recent activity
    print("2. Checking Supabase for recent activity...")
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    try:
        # Check leads (no status column)
        leads = db.client.table('leads').select('id,created_at,email').gte('created_at', cutoff.isoformat()).limit(10).execute()
        print(f"   Leads in last 24h: {len(leads.data)}")
        if leads.data:
            for lead in leads.data[:5]:
                print(f"     - {lead['email']} at {lead['created_at']}")
        else:
            print("     ⚠️  No leads found in last 24 hours")
        print()
        
        # Check internships
        internships = db.client.table('internships').select('id,created_at,status,company,role').gte('created_at', cutoff.isoformat()).limit(10).execute()
        print(f"   Internships in last 24h: {len(internships.data)}")
        if internships.data:
            for job in internships.data[:5]:
                print(f"     - {job['status']}: {job['company']} - {job['role']}")
        else:
            print("     ⚠️  No internships found in last 24 hours")
        print()
        
        # Check drafts (table name is email_drafts, not drafts)
        drafts = db.client.table('email_drafts').select('id,created_at,status').gte('created_at', cutoff.isoformat()).limit(10).execute()
        print(f"   Drafts in last 24h: {len(drafts.data)}")
        if drafts.data:
            for draft in drafts.data[:5]:
                print(f"     - {draft['status']} at {draft['created_at']}")
        else:
            print("     ⚠️  No drafts found in last 24 hours")
        print()
        
        # Check daily usage (table name is daily_usage_stats)
        today = datetime.utcnow().date().isoformat()
        usage = db.client.table('daily_usage_stats').select('*').eq('date', today).execute()
        if usage.data:
            u = usage.data[0]
            print(f"3. Today's usage ({today}):")
            print(f"   Emails sent: {u.get('emails_sent', 0)}/{u.get('daily_limit', 50)}")
            print(f"   SMS sent: {u.get('twilio_sms_sent', 0)}/50")
            print(f"   Groq calls: {u.get('groq_calls', 0)}")
            print(f"   Hunter calls: {u.get('hunter_calls', 0)}")
        else:
            print(f"3. Today's usage ({today}):")
            print("   ⚠️  No usage data - pipeline hasn't run today")
        print()
        
        # Store results for diagnosis
        has_data = len(leads.data) > 0 or len(internships.data) > 0
        
    except Exception as e:
        print(f"   ❌ Error checking Supabase: {e}")
        print()
        has_data = False
        leads = type('obj', (object,), {'data': []})()
        internships = type('obj', (object,), {'data': []})()

    
    print("=" * 60)
    print("Diagnosis:")
    print("=" * 60)
    
    if not logs_dir.exists():
        print("❌ Logs directory missing")
        print("   → Pipeline has never run OR logging not configured")
        print()
        print("Next steps:")
        print("   1. Create logs directory: mkdir backend\\logs")
        print("   2. Run a test cycle: cd backend && python run_one_cycle.py")
        print("   3. Check if logs are created")
    elif not has_data:
        print("⚠️  No recent data in Supabase")
        print("   → Pipeline may not be running or scraping is failing")
        print()
        print("Next steps:")
        print("   1. Run a test cycle: cd backend && python run_one_cycle.py")
        print("   2. Check terminal output for errors")
        print("   3. Verify .env configuration")
    else:
        print("✅ Pipeline appears to be working!")
        print(f"   Found {len(leads.data)} leads and {len(internships.data)} internships")
    
    print()

if __name__ == "__main__":
    main()
