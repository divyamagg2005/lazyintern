#!/usr/bin/env python3
"""Verify that pre-scoring is working."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db

# Check internships with scores
scored = db.client.table('internships')\
    .select('id,company,role,pre_score,status')\
    .not_.is_('pre_score', 'null')\
    .order('created_at', desc=True)\
    .limit(10)\
    .execute()

print(f"✅ Found {len(scored.data)} internships WITH pre_score")
print("\nRecent scored internships:")
for s in scored.data[:5]:
    print(f"  {s['status']:15} | pre:{s['pre_score']:>3} | {s['company'][:30]}")

# Check internships without scores
unscored = db.client.table('internships')\
    .select('id,company,status')\
    .is_('pre_score', 'null')\
    .eq('status', 'discovered')\
    .limit(5)\
    .execute()

print(f"\n⏳ Found {len(unscored.data)} internships still waiting for pre_score")
