"""
Verify the 3-day rotation distribution in job_source.json
"""

import json
from pathlib import Path
from collections import Counter

def verify_rotation():
    """Verify day_rotation distribution"""
    
    json_path = Path(__file__).parent / "data" / "job_source.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sources = data.get("sources", [])
    
    # Count by day_rotation
    rotation_counts = Counter()
    frequency_by_day = {1: Counter(), 2: Counter(), 3: Counter()}
    
    for source in sources:
        day = source.get("day_rotation", 0)
        freq = source.get("scrape_frequency", "daily")
        rotation_counts[day] += 1
        frequency_by_day[day][freq] += 1
    
    print("=" * 60)
    print("3-DAY ROTATION DISTRIBUTION")
    print("=" * 60)
    print(f"\nTotal sources: {len(sources)}")
    print(f"\nDay 1: {rotation_counts[1]} sources")
    print(f"  - daily: {frequency_by_day[1]['daily']}")
    print(f"  - weekly: {frequency_by_day[1]['weekly']}")
    print(f"  - monthly: {frequency_by_day[1]['monthly']}")
    
    print(f"\nDay 2: {rotation_counts[2]} sources")
    print(f"  - daily: {frequency_by_day[2]['daily']}")
    print(f"  - weekly: {frequency_by_day[2]['weekly']}")
    print(f"  - monthly: {frequency_by_day[2]['monthly']}")
    
    print(f"\nDay 3: {rotation_counts[3]} sources")
    print(f"  - daily: {frequency_by_day[3]['daily']}")
    print(f"  - weekly: {frequency_by_day[3]['weekly']}")
    print(f"  - monthly: {frequency_by_day[3]['monthly']}")
    
    print("\n" + "=" * 60)
    print("EXPECTED BEHAVIOR:")
    print("=" * 60)
    print("- Each day will scrape ~35-45 sources (depending on day of cycle)")
    print("- Naukri sources are distributed across all 3 days")
    print("- Monthly sources only scrape if >30 days since last scrape")
    print("- Weekly sources only scrape if >7 days since last scrape")
    print("- This reduces cycle time from 105 sources to ~35-45 per day")
    print("=" * 60)

if __name__ == "__main__":
    verify_rotation()
