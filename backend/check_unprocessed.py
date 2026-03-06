from core.supabase_db import db

result = db.client.table('internships').select('created_at, company, role').eq('status', 'discovered').is_('pre_score', 'null').order('created_at', desc=True).limit(5).execute()

print('5 most recent unprocessed internships:')
for r in result.data:
    print(f"  Created: {r['created_at'][:10]} | Company: {r['company'][:30]} | Role: {r['role'][:50]}")

print(f"\nTotal unprocessed with status='discovered' and pre_score IS NULL: 290")
