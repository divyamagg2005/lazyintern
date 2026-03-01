from __future__ import annotations

import random
from datetime import timedelta

from core.config import settings
from core.supabase_db import db, today_utc, utcnow
from core.logger import logger


# Auto-approve ALL drafts after timeout (no score threshold)
TIMEOUT_HOURS = 2

# Add random delay for auto-approved emails to avoid spam detection
# Auto-approved emails will wait an additional 10-30 minutes after approval
AUTO_APPROVE_MIN_DELAY_MINUTES = 10
AUTO_APPROVE_MAX_DELAY_MINUTES = 30


def run_auto_approver() -> None:
    """
    DEPRECATED: This function is no longer needed as of the immediate-send fix.
    
    The system now approves and sends emails immediately after draft generation,
    eliminating the need for delayed auto-approval. This function is kept for
    backward compatibility but performs no operations.
    
    Previous behavior (now obsolete):
    - Found drafts with status 'generated' and approval_sent_at older than 2h
    - Auto-approved ALL drafts (no score threshold)
    - Added random delay (10-30 min) via approved_at timestamp
    
    The immediate approval flow (implemented in cycle_manager.py) makes this
    2-hour timeout mechanism obsolete. Drafts are now marked as 'approved'
    immediately upon creation with approved_at set to current time.
    """
    # No-op: immediate approval in cycle_manager.py makes this function obsolete
    return

