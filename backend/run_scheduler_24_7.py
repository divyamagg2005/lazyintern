"""
LazyIntern 24/7 Scheduler
Runs pipeline cycles automatically every 2 hours
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from scheduler.cycle_manager import run_cycle
from datetime import datetime
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

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    # Run every 2 hours
    scheduler.add_job(
        scheduled_cycle, 
        'interval', 
        hours=2,
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    logger.info("=" * 60)
    logger.info("LazyIntern 24/7 Scheduler Started")
    logger.info("Pipeline will run every 2 hours")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
