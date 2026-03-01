"""
Cleanup All Data Script

This script deletes ALL data from the database tables to start fresh.

⚠️ WARNING: This is DESTRUCTIVE and CANNOT be undone!
⚠️ Make sure you've sent all pending emails first using send_all_pending_emails.py

Usage:
    python backend/cleanup_all_data.py

What it deletes:
- All internships
- All leads
- All email drafts
- All followup queue entries
- All event logs
- All retry queue entries
- Daily usage stats (optional)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_db import db
from core.logger import logger


def get_table_counts():
    """Get count of records in each table."""
    tables = [
        "internships",
        "leads",
        "email_drafts",
        "followup_queue",
        "event_log",
        "retry_queue",
        "daily_usage_stats"
    ]
    
    counts = {}
    for table in tables:
        try:
            res = db.client.table(table).select("id", count="exact").execute()
            counts[table] = res.count or 0
        except Exception as e:
            counts[table] = f"Error: {e}"
    
    return counts


def cleanup_all_data(keep_daily_stats=False):
    """
    Delete all data from database tables.
    
    Args:
        keep_daily_stats: If True, keeps daily_usage_stats table intact
    """
    print("\n" + "=" * 70)
    print("⚠️  CLEANUP ALL DATA - DESTRUCTIVE OPERATION ⚠️")
    print("=" * 70)
    print("\nThis will DELETE ALL DATA from the following tables:")
    print("  - internships")
    print("  - leads")
    print("  - email_drafts")
    print("  - followup_queue")
    print("  - event_log")
    print("  - retry_queue")
    if not keep_daily_stats:
        print("  - daily_usage_stats")
    print("\n⚠️  THIS CANNOT BE UNDONE! ⚠️")
    print("=" * 70 + "\n")
    
    # Show current counts
    print("📊 Current record counts:")
    counts = get_table_counts()
    for table, count in counts.items():
        if keep_daily_stats and table == "daily_usage_stats":
            print(f"  - {table}: {count} (will be kept)")
        else:
            print(f"  - {table}: {count}")
    print()
    
    # Triple confirmation
    print("⚠️  CONFIRMATION REQUIRED ⚠️")
    print("Type 'DELETE ALL DATA' to proceed (case-sensitive):")
    response = input("> ").strip()
    
    if response != "DELETE ALL DATA":
        print("\n✓ Cancelled. No data was deleted.")
        return
    
    print("\n" + "=" * 70)
    print("DELETING DATA")
    print("=" * 70 + "\n")
    
    deleted_counts = {}
    
    # Delete in order to respect foreign key constraints
    # Order: followup_queue -> email_drafts -> leads -> internships -> event_log -> retry_queue
    
    tables_to_delete = [
        ("followup_queue", "Followup queue entries"),
        ("email_drafts", "Email drafts"),
        ("leads", "Leads"),
        ("internships", "Internships"),
        ("event_log", "Event logs"),
        ("retry_queue", "Retry queue entries"),
    ]
    
    if not keep_daily_stats:
        tables_to_delete.append(("daily_usage_stats", "Daily usage stats"))
    
    for table, description in tables_to_delete:
        try:
            print(f"🗑️  Deleting {description}...", end=" ")
            
            # Delete all records (no filter = delete all)
            res = db.client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            # Count remaining records
            count_res = db.client.table(table).select("id", count="exact").execute()
            remaining = count_res.count or 0
            
            if remaining == 0:
                print(f"✓ Deleted all records")
                deleted_counts[table] = "all"
            else:
                print(f"⚠ {remaining} records remaining")
                deleted_counts[table] = f"{remaining} remaining"
                
        except Exception as e:
            print(f"✗ Error: {e}")
            deleted_counts[table] = f"Error: {e}"
            logger.error(f"Error deleting from {table}: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    
    for table, status in deleted_counts.items():
        print(f"  - {table}: {status}")
    
    print("\n✓ Cleanup complete!")
    print("\nYou can now start fresh with a clean database.")
    print("Run the pipeline to discover new internships and send emails.")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    try:
        # Ask if user wants to keep daily stats
        print("\n" + "=" * 70)
        print("CLEANUP OPTIONS")
        print("=" * 70)
        print("\nDo you want to keep daily usage stats?")
        print("(This preserves your email sending history and limits)")
        print()
        response = input("Keep daily_usage_stats? (yes/no): ").strip().lower()
        keep_stats = response in ["yes", "y"]
        
        cleanup_all_data(keep_daily_stats=keep_stats)
        
    except KeyboardInterrupt:
        print("\n\n✓ Cancelled by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        logger.error(f"Fatal error in cleanup_all_data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
