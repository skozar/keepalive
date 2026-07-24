"""Constants, defaults, and pure helpers."""

import json
from pathlib import Path

APP_NAME = "keepalive"
LOG_DIR = Path.home() / "Library" / "Logs" / APP_NAME
LOG_FILE = LOG_DIR / "keepalive.log"
LAUNCHD_LABEL = "com.keepalive.jiggle"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
SETTINGS_PATH = Path.home() / ".config" / "keepalive" / "settings.json"

DEFAULT_SCHEDULE = "08:00-17:00"
DEFAULT_IDLE = 180
DEFAULT_METHOD = "mouse"
DEFAULT_KEY = "f13"

KEY_CODES = {
    "f13": 105,
    "f14": 106,
    "f15": 107,
}


def parse_schedule(raw: str) -> tuple[int, int]:
    """Parse '04:00-12:00' → (4, 12)."""
    start_str, end_str = raw.split("-")
    return int(start_str.split(":")[0]), int(end_str.split(":")[0])


def load_settings() -> dict:
    """Read ~/.config/keepalive/settings.json, merge with defaults.

    GUI wrote schedule_from/schedule_to (e.g. "08:00", "17:00").
    We merge them into the internal ``schedule`` format ``"08:00-17:00"``.
    """
    defaults = {
        "schedule": DEFAULT_SCHEDULE,
        "idle": DEFAULT_IDLE,
        "method": DEFAULT_METHOD,
        "key": DEFAULT_KEY,
    }
    if not SETTINGS_PATH.exists():
        return defaults

    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return defaults

    # GUI format: schedule_from + schedule_to
    if "schedule_from" in data and "schedule_to" in data:
        defaults["schedule"] = f"{data['schedule_from']}-{data['schedule_to']}"
    elif "schedule" in data:
        defaults["schedule"] = data["schedule"]

    for key in ("idle", "method", "key"):
        if key in data:
            defaults[key] = data[key]

    return defaults


def save_settings(schedule: str, idle: int, method: str, key: str) -> None:
    """Write settings to ~/.config/keepalive/settings.json in GUI-compatible format."""
    parts = schedule.split("-", 1)
    schedule_from = parts[0] if len(parts) > 0 else "08:00"
    schedule_to = parts[1] if len(parts) > 1 else "17:00"

    data = {
        "schedule_from": schedule_from,
        "schedule_to": schedule_to,
        "idle": idle,
        "method": method,
        "key": key,
    }
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n")
