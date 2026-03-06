#!/usr/bin/env python3
"""Check recent internships and their scoring status."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from datetime import datetime, timedelta

def main():
    print("=" * 60)
    print("Recent Internships Status Check")
    print("=" * 60)
    
    # Get recent internships
    cutoff = datetime.utcnow() - timedelta(hours=48)  # Check last 48 hours
    
    try:
        result = db.client.table('internships')\
            .select('id,company,role,status,pre_score,full_score,created_at')\
            .gte('created_at', cutoff.isoformat())\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()
        
        internships = result.data
        
        print(f"\nFound {len(internships)} internships in last 48h\n")
        
        # Count by status
        status_counts = {}
        pre_score_none = 0
        full_score_none = 0
        
        for job in internships:
            status = job.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if job.get('pre_score') is None:
                pre_score_none += 1
            if job.get('full_score') is None:
                full_score_none += 1
        
        print("Status breakdown:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        print(f"\nScoring status:")
        print(f"  Missing pre_score: {pre_score_none}/{len(internships)}")
        print(f"  Missing full_score: {full_score_none}/{len(internships)}")
        
        print("\n" + "=" * 60)
        print("Recent internships detail:")
        print("=" * 60)
        
        for job in internships[:10]:
            company = job.get('company', 'N/A')[:25].ljust(25)
            role = job.get('role', 'N/A')[:35].ljust(35)
            status = job.get('status', 'N/A').ljust(15)
            pre = str(job.get('pre_score', 'None')).rjust(4)
            full = str(job.get('full_score', 'None')).rjust(4)
            
            print(f"{status} | pre:{pre} full:{full} | {company} | {role}")
        
        # Critical check
        print("\n" + "=" * 60)
        if pre_score_none == len(internships) and len(internships) > 0:
            print("🚨 CRITICAL: NO PRE-SCORING IS HAPPENING!")
            print("   All internships are stuck at 'discovered' status")
            print("   Pre-scoring function is not being executed")
        elif pre_score_none > 0:
            print(f"⚠️  WARNING: {pre_score_none} internships missing pre_score")
        else:
            print("✅ Pre-scoring appears to be working")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
