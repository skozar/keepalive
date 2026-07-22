#!/usr/bin/env python3
"""Keep macOS "active" for Microsoft Teams during chosen hours.

Usage:
  keepalive start   [--schedule 04:00-12:00] [--idle 180] [--method mouse|key|both] [--key f13|f14|f15]
  keepalive stop
  keepalive status
  keepalive run     [--schedule 04:00-12:00] [--idle 180] [--method ...] [--key ...]

No subcommand → daemon mode (launched by launchd).
"""

import argparse
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import Quartz

# ── paths ──────────────────────────────────────────────────────────────────
APP_NAME = "keepalive"
LOG_DIR = Path.home() / "Library" / "Logs" / APP_NAME
LOG_FILE = LOG_DIR / "keepalive.log"
LAUNCHD_LABEL = "com.keepalive.jiggle"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"

# ── defaults ───────────────────────────────────────────────────────────────
DEFAULT_SCHEDULE = "04:00-12:00"
DEFAULT_IDLE = 180
DEFAULT_METHOD = "mouse"
DEFAULT_KEY = "f13"

# ── macOS key codes for function keys ──────────────────────────────────────
KEY_CODES = {
    "f13": 105,
    "f14": 106,
    "f15": 107,
}


# ═══════════════════════════════════════════════════════════════════════════
#  logging — rotating 5 × 1 MB, stored in ~/Library/Logs/keepalive/
# ═══════════════════════════════════════════════════════════════════════════

def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("keepalive")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")

    fh = RotatingFileHandler(str(LOG_FILE), maxBytes=1_000_000, backupCount=5)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


log = setup_logging()


# ═══════════════════════════════════════════════════════════════════════════
#  core helpers
# ═══════════════════════════════════════════════════════════════════════════

def parse_schedule(raw: str) -> tuple[int, int]:
    """Parse '04:00-12:00' → (4, 12)."""
    start_str, end_str = raw.split("-")
    return int(start_str.split(":")[0]), int(end_str.split(":")[0])


def idle_seconds() -> float:
    """Seconds since last user input (keyboard or mouse)."""
    return Quartz.CGEventSourceSecondsSinceLastEventType(
        Quartz.kCGEventSourceStateCombinedSessionState,
        Quartz.kCGAnyInputEventType,
    )


def in_active_window(start_hour: int, end_hour: int) -> bool:
    """True if current hour is within [start_hour, end_hour)."""
    hour = datetime.now().hour
    return start_hour <= hour < end_hour


def jiggle():
    """Move cursor 1 px right and back — resets idle timer imperceptibly."""
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    x, y = int(pos.x), int(pos.y)

    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x + 1, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)
    time.sleep(0.05)

    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)


def press_key(key_name: str):
    """Press a function key via AppleScript — resets idle timer."""
    code = KEY_CODES.get(key_name)
    if code is None:
        log.error("Unknown key: %s", key_name)
        return
    subprocess.run(
        ["osascript", "-e",
         f'tell application "System Events" to key code {code}'],
        capture_output=True,
        timeout=5,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  daemon loop — runs when launched by launchd (no subcommand)
# ═══════════════════════════════════════════════════════════════════════════

def daemon(schedule: str, idle_threshold: int, method: str, key: str):
    start_hour, end_hour = parse_schedule(schedule)
    log.info("Daemon started — %02d:00–%02d:00, idle %ds, method=%s, key=%s",
             start_hour, end_hour, idle_threshold, method, key)

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


# ═══════════════════════════════════════════════════════════════════════════
#  launchd plist template — created by `keepalive start`
# ═══════════════════════════════════════════════════════════════════════════

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{binary}</string>
        <string>--schedule</string>
        <string>{schedule}</string>
        <string>--idle</string>
        <string>{idle}</string>
        <string>--method</string>
        <string>{method}</string>
        <string>--key</string>
        <string>{key}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_file}</string>
    <key>StandardErrorPath</key>
    <string>{log_file}</string>
</dict>
</plist>
"""


def _binary_path() -> str:
    """Absolute path to this binary. Works for both python and PyInstaller."""
    return os.path.abspath(sys.argv[0])


# ═══════════════════════════════════════════════════════════════════════════
#  CLI commands
# ═══════════════════════════════════════════════════════════════════════════

def cmd_start(schedule: str, idle: int, method: str, key: str):
    """Install and start the launchd agent."""
    if PLIST_PATH.exists():
        print("⚠️  Agent already installed. Run 'keepalive stop' first to reconfigure.")
        sys.exit(1)

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    plist_xml = PLIST_TEMPLATE.format(
        label=LAUNCHD_LABEL,
        binary=_binary_path(),
        schedule=schedule,
        idle=str(idle),
        method=method,
        key=key,
        log_file=str(LOG_FILE),
    )
    PLIST_PATH.write_text(plist_xml)
    subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
    log.info("Installed and started — schedule %s, idle %ds, method=%s, key=%s",
             schedule, idle, method, key)
    print(f"✅ Agent started — schedule {schedule}, idle {idle}s, method={method}"
          + (f", key={key}" if method in ("key", "both") else ""))
    print(f"   Logs: {LOG_FILE}")


def cmd_stop():
    """Unload and remove the launchd agent."""
    if PLIST_PATH.exists():
        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
        PLIST_PATH.unlink()
        log.info("Stopped and uninstalled")
        print("✅ Agent stopped")
    else:
        print("ℹ️  Agent is not installed")


def _read_plist_config() -> dict | None:
    """Parse plist ProgramArguments into a {key: value} dict. None if no plist."""
    import plistlib
    if not PLIST_PATH.exists():
        return None
    with open(PLIST_PATH, "rb") as f:
        plist = plistlib.load(f)
    args = plist.get("ProgramArguments", [])
    cfg = {}
    for i, arg in enumerate(args):
        if arg.startswith("--") and i + 1 < len(args):
            cfg[arg.lstrip("-")] = args[i + 1]
    return cfg


def cmd_status():
    """Check if the launchd agent is loaded and show its configuration."""
    result = subprocess.run(
        ["launchctl", "list", LAUNCHD_LABEL],
        capture_output=True, text=True,
    )
    running = result.returncode == 0 and result.stdout.strip()

    cfg = _read_plist_config()
    if running:
        print("🟢 keepalive is running")
    else:
        print("🔴 keepalive is not running")

    if cfg:
        method = cfg.get("method", DEFAULT_METHOD)
        extra = f", key={cfg['key']}" if method in ("key", "both") and "key" in cfg else ""
        print(f"   schedule : {cfg.get('schedule', DEFAULT_SCHEDULE)}")
        print(f"   idle     : {cfg.get('idle', str(DEFAULT_IDLE))}s")
        print(f"   method   : {method}{extra}")
    elif running:
        print("   (plist not found — settings unknown)")


def cmd_run(schedule: str, idle: int, method: str, key: str):
    """Run daemon in foreground for testing."""
    extra = f", key={key}" if method in ("key", "both") else ""
    print(f"🟢 Foreground mode — schedule {schedule}, idle {idle}s, method={method}{extra} (Ctrl+C to stop)")
    daemon(schedule, idle, method, key)


# ═══════════════════════════════════════════════════════════════════════════
#  main — detect subcommand vs daemon mode
# ═══════════════════════════════════════════════════════════════════════════

def _add_common_args(parser):
    parser.add_argument("--schedule", default=DEFAULT_SCHEDULE)
    parser.add_argument("--idle", type=int, default=DEFAULT_IDLE)
    parser.add_argument("--method", choices=("mouse", "key", "both"), default=DEFAULT_METHOD)
    parser.add_argument("--key", choices=list(KEY_CODES), default=DEFAULT_KEY)


def main():
    subcommands = {"start", "stop", "status", "run"}
    is_subcommand = len(sys.argv) > 1 and sys.argv[1] in subcommands

    if is_subcommand:
        cmd = sys.argv[1]
        parser = argparse.ArgumentParser(prog=f"keepalive {cmd}")
        if cmd == "start":
            _add_common_args(parser)
            args = parser.parse_args(sys.argv[2:])
            cmd_start(args.schedule, args.idle, args.method, args.key)
        elif cmd == "stop":
            cmd_stop()
        elif cmd == "status":
            cmd_status()
        elif cmd == "run":
            _add_common_args(parser)
            args = parser.parse_args(sys.argv[2:])
            cmd_run(args.schedule, args.idle, args.method, args.key)
    else:
        parser = argparse.ArgumentParser(prog="keepalive")
        _add_common_args(parser)
        args = parser.parse_args(sys.argv[1:])
        daemon(args.schedule, args.idle, args.method, args.key)


if __name__ == "__main__":
    main()
