from core.supabase_db import db, today_utc

print("=" * 70)
print("PIPELINE DIAGNOSTIC")
print("=" * 70)

# Check discovered internships
discovered = db.client.table('internships').select('id').eq('status', 'discovered').execute()
print(f"\n1. Discovered internships waiting: {len(discovered.data)}")

# Check low_priority
low_priority = db.client.table('internships').select('id, company, role, pre_score').eq('status', 'low_priority').limit(5).execute()
print(f"\n2. Low priority (pre-score < 40): {len(low_priority.data)}")
if low_priority.data:
    for i in low_priority.data[:3]:
        print(f"   - {i['company']}: {i['role']} (score: {i.get('pre_score', 'N/A')})")

# Check no_email
no_email = db.client.table('internships').select('id').eq('status', 'no_email').execute()
print(f"\n3. No email found: {len(no_email.data)}")

# Check today's stats
today = today_utc()
today_internships = db.client.table('internships').select('id', count='exact').gte('created_at', str(today)).execute()
print(f"\n4. Total internships discovered today: {today_internships.count}")

# Check leads
today_leads = db.client.table('leads').select('id, email, verified', count='exact').gte('created_at', str(today)).execute()
print(f"\n5. Total leads created today: {today_leads.count}")
if today_leads.data:
    print("   Recent leads:")
    for lead in today_leads.data[:5]:
        print(f"   - {lead['email']} (verified: {lead.get('verified', 'N/A')})")

# Check email_sent status
email_sent = db.client.table('internships').select('id', count='exact').eq('status', 'email_sent').gte('created_at', str(today)).execute()
print(f"\n6. Emails sent today: {email_sent.count}")

# Check daily usage
usage = db.get_or_create_daily_usage(today)
print(f"\n7. Daily Usage Stats:")
print(f"   - Emails sent: {usage.emails_sent}/{usage.daily_limit}")
print(f"   - Hunter calls: {usage.hunter_calls}")
print(f"   - Groq calls: {usage.groq_calls}")
print(f"   - SMS sent: {usage.twilio_sms_sent}/50")

print("\n" + "=" * 70)
