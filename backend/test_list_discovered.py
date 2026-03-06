"""Test if list_discovered_internships returns results"""

from core.supabase_db import db

print("Testing list_discovered_internships()...")
print("=" * 80)

internships = db.list_discovered_internships(limit=200)

print(f"Found {len(internships)} discovered internships")

if internships:
    print("\nFirst 5:")
    for i in internships[:5]:
        print(f"  - {i['company']}: {i['role'][:50]} | Status: {i['status']} | Pre: {i.get('pre_score')}")
else:
    print("\n❌ No internships returned!")
    print("\nChecking database directly...")
    
    # Direct query
    res = db.client.table("internships").select("*").eq("status", "discovered").limit(5).execute()
    print(f"Direct query returned: {len(res.data)} rows")
    if res.data:
        for i in res.data:
            print(f"  - {i['company']}: {i['role'][:50]}")
