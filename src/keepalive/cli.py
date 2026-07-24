"""CLI: start, stop, status, run."""

import argparse
import json
import subprocess
import sys

from keepalive.config import (
    DEFAULT_SCHEDULE, DEFAULT_IDLE, DEFAULT_METHOD, DEFAULT_KEY,
    KEY_CODES, LAUNCHD_LABEL, LOG_FILE, PLIST_PATH,
    load_settings, save_settings,
)
from keepalive.daemon import daemon
from keepalive.log_config import log
from keepalive.plist import PLIST_TEMPLATE, binary_path


# ── JSON encoder helper ──────────────────────────────────────────────────────

def _status_json(running: bool, cfg: dict | None) -> str:
    """Return status as JSON string for --json output."""
    result: dict = {"running": running}
    if cfg and running:
        result["schedule"] = cfg.get("schedule", DEFAULT_SCHEDULE)
        result["idle"] = cfg.get("idle", DEFAULT_IDLE)
        result["method"] = cfg.get("method", DEFAULT_METHOD)
        result["key"] = cfg.get("key", DEFAULT_KEY)
    return json.dumps(result)


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_start(schedule: str, idle: int, method: str, key: str):
    """Install and start the launchd agent."""
    if PLIST_PATH.exists():
        print("⚠️  Agent already installed. Run 'keepalive-cli stop' first to reconfigure.")
        sys.exit(1)

    # Persist to settings.json so the GUI (or future runs) picks it up
    save_settings(schedule, idle, method, key)

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    plist_xml = PLIST_TEMPLATE.format(
        label=LAUNCHD_LABEL,
        binary=binary_path(),
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
    extra = f", key={key}" if method in ("key", "both") else ""
    print(f"✅ Agent started — schedule {schedule}, idle {idle}s, method={method}{extra}")
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


def cmd_status(json_output: bool = False):
    """Show agent status + current settings from settings.json."""
    try:
        result = subprocess.run(
            ["launchctl", "list", LAUNCHD_LABEL],
            capture_output=True, text=True,
        )
        running = result.returncode == 0 and result.stdout.strip()
    except FileNotFoundError:
        running = False

    cfg = load_settings()

    if json_output:
        print(_status_json(running, cfg))
        return

    if running:
        print("🟢 keepalive-cli is running")
    else:
        print("🔴 keepalive-cli is not running")

    method = cfg.get("method", DEFAULT_METHOD)
    extra = f", key={cfg['key']}" if method in ("key", "both") and "key" in cfg else ""
    print(f"   schedule : {cfg.get('schedule', DEFAULT_SCHEDULE)}")
    print(f"   idle     : {cfg.get('idle', DEFAULT_IDLE)}s")
    print(f"   method   : {method}{extra}")


def cmd_run(schedule: str, idle: int, method: str, key: str):
    """Run daemon in foreground for testing."""
    extra = f", key={key}" if method in ("key", "both") else ""
    print(f"🟢 Foreground mode — schedule {schedule}, idle {idle}s, method={method}{extra} (Ctrl+C to stop)")
    daemon(schedule, idle, method, key)


# ── shared args ──────────────────────────────────────────────────────────────

def _add_common_args(parser, defaults: dict | None = None):
    """Add --schedule/--idle/--method/--key with defaults from settings or hardcoded."""
    ds = defaults or {}
    schedule_default = ds.get("schedule", DEFAULT_SCHEDULE)
    idle_default = ds.get("idle", DEFAULT_IDLE)
    method_default = ds.get("method", DEFAULT_METHOD)
    key_default = ds.get("key", DEFAULT_KEY)

    parser.add_argument("--schedule", default=schedule_default,
                        help=f"Active window (default: {schedule_default})")
    parser.add_argument("--idle", type=int, default=idle_default,
                        help=f"Idle threshold in seconds (default: {idle_default})")
    parser.add_argument("--method", choices=("mouse", "key", "both"), default=method_default,
                        help=f"Activity method (default: {method_default})")
    parser.add_argument("--key", choices=list(KEY_CODES), default=key_default,
                        help=f"Key to press (default: {key_default})")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="keepalive-cli",
        description="Keep macOS awake during work hours — stays green in messengers (Slack, Teams, Discord).",
    )
    sub = parser.add_subparsers(dest="command", title="commands")

    # start — defaults from settings.json
    settings = load_settings()
    p_start = sub.add_parser("start", help="Install and start the launchd agent")
    _add_common_args(p_start, defaults=settings)

    # stop
    sub.add_parser("stop", help="Stop and uninstall the agent")

    # status
    p_status = sub.add_parser("status", help="Show agent status")
    p_status.add_argument("--json", action="store_true", help="Output in JSON format")

    # run — also from settings.json
    p_run = sub.add_parser("run", help="Run in foreground for testing (Ctrl+C to stop)")
    _add_common_args(p_run, defaults=settings)

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args.schedule, args.idle, args.method, args.key)
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "status":
        cmd_status(json_output=args.json)
    elif args.command == "run":
        cmd_run(args.schedule, args.idle, args.method, args.key)
    else:
        parser.print_help()
