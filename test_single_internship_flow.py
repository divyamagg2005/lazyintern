#!/usr/bin/env python3
"""Test processing a single internship through the entire pipeline."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from pipeline.pre_scorer import pre_score

def main():
    print("=" * 70)
    print("TESTING SINGLE INTERNSHIP FLOW")
    print("=" * 70)
    print()
    
    # Get one discovered internship
    internships = db.list_discovered_internships(limit=1)
    
    if not internships:
        print("❌ No discovered internships to test")
        return
    
    internship = internships[0]
    iid = internship["id"]
    
    print(f"Testing internship:")
    print(f"  ID: {iid}")
    print(f"  Company: {internship.get('company')}")
    print(f"  Role: {internship.get('role')}")
    print(f"  Status: {internship.get('status')}")
    print()
    
    # Test 1: Pre-scoring
    print("Test 1: Pre-scoring...")
    try:
        ps = pre_score(internship)
        print(f"  ✅ Pre-score calculated: {ps.score}")
        print(f"  ✅ Breakdown: {ps.breakdown}")
        
        # Update database
        db.client.table("internships").update(
            {"pre_score": ps.score}
        ).eq("id", iid).execute()
        print(f"  ✅ Database updated")
    except Exception as e:
        print(f"  ❌ Pre-scoring failed: {e}")
        return
    
    print()
    
    # Test 2: Event logging
    print("Test 2: Event logging...")
    try:
        db.log_event(iid, "test_event", {"test": True})
        print(f"  ✅ Event logged successfully")
    except Exception as e:
        print(f"  ❌ Event logging failed: {e}")
        return
    
    print()
    
    # Test 3: Daily usage tracking
    print("Test 3: Daily usage tracking...")
    try:
        from core.supabase_db import today_utc
        today = today_utc()
        usage = db.get_or_create_daily_usage(today)
        print(f"  ✅ Daily usage retrieved: {usage.emails_sent}/{usage.daily_limit} emails")
    except Exception as e:
        print(f"  ❌ Daily usage tracking failed: {e}")
        return
    
    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED - Pipeline flow is working correctly")
    print("=" * 70)

if __name__ == '__main__':
    main()
