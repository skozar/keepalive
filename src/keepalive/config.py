"""Constants, defaults, and pure helpers."""

from pathlib import Path

APP_NAME = "keepalive"
LOG_DIR = Path.home() / "Library" / "Logs" / APP_NAME
LOG_FILE = LOG_DIR / "keepalive.log"
LAUNCHD_LABEL = "com.keepalive.jiggle"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"

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
