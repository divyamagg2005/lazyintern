#!/usr/bin/env python3
"""Process all unscored internships through the pipeline."""

import sys
sys.path.insert(0, 'backend')

from core.supabase_db import db
from scheduler.cycle_manager import _process_discovered_internships
from pipeline.pre_scorer import _load_resume

def main():
    print("=" * 70)
    print("PROCESSING UNSCORED INTERNSHIPS")
    print("=" * 70)
    print()
    
    # Check how many unscored internships exist
    unscored = db.client.table('internships')\
        .select('id,company,role,status')\
        .eq('status', 'discovered')\
        .is_('pre_score', 'null')\
        .execute()
    
    count = len(unscored.data) if unscored.data else 0
    
    print(f"Found {count} unscored internships with status='discovered'")
    print()
    
    if count == 0:
        print("✅ No unscored internships to process")
        return
    
    print(f"Processing {count} internships through the pipeline...")
    print("This will:")
    print("  1. Pre-score each internship")
    print("  2. Extract emails (regex + Hunter.io)")
    print("  3. Validate emails")
    print("  4. Full score")
    print("  5. Generate drafts")
    print("  6. Send emails immediately")
    print("  7. Send SMS notifications")
    print()
    
    input("Press Enter to continue or Ctrl+C to cancel...")
    print()
    
    # Load resume for scoring
    resume = _load_resume()
    
    # Process all discovered internships
    print("Starting processing...")
    print("=" * 70)
    
    try:
        _process_discovered_internships(resume, limit=500)
        print()
        print("=" * 70)
        print("✅ Processing complete!")
        print()
        
        # Check results
        remaining = db.client.table('internships')\
            .select('id')\
            .eq('status', 'discovered')\
            .is_('pre_score', 'null')\
            .execute()
        
        remaining_count = len(remaining.data) if remaining.data else 0
        processed_count = count - remaining_count
        
        print(f"Processed: {processed_count} internships")
        print(f"Remaining: {remaining_count} internships")
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
