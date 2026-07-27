"""Linear config migrations.

Each migration is a pure function: old_dict → new_dict.
Schema version stored in config["schema_version"]; missing means 0.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from keepalive.config import DEFAULTS  # noqa: F401

CURRENT_SCHEMA = 1

# ── v0.7 / v0.8 defaults (kept here to avoid circular import with config.py) ──
_DEFAULT_IDLE = 180
_DEFAULT_METHOD = "mouse"
_DEFAULT_KEY = "f13"
_DEFAULT_SCHEDULE_FROM = "09:00"
_DEFAULT_SCHEDULE_TO = "18:00"


def _migrate_0_to_1(raw: dict[str, Any]) -> dict[str, Any]:
    """v0.7/v0.8 flat format → v0.10 nested format.

    Already-nested configs pass through unchanged.
    """
    # Already nested — nothing to do.
    if "activity" in raw or "triggers" in raw:
        return raw

    idle = raw.get("idle", _DEFAULT_IDLE)
    method = raw.get("method", _DEFAULT_METHOD)
    key = raw.get("key", _DEFAULT_KEY)
    sched_from = raw.get("schedule_from", _DEFAULT_SCHEDULE_FROM)
    sched_to = raw.get("schedule_to", _DEFAULT_SCHEDULE_TO)
    return {
        "activity": {"idle": idle, "method": method, "key": key},
        "caffeinate": {
            "enabled": False,
            "mode": "display",
            "lid_closed": False,
        },
        "triggers": {
            "schedule": {
                "enabled": True,
                "from": sched_from,
                "to": sched_to,
            },
            "wifi": {
                "enabled": False,
                "ssids": [],
                "on_match": "start",
                "on_lost": "stop",
            },
            "app": {
                "enabled": False,
                "apps": [],
                "on_active": "start",
                "on_inactive": "schedule",
            },
        },
    }


MIGRATIONS: list[Callable[[dict[str, Any]], dict[str, Any]]] = [
    _migrate_0_to_1,
]


def migrate(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply any pending migrations to *raw*.

    Returns the migrated dict.  Does NOT write to disk — caller
    should persist the result.
    """
    version = raw.get("schema_version", 0)
    for v in range(version, CURRENT_SCHEMA):
        raw = MIGRATIONS[v](raw)
        raw["schema_version"] = v + 1
    return raw
