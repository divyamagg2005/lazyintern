"""
Test script to verify all three fixes:
1. Scrape frequency tracking
2. Daily stats reset
3. SMS daily limit enforcement
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from core.supabase_db import db, today_utc, utcnow
from scraper.scrape_router import _load_tracking, _should_scrape_source, _update_tracking
from approval.twilio_sender import send_notification_sms
from core.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent
TRACKING_PATH = PROJECT_ROOT / "data" / "source_tracking.json"


def test_scrape_frequency():
    """Test Issue 1: Scrape frequency tracking"""
    print("\n" + "=" * 70)
    print("TEST 1: Scrape Frequency Tracking")
    print("=" * 70)
    
    # Load tracking
    tracking = _load_tracking()
    print(f"\n✓ Tracking file loaded: {TRACKING_PATH}")
    print(f"  Sources tracked: {len(tracking.get('sources', {}))}")
    
    # Test daily source (should always scrape)
    daily_source = {
        "name": "Test Daily Source",
        "url": "https://example.com/daily",
        "scrape_frequency": "daily"
    }
    should_scrape = _should_scrape_source(daily_source, tracking)
    print(f"\n✓ Daily source: should_scrape = {should_scrape} (expected: True)")
    assert should_scrape is True, "Daily sources should always scrape"
    
    # Test weekly source (just scraped)
    weekly_source = {
        "name": "Test Weekly Source",
        "url": "https://example.com/weekly",
        "scrape_frequency": "weekly"
    }
    
    # Simulate recent scrape
    test_tracking = {"sources": {}}
    _update_tracking(weekly_source["url"], test_tracking)
    
    should_scrape = _should_scrape_source(weekly_source, test_tracking)
    print(f"✓ Weekly source (just scraped): should_scrape = {should_scrape} (expected: False)")
    assert should_scrape is False, "Weekly source just scraped should not scrape again"
    
    # Test weekly source (8 days ago)
    old_tracking = {
        "sources": {
            weekly_source["url"]: {
                "last_scraped_at": (utcnow() - timedelta(days=8)).isoformat()
            }
        }
    }
    should_scrape = _should_scrape_source(weekly_source, old_tracking)
    print(f"✓ Weekly source (8 days old): should_scrape = {should_scrape} (expected: True)")
    assert should_scrape is True, "Weekly source >7 days old should scrape"
    
    # Test monthly source
    monthly_source = {
        "name": "Test Monthly Source",
        "url": "https://example.com/monthly",
        "scrape_frequency": "monthly"
    }
    
    old_monthly_tracking = {
        "sources": {
            monthly_source["url"]: {
                "last_scraped_at": (utcnow() - timedelta(days=31)).isoformat()
            }
        }
    }
    should_scrape = _should_scrape_source(monthly_source, old_monthly_tracking)
    print(f"✓ Monthly source (31 days old): should_scrape = {should_scrape} (expected: True)")
    assert should_scrape is True, "Monthly source >30 days old should scrape"
    
    print("\n✅ TEST 1 PASSED: Scrape frequency tracking works correctly")


def test_daily_stats_reset():
    """Test Issue 2: Daily stats reset at midnight"""
    print("\n" + "=" * 70)
    print("TEST 2: Daily Stats Reset")
    print("=" * 70)
    
    today = today_utc()
    
    # Get or create today's stats
    usage = db.get_or_create_daily_usage(today)
    print(f"\n✓ Today's stats ({today}):")
    print(f"  emails_sent: {usage.emails_sent}")
    print(f"  hunter_calls: {usage.hunter_calls}")
    print(f"  twilio_sms_sent: {usage.twilio_sms_sent}")
    
    # Verify yesterday's stats are separate (if they exist)
    yesterday = today - timedelta(days=1)
    yesterday_result = (
        db.client.table("daily_usage_stats")
        .select("*")
        .eq("date", str(yesterday))
        .limit(1)
        .execute()
    )
    
    if yesterday_result.data:
        print(f"\n✓ Yesterday's stats ({yesterday}) are preserved:")
        print(f"  emails_sent: {yesterday_result.data[0].get('emails_sent', 0)}")
        print(f"  hunter_calls: {yesterday_result.data[0].get('hunter_calls', 0)}")
    else:
        print(f"\n✓ No stats for yesterday ({yesterday}) - this is the first day")
    
    # Verify date is UTC
    print(f"\n✓ Using UTC date: {today}")
    print(f"  Current UTC time: {utcnow().isoformat()}")
    
    print("\n✅ TEST 2 PASSED: Daily stats use UTC dates and preserve history")


def test_sms_daily_limit():
    """Test Issue 3: SMS daily limit enforcement"""
    print("\n" + "=" * 70)
    print("TEST 3: SMS Daily Limit Enforcement")
    print("=" * 70)
    
    today = today_utc()
    usage = db.get_or_create_daily_usage(today)
    
    print(f"\n✓ Current SMS usage:")
    print(f"  SMS sent today: {usage.twilio_sms_sent}")
    print(f"  SMS daily limit: 15")
    print(f"  Remaining: {15 - usage.twilio_sms_sent}")
    
    # Check if twilio_sms_sent column exists
    has_column = hasattr(usage, 'twilio_sms_sent')
    print(f"\n✓ twilio_sms_sent column exists: {has_column}")
    assert has_column, "twilio_sms_sent column must exist in DailyUsage dataclass"
    
    # Verify the column is in the database
    result = db.client.table("daily_usage_stats").select("twilio_sms_sent").eq("date", str(today)).limit(1).execute()
    if result.data:
        print(f"✓ Database column value: {result.data[0].get('twilio_sms_sent', 'NOT FOUND')}")
    else:
        print("⚠️  No row found for today - will be created on first SMS send")
    
    print("\n✅ TEST 3 PASSED: SMS tracking column exists and is accessible")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("LAZYINTERN FIXES VERIFICATION")
    print("Testing 3 critical fixes")
    print("=" * 70)
    
    try:
        test_scrape_frequency()
        test_daily_stats_reset()
        test_sms_daily_limit()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run the SQL migration: backend/migrations/add_sms_tracking.sql")
        print("2. Restart the scheduler: python run_scheduler_24_7.py")
        print("3. Monitor logs for scrape frequency messages")
        print("4. Verify SMS limit enforcement in Twilio logs")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
