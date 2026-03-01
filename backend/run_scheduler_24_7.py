"""
LazyIntern 24/7 Scheduler
Runs pipeline cycles automatically every 2 hours
Resets daily usage stats at midnight UTC
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from scheduler.cycle_manager import run_cycle
from core.supabase_db import db, today_utc
from datetime import datetime, time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scheduled_cycle():
    """Wrapper for run_cycle with logging"""
    logger.info("=" * 60)
    logger.info("Starting scheduled pipeline cycle")
    logger.info("=" * 60)
    try:
        run_cycle()
        logger.info("Cycle completed successfully")
    except Exception as e:
        logger.error(f"Cycle failed with error: {e}", exc_info=True)
    logger.info("=" * 60)


def reset_daily_stats():
    """
    Verify daily usage stats for new day at midnight UTC.
    
    Note: Stats are automatically reset because each date gets its own row.
    When midnight hits, get_or_create_daily_usage() creates a fresh row
    with all counters at zero for the new date.
    
    This function just logs the transition and verifies the new row exists.
    """
    logger.info("=" * 60)
    logger.info("Midnight UTC: New day transition")
    logger.info("=" * 60)
    try:
        today = today_utc()
        # This will create a new row for today if it doesn't exist
        # (which it won't at midnight, so counters start at zero)
        usage = db.get_or_create_daily_usage(today)
        logger.info(f"Daily stats for {today}:")
        logger.info(f"  - emails_sent: {usage.emails_sent}/{usage.daily_limit}")
        logger.info(f"  - hunter_calls: {usage.hunter_calls}")
        logger.info(f"  - groq_calls: {usage.groq_calls}")
        logger.info(f"  - twilio_sms_sent: {usage.twilio_sms_sent}")
        logger.info("Previous day's data preserved in database for analytics")
    except Exception as e:
        logger.error(f"Failed to verify daily stats: {e}", exc_info=True)
    logger.info("=" * 60)


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # Run pipeline every 90 minutes (balanced discovery rate)
    scheduler.add_job(
        scheduled_cycle, 
        'interval', 
        minutes=90,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    # Reset daily stats at midnight UTC (00:00)
    scheduler.add_job(
        reset_daily_stats,
        'cron',
        hour=0,
        minute=0,
        timezone='UTC'
    )
    
    logger.info("=" * 60)
    logger.info("LazyIntern 24/7 Scheduler Started")
    logger.info("Pipeline will run every 90 minutes")
    logger.info("Daily stats reset at 00:00 UTC")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
