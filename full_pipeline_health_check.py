#!/usr/bin/env python3
"""Comprehensive pipeline health check."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from datetime import datetime, timedelta

def check_database_connection():
    """Test database connectivity."""
    try:
        result = db.client.table('internships').select('id').limit(1).execute()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {e}"

def check_pre_scoring():
    """Check if pre-scoring is working."""
    try:
        # Check for recently scored internships
        cutoff = datetime.utcnow() - timedelta(hours=2)
        scored = db.client.table('internships')\
            .select('id,pre_score,created_at')\
            .not_.is_('pre_score', 'null')\
            .gte('created_at', cutoff.isoformat())\
            .execute()
        
        if scored.data and len(scored.data) > 0:
            return True, f"Pre-scoring working: {len(scored.data)} internships scored in last 2 hours"
        
        # Check if there are any scored internships at all
        any_scored = db.client.table('internships')\
            .select('id,pre_score')\
            .not_.is_('pre_score', 'null')\
            .limit(1)\
            .execute()
        
        if any_scored.data:
            return True, "Pre-scoring functional (older scores found)"
        
        return False, "No pre-scored internships found"
    except Exception as e:
        return False, f"Pre-scoring check failed: {e}"

def check_email_extraction():
    """Check if email extraction is working."""
    try:
        leads = db.client.table('leads').select('id,email').limit(5).execute()
        if leads.data and len(leads.data) > 0:
            return True, f"Email extraction working: {len(leads.data)} leads found"
        return False, "No leads found (email extraction may not have run yet)"
    except Exception as e:
        return False, f"Email extraction check failed: {e}"

def check_draft_generation():
    """Check if draft generation is working."""
    try:
        drafts = db.client.table('email_drafts').select('id,status').limit(5).execute()
        if drafts.data and len(drafts.data) > 0:
            return True, f"Draft generation working: {len(drafts.data)} drafts found"
        return False, "No drafts found (may not have reached this stage yet)"
    except Exception as e:
        return False, f"Draft generation check failed: {e}"

def check_daily_usage():
    """Check daily usage tracking."""
    try:
        from core.supabase_db import today_utc
        today = today_utc()
        usage = db.get_or_create_daily_usage(today)
        return True, f"Daily usage: {usage.emails_sent}/{usage.daily_limit} emails, {usage.hunter_calls} Hunter calls, {usage.groq_calls} Groq calls"
    except Exception as e:
        return False, f"Daily usage check failed: {e}"

def check_discovered_internships():
    """Check for internships waiting to be processed."""
    try:
        discovered = db.client.table('internships')\
            .select('id')\
            .eq('status', 'discovered')\
            .limit(10)\
            .execute()
        
        count = len(discovered.data) if discovered.data else 0
        if count > 0:
            return True, f"{count} internships waiting to be processed"
        return True, "No internships waiting (all processed)"
    except Exception as e:
        return False, f"Discovered internships check failed: {e}"

def main():
    print("=" * 70)
    print("LAZYINTERN PIPELINE HEALTH CHECK")
    print("=" * 70)
    print()
    
    checks = [
        ("Database Connection", check_database_connection),
        ("Pre-Scoring", check_pre_scoring),
        ("Email Extraction", check_email_extraction),
        ("Draft Generation", check_draft_generation),
        ("Daily Usage Tracking", check_daily_usage),
        ("Discovered Internships", check_discovered_internships),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} | {name}")
            print(f"       {message}")
            print()
            
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL | {name}")
            print(f"       Unexpected error: {e}")
            print()
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Pipeline is fully functional")
    else:
        print("⚠️  SOME CHECKS FAILED - Review issues above")
    print("=" * 70)

if __name__ == '__main__':
    main()
