from __future__ import annotations

"""
Phase 0 scheduler helper.

Production scheduling is best handled by:
- Windows Task Scheduler (run `python -m scheduler.cycle_manager --once` 3x/day), or
- a cloud cron (GitHub Actions / Render / Railway), or
- a long-running process manager.

This file provides a simple "run forever" loop for local testing.
"""

import time

from scheduler.cycle_manager import run_cycle


def run_forever(interval_minutes: int = 60) -> None:
    while True:
        run_cycle()
        time.sleep(interval_minutes * 60)

