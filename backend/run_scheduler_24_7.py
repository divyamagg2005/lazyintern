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
    Reset daily usage stats at midnight UTC.
    Creates a new row for the new date (keeps historical data).
    """
    logger.info("=" * 60)
    logger.info("Midnight UTC: Resetting daily usage stats")
    logger.info("=" * 60)
    try:
        today = today_utc()
        # get_or_create_daily_usage will create a new row for today if it doesn't exist
        # Old rows are preserved for historical tracking
        usage = db.get_or_create_daily_usage(today)
        logger.info(f"Daily stats initialized for {today}: emails_sent=0, hunter_calls=0, etc.")
        logger.info("Historical data preserved in previous date rows")
    except Exception as e:
        logger.error(f"Failed to reset daily stats: {e}", exc_info=True)
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
