from core.supabase_db import db

# Check all discovered internships
all_discovered = db.client.table('internships').select('pre_score, status').eq('status', 'discovered').execute()

print(f"Total with status='discovered': {len(all_discovered.data)}")

# Count by pre_score
null_count = sum(1 for r in all_discovered.data if r['pre_score'] is None)
not_null_count = sum(1 for r in all_discovered.data if r['pre_score'] is not None)

print(f"  - With pre_score IS NULL: {null_count}")
print(f"  - With pre_score NOT NULL: {not_null_count}")

# Show sample of those with pre_score NOT NULL
if not_null_count > 0:
    print("\nSample of 'discovered' internships that have pre_score (already processed):")
    samples = [r for r in all_discovered.data if r['pre_score'] is not None][:5]
    for s in samples:
        print(f"  pre_score: {s['pre_score']}")
