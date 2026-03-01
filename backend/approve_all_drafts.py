"""
Approve All Generated Drafts Script

This script updates all drafts with status='generated' to status='approved'
so they can be sent by the send_all_pending_emails.py script.

Usage:
    python backend/approve_all_drafts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.supabase_db import db, utcnow
from core.logger import logger


def approve_all_generated_drafts():
    """Update all generated drafts to approved status."""
    print("\n" + "=" * 70)
    print("APPROVE ALL GENERATED DRAFTS")
    print("=" * 70)
    print("\nThis will update all drafts with status='generated' to 'approved'")
    print("so they can be sent immediately.")
    print("=" * 70 + "\n")
    
    # Get count of generated drafts
    res = (
        db.client.table("email_drafts")
        .select("id", count="exact")
        .eq("status", "generated")
        .execute()
    )
    
    generated_count = res.count or 0
    
    if generated_count == 0:
        print("✓ No generated drafts found. All drafts are already approved or sent.")
        return
    
    print(f"Found {generated_count} draft(s) with status='generated'")
    print(f"Updating to status='approved' with approved_at=now...")
    print()
    
    try:
        # Update all generated drafts to approved
        now = utcnow().isoformat()
        res = (
            db.client.table("email_drafts")
            .update({
                "status": "approved",
                "approved_at": now
            })
            .eq("status", "generated")
            .execute()
        )
        
        updated_count = len(res.data or [])
        
        print(f"✓ Updated {updated_count} draft(s) to 'approved' status")
        print(f"✓ Set approved_at to current time: {now}")
        print()
        print("You can now run send_all_pending_emails.py to send these emails.")
        
    except Exception as e:
        print(f"✗ Error updating drafts: {e}")
        logger.error(f"Error approving drafts: {e}")
        sys.exit(1)
    
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    try:
        approve_all_generated_drafts()
    except KeyboardInterrupt:
        print("\n\n✓ Cancelled by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        logger.error(f"Fatal error in approve_all_generated_drafts: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
