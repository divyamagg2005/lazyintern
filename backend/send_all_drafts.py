"""
Send all pending email drafts (16 emails).
This will send emails to all leads with generated drafts.
"""

import time
from core.supabase_db import db, today_utc
from outreach.gmail_client import send_email
from core.logger import logger

def send_all_pending_drafts():
    """Send all drafts with status='generated'."""
    
    print("=" * 70)
    print("Send All Pending Drafts")
    print("=" * 70)
    
    # Get all pending drafts
    print("\n1. Fetching pending drafts...")
    result = (
        db.client.table("email_drafts")
        .select("*")
        .eq("status", "generated")
        .execute()
    )
    
    pending_drafts = result.data or []
    total = len(pending_drafts)
    
    if total == 0:
        print("   No pending drafts found.")
        print("\n   All drafts have already been sent or rejected.")
        return
    
    print(f"   ✓ Found {total} pending draft(s)")
    
    # Confirm before sending
    print("\n" + "=" * 70)
    print("CONFIRMATION")
    print("=" * 70)
    print(f"\nYou are about to send {total} emails.")
    print("\nRecipients:")
    
    # Show first 5 recipients
    for i, draft in enumerate(pending_drafts[:5], 1):
        lead_id = draft.get("lead_id")
        if lead_id:
            lead_result = db.client.table("leads").select("email").eq("id", lead_id).limit(1).execute()
            if lead_result.data:
                email = lead_result.data[0].get("email", "")
                print(f"  {i}. {email}")
    
    if total > 5:
        print(f"  ... and {total - 5} more")
    
    print("\n⚠️  WARNING: This will send real emails to real people!")
    response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\nCancelled. No emails sent.")
        return
    
    # Send emails
    print("\n" + "=" * 70)
    print("Sending Emails")
    print("=" * 70)
    
    success_count = 0
    error_count = 0
    
    for idx, draft in enumerate(pending_drafts, 1):
        draft_id = draft["id"]
        lead_id = draft.get("lead_id")
        
        if not lead_id:
            print(f"\n[{idx}/{total}] ❌ Draft {draft_id}: No lead_id")
            error_count += 1
            continue
        
        # Get lead info
        lead_result = db.client.table("leads").select("*").eq("id", lead_id).limit(1).execute()
        if not lead_result.data:
            print(f"\n[{idx}/{total}] ❌ Draft {draft_id}: Lead not found")
            error_count += 1
            continue
        
        lead = lead_result.data[0]
        email = lead.get("email", "")
        
        # Get internship info for logging
        internship_id = lead.get("internship_id")
        company = "Unknown"
        if internship_id:
            internship_result = db.client.table("internships").select("company").eq("id", internship_id).limit(1).execute()
            if internship_result.data:
                company = internship_result.data[0].get("company", "Unknown")
        
        print(f"\n[{idx}/{total}] Sending to: {email} ({company})")
        
        try:
            # Send email
            send_email(draft, lead)
            
            print(f"         ✓ Email sent successfully")
            success_count += 1
            
            # Add 2 second delay between emails to avoid rate limiting
            if idx < total:
                time.sleep(2)
            
        except Exception as e:
            print(f"         ❌ Failed: {str(e)[:100]}")
            error_count += 1
            continue
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal drafts: {total}")
    print(f"✓ Sent successfully: {success_count}")
    print(f"❌ Failed: {error_count}")
    
    if success_count > 0:
        print(f"\n🎉 {success_count} email(s) sent!")
        print("\nNext steps:")
        print("1. Check your Gmail 'Sent' folder to verify")
        print("2. Follow-ups will be sent automatically after 5 days")
        print("3. Monitor replies in Gmail")
    
    if error_count > 0:
        print(f"\n⚠️  {error_count} email(s) failed")
        print("Check the error messages above for details")
        print("Failed emails are added to retry queue")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    send_all_pending_drafts()
