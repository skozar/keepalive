"""Schedule trigger — True when current time is inside the configured window."""

from datetime import datetime

Schedule = tuple[int, int]  # (start_hour, end_hour)


def in_active_window(hours: tuple[int, int], *, now: datetime | None = None) -> bool:
    """Return True when current time is inside [start_hour, end_hour).

    Accepts optional *now* for testing — defaults to ``datetime.now()``.
    """
    start_h, end_h = hours
    if now is None:
        now = datetime.now()
    current = now.hour
    if start_h <= end_h:
        return start_h <= current < end_h
    # overnight window, e.g. 22:00–02:00
    return current >= start_h or current < end_h
