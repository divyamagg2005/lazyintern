"""
Test script to verify 3-day rotation logic implementation
"""

from datetime import date
from scraper.scrape_router import load_sources, _should_scrape_source, _is_linkedin_url

def test_rotation_logic():
    """Test the rotation logic without actually scraping"""
    
    sources = load_sources()
    tracking = {"sources": {}}  # Empty tracking for testing
    
    # Calculate current day
    day_of_cycle = (date.today().toordinal() % 3) + 1
    
    print("=" * 80)
    print(f"🔄 3-DAY ROTATION TEST")
    print(f"📅 Date: {date.today()}")
    print(f"🔢 Current day of cycle: {day_of_cycle}")
    print("=" * 80)
    
    # Count sources by day
    day_counts = {1: 0, 2: 0, 3: 0, None: 0}
    linkedin_count = 0
    
    for source in sources:
        day_rot = source.get("day_rotation")
        day_counts[day_rot] = day_counts.get(day_rot, 0) + 1
        
        if _is_linkedin_url(source.get("url", "")):
            linkedin_count += 1
    
    print(f"\n📊 Source Distribution:")
    print(f"   Day 1: {day_counts.get(1, 0)} sources")
    print(f"   Day 2: {day_counts.get(2, 0)} sources")
    print(f"   Day 3: {day_counts.get(3, 0)} sources")
    print(f"   No rotation: {day_counts.get(None, 0)} sources")
    print(f"   LinkedIn sources: {linkedin_count}")
    print(f"   Total: {len(sources)} sources")
    
    # Test which sources would be scraped today
    to_scrape = []
    to_skip = []
    
    for source in sources:
        should_scrape, skip_reason = _should_scrape_source(source, tracking)
        if should_scrape:
            to_scrape.append(source.get("name", "Unknown"))
        else:
            to_skip.append((source.get("name", "Unknown"), skip_reason))
    
    print(f"\n✅ Sources to scrape today (Day {day_of_cycle}): {len(to_scrape)}")
    print(f"⏭️  Sources to skip today: {len(to_skip)}")
    
    # Show first 5 sources to scrape
    print(f"\n📋 First 5 sources to scrape:")
    for i, name in enumerate(to_scrape[:5], 1):
        print(f"   {i}. {name}")
    
    # Show first 5 sources to skip with reasons
    print(f"\n⏭️  First 5 sources to skip:")
    for i, (name, reason) in enumerate(to_skip[:5], 1):
        print(f"   {i}. {name} ({reason})")
    
    # Count LinkedIn sources to scrape today
    linkedin_to_scrape = [s for s in to_scrape if any(_is_linkedin_url(src.get("url", "")) for src in sources if src.get("name") == s)]
    print(f"\n🔗 LinkedIn sources to scrape today: {len([s for s in sources if _is_linkedin_url(s.get('url', '')) and _should_scrape_source(s, tracking)[0]])}")
    
    print("\n" + "=" * 80)
    print("✅ Rotation logic test complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_rotation_logic()
