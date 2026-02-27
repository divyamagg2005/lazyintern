"""
Quick script to verify scoring_config is seeded correctly.
"""

from core.supabase_db import db

def verify_scoring_config():
    print("=" * 60)
    print("Verifying Scoring Config in Supabase")
    print("=" * 60)
    
    # Trigger seeding
    print("\n1. Calling seed_scoring_config_if_empty()...")
    db.seed_scoring_config_if_empty()
    print("   ✓ Seeding completed (or already existed)")
    
    # Fetch current config
    print("\n2. Fetching scoring_config from Supabase...")
    res = db.client.table("scoring_config").select("*").execute()
    
    if not res.data:
        print("   ✗ ERROR: scoring_config table is empty!")
        return False
    
    print(f"   ✓ Found {len(res.data)} scoring config entries")
    
    # Display config
    print("\n3. Current Scoring Weights:")
    print("-" * 60)
    total_weight = 0.0
    for entry in res.data:
        key = entry.get("key", "unknown")
        weight = entry.get("weight", 0.0)
        description = entry.get("description", "")
        total_weight += weight
        print(f"   {key:30s} | {weight:.2f} | {description}")
    
    print("-" * 60)
    print(f"   {'TOTAL':30s} | {total_weight:.2f}")
    
    # Verify total is 1.0
    print("\n4. Validation:")
    if abs(total_weight - 1.0) < 0.01:
        print("   ✓ Total weight = 1.00 (100%) - CORRECT")
    else:
        print(f"   ✗ Total weight = {total_weight:.2f} - INCORRECT (should be 1.00)")
        return False
    
    # Verify expected keys
    expected_keys = {
        "relevance_score",
        "resume_overlap_score", 
        "tech_stack_score",
        "location_score",
        "historical_success_score"
    }
    actual_keys = {entry["key"] for entry in res.data}
    
    if expected_keys == actual_keys:
        print("   ✓ All expected keys present")
    else:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if missing:
            print(f"   ✗ Missing keys: {missing}")
        if extra:
            print(f"   ⚠ Extra keys: {extra}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ SCORING CONFIG VERIFIED SUCCESSFULLY")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        verify_scoring_config()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
