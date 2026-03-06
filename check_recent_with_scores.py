#!/usr/bin/env python3
"""Check ALL recent internships including those with scores."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from datetime import datetime, timedelta

def main():
    print("=" * 60)
    print("ALL Recent Internships (including scored)")
    print("=" * 60)
    
    # Get ALL recent internships (not just discovered)
    cutoff = datetime.utcnow() - timedelta(hours=1)  # Last 1 hour
    
    try:
        result = db.client.table('internships')\
            .select('id,company,role,status,pre_score,full_score,created_at')\
            .gte('created_at', cutoff.isoformat())\
            .order('created_at', desc=True)\
            .limit(50)\
            .execute()
        
        internships = result.data
        
        print(f"\nFound {len(internships)} internships in last hour\n")
        
        # Count by status
        status_counts = {}
        for job in internships:
            status = job.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Status breakdown:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        print("\n" + "=" * 60)
        print("Recent internships (last 20):")
        print("=" * 60)
        
        for job in internships[:20]:
            company = job.get('company', 'N/A')[:25].ljust(25)
            role = job.get('role', 'N/A')[:35].ljust(35)
            status = job.get('status', 'N/A').ljust(15)
            pre = str(job.get('pre_score', 'None')).rjust(4)
            full = str(job.get('full_score', 'None')).rjust(4)
            
            print(f"{status} | pre:{pre} full:{full} | {company} | {role}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
