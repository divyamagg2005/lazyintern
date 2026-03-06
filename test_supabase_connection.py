#!/usr/bin/env python3
"""Test Supabase connection and query performance."""

import sys
import time
sys.path.insert(0, 'backend')

from core.supabase_db import db

def test_query(name, query_func):
    """Test a query and measure its execution time."""
    print(f"\nTesting: {name}")
    print("-" * 60)
    start = time.time()
    try:
        result = query_func()
        elapsed = time.time() - start
        print(f"✅ Success in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Failed after {elapsed:.2f}s: {e}")
        return None

def main():
    print("=" * 60)
    print("Supabase Connection Test")
    print("=" * 60)
    
    # Test 1: Simple count query
    test_query(
        "Count internships",
        lambda: db.client.table("internships").select("id", count="exact").execute()
    )
    
    # Test 2: Get discovered internships
    result = test_query(
        "List discovered internships (limit 1)",
        lambda: db.list_discovered_internships(limit=1)
    )
    
    if result and len(result) > 0:
        internship = result[0]
        iid = internship["id"]
        
        # Test 3: Log event
        test_query(
            "Log event",
            lambda: db.log_event(iid, "test_event", {"test": True})
        )
        
        # Test 4: Update internship
        test_query(
            "Update internship pre_score",
            lambda: db.client.table("internships").update(
                {"pre_score": 50}
            ).eq("id", iid).execute()
        )
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == '__main__':
    main()
