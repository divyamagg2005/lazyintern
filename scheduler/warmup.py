from __future__ import annotations

from datetime import date


def get_daily_limit(account_created_date: date, today: date) -> int:
    """
    Simple warmup schedule from final_pipeline.md.
    """
    days_active = (today - account_created_date).days
    if days_active <= 3:
        return 5
    if days_active <= 7:
        return 8
    if days_active <= 11:
        return 12
    return 15

