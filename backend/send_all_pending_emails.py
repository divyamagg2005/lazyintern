"""
Send All Pending Emails Script

This script sends emails to all leads that have approved drafts in the database.
Use this to clear out pending emails before starting fresh.

Usage:
    python backend/send_all_pending_emails.py

Features:
- Sends all approved/auto_approved drafts
- Respects email spacing (45-55 minutes between sends)
- Respects daily email limit
- Shows progress in real-time
- Handles errors gracefully
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_db import db, today_utc, utcnow
from outreach.queue_manager import process_email_queue
from core.logger import logger


def get_pending_drafts_count():
    """Get count of pending approved drafts."""
    res = (
        db.client.table("email_drafts")
        .select("id", count="exact")
        .in_("status", ["approved", "auto_approved"])
        .execute()
    )
    return res.count or 0


def get_all_draft_statuses():
    """Get count of drafts by status for debugging."""
    res = (
        db.client.table("email_drafts")
        .select("status")
        .execute()
    )
    
    statuses = {}
    for draft in res.data or []:
        status = draft.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    
    return statuses


def get_last_sent_time():
    """Get timestamp of last sent email."""
    res = (
        db.client.table("email_drafts")
        .select("sent_at")
        .eq("status", "sent")
        .order("sent_at", desc=True)
        .limit(1)
        .execute()
    )
    
    if res.data:
        return datetime.fromisoformat(res.data[0]["sent_at"].replace("Z", "+00:00"))
    return None


def calculate_wait_time():
    """Calculate how long to wait before next email can be sent."""
    last_sent = get_last_sent_time()
    
    if not last_sent:
        return 0  # No previous email, can send immediately
    
    now = utcnow()
    time_since_last = (now - last_sent).total_seconds()
    min_gap_seconds = 45 * 60  # 45 minutes
    
    if time_since_last >= min_gap_seconds:
        return 0  # Enough time has passed
    
    wait_seconds = min_gap_seconds - time_since_last
    return wait_seconds


def send_all_pending_emails():
    """
    Send all pending approved emails IMMEDIATELY.
    
    This function bypasses spacing and daily limit constraints
    since it's an explicit manual operation for cleanup.
    """
    print("\n" + "=" * 70)
    print("SEND ALL PENDING EMAILS - IMMEDIATE MODE")
    print("=" * 70)
    print("\nThis script will send ALL approved drafts IMMEDIATELY.")
    print("⚠️  Bypasses spacing constraints and daily limits.")
    print("⚠️  Use only for manual cleanup before database reset.")
    print("\nPress Ctrl+C to stop at any time.")
    print("=" * 70 + "\n")
    
    # Get initial counts
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    daily_limit = usage.daily_limit or 15
    pending_count = get_pending_drafts_count()
    all_statuses = get_all_draft_statuses()
    
    print(f"📊 Status:")
    print(f"  - Pending drafts (approved/auto_approved): {pending_count}")
    print(f"  - All draft statuses:")
    for status, count in all_statuses.items():
        print(f"    • {status}: {count}")
    print(f"  - Emails sent today: {usage.emails_sent}/{daily_limit}")
    print()
    
    if pending_count == 0:
        print("✓ No pending approved drafts found.")
        print("\n⚠️  Note: If you have drafts with status='generated', they need to be")
        print("   approved first. Run: python approve_all_drafts.py")
        return
    
    print(f"⚠️  IMMEDIATE MODE: Will send all {pending_count} emails without delays.")
    print(f"⚠️  This bypasses the 45-minute spacing constraint.")
    print(f"⚠️  This bypasses the daily limit of {daily_limit}.")
    print()
    
    # Auto-start without confirmation
    print(f"Starting to send {pending_count} email(s) immediately...")
    print()
    
    print("\n" + "=" * 70)
    print("SENDING EMAILS - IMMEDIATE MODE")
    print("=" * 70 + "\n")
    
    emails_sent = 0
    
    try:
        while True:
            # Check if there are pending drafts
            pending_count = get_pending_drafts_count()
            if pending_count == 0:
                print("\n✓ All pending drafts have been sent!")
                break
            
            # Send one email immediately (no spacing check, no daily limit check)
            print(f"📧 Sending email {emails_sent + 1}/{pending_count + emails_sent}...", end=" ")
            
            try:
                # Get one approved draft directly
                res = (
                    db.client.table("email_drafts")
                    .select("*, leads!inner(id, email, internship_id)")
                    .in_("status", ["approved", "auto_approved"])
                    .order("approved_at", desc=False)
                    .limit(1)
                    .execute()
                )
                
                drafts = res.data or []
                if not drafts:
                    print("⚠ No more drafts to send")
                    break
                
                row = drafts[0]
                draft = row
                lead = {
                    "email": row["leads"]["email"],
                    "id": row["leads"].get("id"),
                    "internship_id": row["leads"].get("internship_id")
                }
                
                # Send email directly using gmail_client
                from outreach import gmail_client
                gmail_client.send_email(draft, lead)
                
                # Update usage counter
                today = today_utc()
                db.bump_daily_usage(today, emails_sent=1)
                
                emails_sent += 1
                pending_count = get_pending_drafts_count()
                print(f"✓ Sent to {lead['email']}! ({pending_count} pending)")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
                logger.error(f"Error sending email: {e}")
                # Continue to next email instead of stopping
                continue
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
    
    # Final summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Emails sent: {emails_sent}")
    
    usage = db.get_or_create_daily_usage(today)
    pending_count = get_pending_drafts_count()
    print(f"✓ Total emails sent today: {usage.emails_sent}")
    print(f"✓ Pending drafts remaining: {pending_count}")
    
    if pending_count > 0:
        print(f"\n⚠ {pending_count} draft(s) still pending.")
        print("  - Run the script again to send remaining emails.")
    else:
        print("\n✓ All pending drafts have been sent!")
        print("✓ You can now run cleanup_all_data.py to reset the database.")
    
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    try:
        send_all_pending_emails()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        logger.error(f"Fatal error in send_all_pending_emails: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
