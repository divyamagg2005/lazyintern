"""
Validate job_source.json structure and check for issues
"""

import json
from pathlib import Path

def validate_job_source():
    """Validate the job_source.json file"""
    
    json_path = Path(__file__).parent / "data" / "job_source.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=" * 80)
        print("✅ VALID JSON - File parsed successfully")
        print("=" * 80)
        
        sources = data.get("sources", [])
        print(f"\n📊 Total sources: {len(sources)}")
        
        # Check for missing day_rotation
        missing_rotation = [s for s in sources if "day_rotation" not in s]
        print(f"\n⚠️  Sources missing 'day_rotation' field: {len(missing_rotation)}")
        
        if missing_rotation:
            print("\nFirst 10 sources missing day_rotation:")
            for i, source in enumerate(missing_rotation[:10], 1):
                print(f"   {i}. {source.get('name', 'Unknown')}")
        
        # Check day_rotation distribution
        day_counts = {1: 0, 2: 0, 3: 0}
        for source in sources:
            day_rot = source.get("day_rotation")
            if day_rot in day_counts:
                day_counts[day_rot] += 1
        
        print(f"\n📈 Day rotation distribution:")
        print(f"   Day 1: {day_counts[1]} sources")
        print(f"   Day 2: {day_counts[2]} sources")
        print(f"   Day 3: {day_counts[3]} sources")
        
        # Check for invalid day_rotation values
        invalid_rotation = [s for s in sources if s.get("day_rotation") not in [1, 2, 3, None]]
        if invalid_rotation:
            print(f"\n❌ Sources with invalid day_rotation (not 1, 2, or 3): {len(invalid_rotation)}")
            for source in invalid_rotation[:5]:
                print(f"   - {source.get('name')}: day_rotation={source.get('day_rotation')}")
        
        # Check scrape_frequency values
        freq_counts = {}
        for source in sources:
            freq = source.get("scrape_frequency", "daily")
            freq_counts[freq] = freq_counts.get(freq, 0) + 1
        
        print(f"\n📅 Scrape frequency distribution:")
        for freq, count in sorted(freq_counts.items()):
            print(f"   {freq}: {count} sources")
        
        # Check for required fields
        print(f"\n🔍 Checking required fields...")
        missing_fields = []
        for i, source in enumerate(sources):
            if not source.get("name"):
                missing_fields.append(f"Source {i}: missing 'name'")
            if not source.get("url"):
                missing_fields.append(f"Source {i}: missing 'url'")
            if not source.get("type"):
                missing_fields.append(f"Source {i}: missing 'type'")
        
        if missing_fields:
            print(f"❌ Found {len(missing_fields)} sources with missing required fields:")
            for issue in missing_fields[:10]:
                print(f"   - {issue}")
        else:
            print("✅ All sources have required fields (name, url, type)")
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION COMPLETE")
        print("=" * 80)
        
        # Summary
        if not missing_rotation and not invalid_rotation and not missing_fields:
            print("\n🎉 Perfect! Your job_source.json is fully compatible with the rotation code!")
        else:
            print("\n⚠️  Issues found - see details above")
        
    except json.JSONDecodeError as e:
        print(f"❌ INVALID JSON: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    validate_job_source()
