"""Trigger conditions — each returns True when keepalive should fire."""

from collections.abc import Callable

Condition = Callable[[], bool]


def combine_or(*conditions: Condition) -> Condition:
    """Return a condition that is True when **any** one is True."""
    return lambda: any(c() for c in conditions)
