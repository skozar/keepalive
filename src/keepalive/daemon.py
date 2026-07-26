"""Daemon loop and input simulation functions."""

import random
import subprocess
import time
from datetime import datetime
from typing import cast

from keepalive.config import KEY_CODES, parse_schedule
from keepalive.log_config import log


def idle_seconds() -> float:
    """Seconds since last user input (keyboard or mouse)."""
    import Quartz

    return cast(
        float,
        Quartz.CGEventSourceSecondsSinceLastEventType(
            Quartz.kCGEventSourceStateCombinedSessionState,
            Quartz.kCGAnyInputEventType,
        ),
    )


def in_active_window(start_hour: int, end_hour: int, now: datetime | None = None) -> bool:
    """True if current hour is within [start_hour, end_hour)."""
    if now is None:
        now = datetime.now()
    return start_hour <= now.hour < end_hour


def jiggle() -> None:
    """Move cursor 1 px right and back — resets idle timer imperceptibly."""
    import Quartz

    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    x, y = int(pos.x), int(pos.y)

    move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x + 1, y), 0)
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)
    time.sleep(0.05)

    move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)


def press_key(key_name: str) -> None:
    """Press a function key via AppleScript — resets idle timer."""
    code = KEY_CODES.get(key_name)
    if code is None:
        log.error("Unknown key: %s", key_name)
        return
    subprocess.run(
        ["osascript", "-e", f'tell application "System Events" to key code {code}'],
        capture_output=True,
        timeout=5,
    )


def daemon(schedule: str, idle_threshold: int, method: str, key: str) -> None:
    """Run the main daemon loop — never returns."""
    start_hour, end_hour = parse_schedule(schedule)
    log.info(
        "Daemon started — %02d:00–%02d:00, idle %ds, method=%s, key=%s",
        start_hour,
        end_hour,
        idle_threshold,
        method,
        key,
    )

    while True:
        try:
            if in_active_window(start_hour, end_hour):
                idle = idle_seconds()
                if idle >= idle_threshold:
                    if method in ("mouse", "both"):
                        jiggle()
                    if method in ("key", "both"):
                        press_key(key)
                    log.info("Keepalive fired (method=%s, idle %.0fs)", method, idle)
                else:
                    log.info("Active (idle %.0fs), skipping", idle)
                time.sleep(random.randint(30, 60))
            else:
                time.sleep(300)
        except Exception:
            log.exception("Error — restarting loop in 30s")
            time.sleep(30)
