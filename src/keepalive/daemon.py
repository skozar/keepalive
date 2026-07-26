"""Daemon loop — platform-independent (depends only on InputDriver protocol)."""

import random
import time
from datetime import datetime

from keepalive.config import parse_schedule
from keepalive.log_config import log
from keepalive.protocols import InputDriver


def in_active_window(start_hour: int, end_hour: int, now: datetime | None = None) -> bool:
    """True if current hour is within [start_hour, end_hour)."""
    if now is None:
        now = datetime.now()
    return start_hour <= now.hour < end_hour


def daemon(
    schedule: str,
    idle_threshold: int,
    method: str,
    key: str,
    input_drv: InputDriver,
    *,
    max_iterations: int | None = None,
) -> None:
    """Run the main daemon loop.

    *max_iterations* is for testing only — the production path
    calls ``daemon(..., max_iterations=None)`` which runs forever.
    """
    start_hour, end_hour = parse_schedule(schedule)
    log.info(
        "Daemon started — %02d:00–%02d:00, idle %ds, method=%s, key=%s",
        start_hour,
        end_hour,
        idle_threshold,
        method,
        key,
    )

    iteration = 0
    while True:
        if max_iterations is not None and iteration >= max_iterations:
            break
        iteration += 1

        try:
            if in_active_window(start_hour, end_hour):
                idle = input_drv.idle_seconds()
                if idle >= idle_threshold:
                    if method in ("mouse", "both"):
                        input_drv.jiggle()
                    if method in ("key", "both"):
                        input_drv.press_key(key)
                    log.info("Keepalive fired (method=%s, idle %.0fs)", method, idle)
                else:
                    log.info("Active (idle %.0fs), skipping", idle)
                time.sleep(random.randint(30, 60))
            else:
                time.sleep(300)
        except Exception:
            log.exception("Error — restarting loop in 30s")
            time.sleep(30)
