"""
Diagnostic script to investigate why no emails were sent today.
Connects to Supabase and runs read-only queries to analyze the pipeline.
"""

import os
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("🔍 DIAGNOSTIC REPORT: No Emails Sent Today")
print("=" * 80)
print(f"📅 Date: {date.today()}")
print("=" * 80)

# Query 1: Check today's internships
print("\n1️⃣ TODAY'S INTERNSHIPS:")
print("-" * 80)
result = supabase.table("internships").select(
    "id, company, role, status, pre_score, full_score, created_at"
).gte("created_at", f"{date.today()}T00:00:00").execute()

internships = result.data
print(f"Total internships scraped today: {len(internships)}")

if internships:
    # Group by status
    status_counts = {}
    pre_score_null = 0
    full_score_null = 0
    
    for i in internships:
        status = i.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if i.get("pre_score") is None:
            pre_score_null += 1
        if i.get("full_score") is None:
            full_score_null += 1
    
    print(f"\nStatus breakdown:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    
    print(f"\nScoring status:")
    print(f"  - Internships with NULL pre_score: {pre_score_null}/{len(internships)}")
    print(f"  - Internships with NULL full_score: {full_score_null}/{len(internships)}")
    
    # Show first 5 internships
    print(f"\nFirst 5 internships:")
    for i in internships[:5]:
        print(f"  - {i['company']}: {i['role'][:50]} | Status: {i['status']} | Pre: {i.get('pre_score')} | Full: {i.get('full_score')}")

# Query 2: Check today's leads
print("\n\n2️⃣ TODAY'S LEADS (EMAILS FOUND):")
print("-" * 80)
result = supabase.table("leads").select(
    "id, email, source, confidence, verified, created_at"
).gte("created_at", f"{date.today()}T00:00:00").execute()

leads = result.data
print(f"Total leads created today: {len(leads)}")

if leads:
    print(f"\nFirst 5 leads:")
    for lead in leads[:5]:
        print(f"  - {lead['email']} | Source: {lead['source']} | Verified: {lead.get('verified')}")

# Query 3: Check today's email drafts
print("\n\n3️⃣ TODAY'S EMAIL DRAFTS:")
print("-" * 80)
result = supabase.table("email_drafts").select(
    "id, status, created_at, sent_at"
).gte("created_at", f"{date.today()}T00:00:00").execute()

drafts = result.data
print(f"Total drafts created today: {len(drafts)}")

if drafts:
    status_counts = {}
    for d in drafts:
        status = d.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\nDraft status breakdown:")
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")

# Query 4: Check pipeline events
print("\n\n4️⃣ PIPELINE EVENTS FOR TODAY'S INTERNSHIPS:")
print("-" * 80)

if internships:
    internship_ids = [i["id"] for i in internships]
    
    result = supabase.table("pipeline_events").select(
        "event, metadata"
    ).in_("internship_id", internship_ids).execute()
    
    events = result.data
    print(f"Total events logged: {len(events)}")
    
    if events:
        # Group by event type
        event_counts = {}
        for e in events:
            event_type = e.get("event", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        print(f"\nEvent breakdown:")
        for event, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {event}: {count}")
        
        # Check for specific events
        critical_events = ["pre_scored", "email_found_regex", "email_found_hunter", 
                          "no_email_found", "hunter_blocked_job_board", 
                          "hunter_skipped_domain_contacted", "draft_generated", "email_sent_immediately"]
        
        print(f"\nCritical events:")
        for event in critical_events:
            count = event_counts.get(event, 0)
            symbol = "✅" if count > 0 else "❌"
            print(f"  {symbol} {event}: {count}")

# Query 5: Check daily usage stats
print("\n\n5️⃣ TODAY'S USAGE STATS:")
print("-" * 80)
result = supabase.table("daily_usage_stats").select(
    "*"
).eq("date", str(date.today())).execute()

usage = result.data
if usage:
    stats = usage[0]
    print(f"Emails sent: {stats.get('emails_sent', 0)}/{stats.get('daily_limit', 50)}")
    print(f"Hunter API calls: {stats.get('hunter_calls', 0)}")
    print(f"Groq API calls: {stats.get('groq_calls', 0)}")
    print(f"Pre-score kills: {stats.get('pre_score_kills', 0)}")
    print(f"Validation fails: {stats.get('validation_fails', 0)}")
    print(f"Auto approvals: {stats.get('auto_approvals', 0)}")
    print(f"Twilio SMS sent: {stats.get('twilio_sms_sent', 0)}")
else:
    print("No usage stats found for today")

# Query 6: Check for unprocessed discovered internships
print("\n\n6️⃣ UNPROCESSED DISCOVERED INTERNSHIPS:")
print("-" * 80)
result = supabase.table("internships").select(
    "id, company, role, created_at, pre_score"
).eq("status", "discovered").is_("pre_score", "null").execute()

unprocessed = result.data
print(f"Total unprocessed 'discovered' internships: {len(unprocessed)}")

if unprocessed:
    print(f"\nFirst 10 unprocessed internships:")
    for i in unprocessed[:10]:
        print(f"  - {i['company']}: {i['role'][:50]} | Created: {i['created_at']}")

# Query 7: Check what list_discovered_internships returns
print("\n\n7️⃣ TESTING list_discovered_internships() FUNCTION:")
print("-" * 80)
from core.supabase_db import db as db_instance
discovered_list = db_instance.list_discovered_internships(limit=200)
print(f"list_discovered_internships() returned: {len(discovered_list)} internships")

if discovered_list:
    # Check how many have NULL pre_score
    null_pre_score = sum(1 for i in discovered_list if i.get('pre_score') is None)
    print(f"  - With NULL pre_score: {null_pre_score}")
    print(f"  - With pre_score: {len(discovered_list) - null_pre_score}")
    
    # Show first 5 with NULL pre_score
    null_ones = [i for i in discovered_list if i.get('pre_score') is None][:5]
    if null_ones:
        print(f"\nFirst 5 with NULL pre_score:")
        for i in null_ones:
            print(f"  - {i['company']}: {i['role'][:50]} | Created: {i.get('created_at')}")

# Summary
print("\n\n" + "=" * 80)
print("📊 SUMMARY:")
print("=" * 80)

if len(internships) == 0:
    print("❌ ISSUE: No internships were scraped today")
    print("   → Check if scraper is running correctly")
elif pre_score_null == len(internships):
    print("❌ ISSUE: Internships were scraped but NEVER pre-scored")
    print("   → _process_discovered_internships() was never called")
    print("   → Check if run_cycle() is calling the processing function")
elif len(leads) == 0:
    print("❌ ISSUE: Internships were scored but NO emails were found")
    print("   → Check regex extraction and Hunter API logic")
elif len(drafts) == 0:
    print("❌ ISSUE: Emails were found but NO drafts were generated")
    print("   → Check draft generation logic")
elif usage and usage[0].get('emails_sent', 0) == 0:
    print("❌ ISSUE: Drafts were created but NO emails were sent")
    print("   → Check email sending logic and daily limits")
else:
    print("✅ System appears to be working correctly")

print("=" * 80)
