"""
Test script to demonstrate 3-day rotation logic
Shows which sources would be scraped on each day of the cycle
"""

import json
from datetime import date
from pathlib import Path

def test_rotation():
    """Test the 3-day rotation logic"""
    
    json_path = Path(__file__).parent / "data" / "job_source.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sources = data.get("sources", [])
    
    # Calculate current day of cycle
    day_of_cycle = (date.today().toordinal() % 3) + 1
    
    print("=" * 70)
    print(f"TODAY'S DATE: {date.today()}")
    print(f"CURRENT DAY OF CYCLE: {day_of_cycle}")
    print("=" * 70)
    
    # Filter sources for today
    today_sources = [s for s in sources if s.get("day_rotation") == day_of_cycle]
    
    print(f"\n✅ SOURCES TO SCRAPE TODAY (Day {day_of_cycle}): {len(today_sources)}")
    print("-" * 70)
    
    # Group by frequency
    daily = [s for s in today_sources if s.get("scrape_frequency") == "daily"]
    weekly = [s for s in today_sources if s.get("scrape_frequency") == "weekly"]
    monthly = [s for s in today_sources if s.get("scrape_frequency") == "monthly"]
    
    print(f"\nDaily sources ({len(daily)}):")
    for s in daily[:10]:  # Show first 10
        print(f"  - {s['name']}")
    if len(daily) > 10:
        print(f"  ... and {len(daily) - 10} more")
    
    if weekly:
        print(f"\nWeekly sources ({len(weekly)}):")
        for s in weekly:
            print(f"  - {s['name']}")
    
    if monthly:
        print(f"\nMonthly sources ({len(monthly)}):")
        for s in monthly[:5]:  # Show first 5
            print(f"  - {s['name']}")
        if len(monthly) > 5:
            print(f"  ... and {len(monthly) - 5} more")
    
    # Show Naukri sources for today
    naukri_today = [s for s in today_sources if "Naukri" in s.get("name", "")]
    print(f"\n🎯 Naukri sources today: {len(naukri_today)}")
    for s in naukri_today:
        print(f"  - {s['name']}")
    
    # Show what would be scraped on other days
    print("\n" + "=" * 70)
    print("ROTATION PREVIEW (All 3 Days)")
    print("=" * 70)
    
    for day in [1, 2, 3]:
        day_sources = [s for s in sources if s.get("day_rotation") == day]
        daily_count = len([s for s in day_sources if s.get("scrape_frequency") == "daily"])
        weekly_count = len([s for s in day_sources if s.get("scrape_frequency") == "weekly"])
        monthly_count = len([s for s in day_sources if s.get("scrape_frequency") == "monthly"])
        naukri_count = len([s for s in day_sources if "Naukri" in s.get("name", "")])
        
        marker = " ← TODAY" if day == day_of_cycle else ""
        print(f"\nDay {day}: {len(day_sources)} sources total{marker}")
        print(f"  - Daily: {daily_count}")
        print(f"  - Weekly: {weekly_count}")
        print(f"  - Monthly: {monthly_count}")
        print(f"  - Naukri: {naukri_count}")
    
    print("\n" + "=" * 70)
    print("EXPECTED BEHAVIOR:")
    print("=" * 70)
    print("✅ Each day scrapes ~35-45 sources (depending on weekly/monthly)")
    print("✅ Naukri sources distributed: max 2 per day (no more timeouts)")
    print("✅ Cycle time reduced from 105 sources to ~35-45 per day")
    print("✅ Each source scraped every 3 days + frequency checks")
    print("=" * 70)

if __name__ == "__main__":
    test_rotation()
