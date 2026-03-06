#!/usr/bin/env python3
"""Test pre-scoring on a single internship."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from pipeline.pre_scorer import pre_score

def main():
    print("=" * 60)
    print("Testing Pre-Scoring")
    print("=" * 60)
    
    # Get one discovered internship
    internships = db.list_discovered_internships(limit=1)
    
    if not internships:
        print("❌ No discovered internships found")
        return
    
    internship = internships[0]
    print(f"\nTesting internship:")
    print(f"  Company: {internship.get('company')}")
    print(f"  Role: {internship.get('role')}")
    print(f"  Status: {internship.get('status')}")
    print(f"  Current pre_score: {internship.get('pre_score')}")
    
    print("\n" + "=" * 60)
    print("Running pre_score()...")
    print("=" * 60)
    
    try:
        ps = pre_score(internship)
        print(f"\n✅ Pre-scoring completed!")
        print(f"   Score: {ps.score}")
        print(f"   Breakdown: {ps.breakdown}")
        
        # Update the database
        print(f"\nUpdating database...")
        db.client.table("internships").update(
            {"pre_score": ps.score}
        ).eq("id", internship["id"]).execute()
        print(f"✅ Database updated")
        
    except Exception as e:
        print(f"\n❌ Error during pre-scoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
