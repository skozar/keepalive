"""Constants, config schema, validation, persistence."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from keepalive.migrations import migrate as _migrate_config

APP_NAME = "keepalive"
LOG_DIR = Path.home() / "Library" / "Logs" / APP_NAME
LOG_FILE = LOG_DIR / "keepalive.log"
LAUNCHD_LABEL = "com.keepalive.jiggle"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
SETTINGS_PATH = Path.home() / ".config" / "keepalive" / "settings.json"

DEFAULT_SCHEDULE_FROM = "08:00"
DEFAULT_SCHEDULE_TO = "17:00"
DEFAULT_SCHEDULE = f"{DEFAULT_SCHEDULE_FROM}-{DEFAULT_SCHEDULE_TO}"
DEFAULT_IDLE = 180
DEFAULT_METHOD = "mouse"
DEFAULT_KEY = "f13"

KEY_CODES: dict[str, int] = {
    "f13": 105,
    "f14": 106,
    "f15": 107,
}

# ── schema ────────────────────────────────────────────────────────────────────

# All top-level keys that must be present.
REQUIRED_FIELDS = {"activity", "caffeinate", "triggers"}

DEFAULTS: dict[str, Any] = {
    "schema_version": 1,
    "activity": {
        "idle": DEFAULT_IDLE,
        "method": DEFAULT_METHOD,
        "key": DEFAULT_KEY,
    },
    "caffeinate": {
        "enabled": False,
        "mode": "display",  # "display" | "system"
        "lid_closed": False,
    },
    "triggers": {
        "schedule": {
            "enabled": True,
            "from": DEFAULT_SCHEDULE_FROM,
            "to": DEFAULT_SCHEDULE_TO,
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

METHODS = {"mouse", "key", "both", "boost"}
CAFFEINATE_MODES = {"display", "system"}
TRIGGER_ACTIONS = {"start", "stop", "schedule"}

SCHEDULE_RE = re.compile(r"^\d{2}:\d{2}$")


def _fail(msg: str) -> str:
    return msg


# ── validation ─────────────────────────────────────────────────────────────────


def validate_config(data: dict[str, Any]) -> list[str]:  # noqa: C901 (comprehensive validation)
    """Check that *data* is a full, valid config dict.  Returns a list of
    human-readable error strings (empty list == valid)."""
    errors: list[str] = []

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"Missing required fields: {', '.join(sorted(missing))}")
        return errors  # can't validate deeper

    # --- activity ---
    act = data.get("activity", {})
    if not isinstance(act, dict):
        errors.append("activity: must be an object")
    else:
        for key in ("idle", "method", "key"):
            if key not in act:
                errors.append(f"activity.{key}: missing")
        if "idle" in act and not isinstance(act["idle"], int):
            errors.append("activity.idle: must be integer")
        if "idle" in act and isinstance(act["idle"], int) and not (10 <= act["idle"] <= 3600):
            errors.append("activity.idle: must be 10–3600")
        if "method" in act and act["method"] not in METHODS:
            errors.append(f"activity.method: must be one of {sorted(METHODS)}")
        if "key" in act and act["key"] not in KEY_CODES:
            errors.append(f"activity.key: must be one of {sorted(KEY_CODES)}")

    # --- caffeinate ---
    caf = data.get("caffeinate", {})
    if not isinstance(caf, dict):
        errors.append("caffeinate: must be an object")
    else:
        for key in ("enabled", "mode", "lid_closed"):
            if key not in caf:
                errors.append(f"caffeinate.{key}: missing")
        if "enabled" in caf and not isinstance(caf["enabled"], bool):
            errors.append("caffeinate.enabled: must be boolean")
        if "mode" in caf and caf["mode"] not in CAFFEINATE_MODES:
            errors.append(f"caffeinate.mode: must be one of {sorted(CAFFEINATE_MODES)}")
        if "lid_closed" in caf and not isinstance(caf["lid_closed"], bool):
            errors.append("caffeinate.lid_closed: must be boolean")

    # --- triggers ---
    trig = data.get("triggers", {})
    if not isinstance(trig, dict):
        errors.append("triggers: must be an object")
    else:
        for section in ("schedule", "wifi", "app"):
            obj = trig.get(section, {})
            if not isinstance(obj, dict):
                errors.append(f"triggers.{section}: must be an object")
                continue
            if "enabled" not in obj:
                errors.append(f"triggers.{section}.enabled: missing")
            elif not isinstance(obj["enabled"], bool):
                errors.append(f"triggers.{section}.enabled: must be boolean")

        # schedule
        sch = trig.get("schedule", {})
        if isinstance(sch, dict):
            for sub in ("from", "to"):
                if sub not in sch:
                    errors.append(f"triggers.schedule.{sub}: missing")
                elif not isinstance(sch[sub], str) or not SCHEDULE_RE.match(sch[sub]):
                    errors.append(f"triggers.schedule.{sub}: must be HH:MM")

        # wifi
        wf = trig.get("wifi", {})
        if isinstance(wf, dict):
            if "ssids" not in wf:
                errors.append("triggers.wifi.ssids: missing")
            elif not isinstance(wf["ssids"], list) or not all(
                isinstance(x, str) for x in wf["ssids"]
            ):
                errors.append("triggers.wifi.ssids: must be list of strings")
            if "on_match" in wf and wf["on_match"] not in TRIGGER_ACTIONS:
                errors.append(f"triggers.wifi.on_match: must be one of {sorted(TRIGGER_ACTIONS)}")
            if "on_lost" in wf and wf["on_lost"] not in TRIGGER_ACTIONS:
                errors.append(f"triggers.wifi.on_lost: must be one of {sorted(TRIGGER_ACTIONS)}")

        # app
        ap = trig.get("app", {})
        if isinstance(ap, dict):
            if "apps" not in ap:
                errors.append("triggers.app.apps: missing")
            elif not isinstance(ap["apps"], list) or not all(
                isinstance(x, str) for x in ap["apps"]
            ):
                errors.append("triggers.app.apps: must be list of strings")
            if "on_active" in ap and ap["on_active"] not in TRIGGER_ACTIONS:
                errors.append(f"triggers.app.on_active: must be one of {sorted(TRIGGER_ACTIONS)}")
            if "on_inactive" in ap and ap["on_inactive"] not in TRIGGER_ACTIONS:
                errors.append(f"triggers.app.on_inactive: must be one of {sorted(TRIGGER_ACTIONS)}")

    return errors


# ── persistence ────────────────────────────────────────────────────────────────


def load_settings() -> dict[str, Any]:
    """Read settings.json, migrate old formats, merge with defaults."""
    if not SETTINGS_PATH.exists():
        return DEFAULTS

    try:
        raw: Any = json.loads(SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, OSError):  # fmt: skip
        return DEFAULTS

    if not isinstance(raw, dict):
        return DEFAULTS

    # --- migrate if needed ---
    raw = _migrate_config(raw)

    # --- deep-merge with defaults for any missing keys ---
    merged = _deep_merge(DEFAULTS, raw)
    return merged


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *overrides* into *defaults*."""
    result: dict[str, Any] = {}
    for key in set(defaults.keys()) | set(overrides.keys()):
        if key in overrides:
            val = overrides[key]
            if key in defaults and isinstance(defaults[key], dict) and isinstance(val, dict):  # noqa: E501
                result[key] = _deep_merge(defaults[key], val)
            else:
                result[key] = val
        else:
            result[key] = defaults[key]
    return result


def write_config(data: dict[str, Any]) -> list[str]:
    """Validate *data* and write it to settings.json.

    Returns a list of errors (empty == success, file written)."""
    errors = validate_config(data)
    if errors:
        return errors
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    return []


# ── system sleep (macOS) ───────────────────────────────────────────────────────


def get_system_sleep() -> int | None:
    """Read system sleep timeout in seconds from pmset.  macOS only."""
    import platform

    if platform.system() != "Darwin":
        return None
    try:
        out = subprocess.run(
            ["pmset", "-g"],
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout
        for line in out.splitlines():
            if "sleep" in line.lower() and "displaysleep" not in line.lower():
                parts = line.strip().split()
                for p in parts:
                    try:
                        return int(p) * 60  # pmset returns minutes
                    except ValueError:
                        continue
    except Exception:
        pass
    return None


def save_settings(schedule: str, idle: int, method: str, key: str) -> None:
    """Write key settings — legacy API used by cmd_start.  Merges with
    existing config rather than overwriting everything."""
    cfg = load_settings()
    parts = schedule.split("-", 1)
    cfg["triggers"]["schedule"]["from"] = parts[0] if parts else "08:00"
    cfg["triggers"]["schedule"]["to"] = parts[1] if len(parts) > 1 else "17:00"
    cfg["activity"]["idle"] = idle
    cfg["activity"]["method"] = method
    cfg["activity"]["key"] = key
    write_config(cfg)


# ── helpers (kept for backward compat in daemon / cli) ─────────────────────────


def parse_schedule(from_str: str, to_str: str | None = None) -> tuple[int, int]:
    """Parse '08:00', '17:00' → (8, 17)  OR  '08:00-17:00' → (8, 17)."""
    if to_str is None:
        # legacy single-string format
        parts = from_str.split("-", 1)
        from_str, to_str = parts[0], parts[1] if len(parts) > 1 else "17:00"
    return int(from_str.split(":")[0]), int(to_str.split(":")[0])


# Convenience accessors so existing code (daemon, cli) doesn't break
# while we transition triggers into trigger modules.


def activity_idle(cfg: dict[str, Any]) -> int:
    return int(cfg.get("activity", {}).get("idle", DEFAULT_IDLE))


def activity_method(cfg: dict[str, Any]) -> str:
    return str(cfg.get("activity", {}).get("method", DEFAULT_METHOD))


def activity_key(cfg: dict[str, Any]) -> str:
    return str(cfg.get("activity", {}).get("key", DEFAULT_KEY))


def schedule_enabled(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("triggers", {}).get("schedule", {}).get("enabled", True))


def schedule_hours(cfg: dict[str, Any]) -> tuple[int, int]:
    sch = cfg.get("triggers", {}).get("schedule", {})
    return parse_schedule(
        str(sch.get("from", DEFAULT_SCHEDULE_FROM)),
        str(sch.get("to", DEFAULT_SCHEDULE_TO)),
    )  # noqa: E501
