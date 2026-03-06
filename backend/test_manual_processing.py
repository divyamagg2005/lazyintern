"""
Manually test the _process_discovered_internships function
to see why it's not processing internships
"""

import logging
from core.logger import setup_logging
from core.supabase_db import db
from scheduler.cycle_manager import _process_discovered_internships, _load_resume

# Set up logging
setup_logging()
logger = logging.getLogger("lazyintern")

print("=" * 80)
print("MANUAL PROCESSING TEST")
print("=" * 80)

# Check what internships are available
print("\n1. Checking discovered internships...")
internships = db.list_discovered_internships(limit=200)
print(f"Found {len(internships)} discovered internships")

if not internships:
    print("❌ No internships to process!")
    exit(1)

# Count how many have NULL pre_score
null_pre_score = sum(1 for i in internships if i.get('pre_score') is None)
print(f"  - With NULL pre_score: {null_pre_score}")
print(f"  - With pre_score: {len(internships) - null_pre_score}")

# Show first 5 with NULL pre_score
null_ones = [i for i in internships if i.get('pre_score') is None][:5]
if null_ones:
    print(f"\nFirst 5 unprocessed:")
    for i in null_ones:
        print(f"  - {i['company']}: {i['role'][:50]}")

# Load resume
print("\n2. Loading resume...")
try:
    resume = _load_resume()
    print(f"✅ Resume loaded successfully")
    print(f"   Skills: {len(resume.get('skills', []))} items")
    print(f"   Preferred locations: {resume.get('preferred_locations', [])}")
except Exception as e:
    print(f"❌ Failed to load resume: {e}")
    exit(1)

# Try to process
print("\n3. Calling _process_discovered_internships()...")
print("=" * 80)

try:
    _process_discovered_internships(resume, limit=5)  # Process only 5 for testing
    print("=" * 80)
    print("✅ Processing completed without errors")
except Exception as e:
    print("=" * 80)
    print(f"❌ Processing failed with error: {e}")
    import traceback
    traceback.print_exc()

# Check results
print("\n4. Checking results...")
internships_after = db.list_discovered_internships(limit=200)
null_after = sum(1 for i in internships_after if i.get('pre_score') is None)

print(f"Unprocessed before: {null_pre_score}")
print(f"Unprocessed after: {null_after}")
print(f"Processed: {null_pre_score - null_after}")

if null_pre_score == null_after:
    print("\n❌ NO INTERNSHIPS WERE PROCESSED!")
    print("This confirms the bug - _process_discovered_internships() is not working")
else:
    print(f"\n✅ {null_pre_score - null_after} internships were processed")
