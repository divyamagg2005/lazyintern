from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(log_dir, "last_run.log")
    
    # Configure logging with both console and file handlers
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_file, mode='w', encoding='utf-8')  # File output (overwrite each run)
        ]
    )
    
    # Suppress noisy third-party library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


logger = logging.getLogger("lazyintern")

