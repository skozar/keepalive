"""CLI: start, stop, status, run."""

import argparse
import json
import sys
from typing import Any

from keepalive.config import (
    DEFAULT_IDLE,
    DEFAULT_KEY,
    DEFAULT_METHOD,
    DEFAULT_SCHEDULE,
    KEY_CODES,
    load_settings,
    save_settings,
)
from keepalive.daemon import daemon
from keepalive.drivers.factory import create_input_driver, create_scheduler
from keepalive.log_config import log
from keepalive.protocols import InputDriver, SchedulerDriver

# ── JSON encoder helper ──────────────────────────────────────────────────────


def _status_json(running: bool, cfg: dict[str, Any] | None) -> str:
    """Return status as JSON string for --json output."""
    result: dict[str, Any] = {"running": running}
    if cfg and running:
        result["schedule"] = cfg.get("schedule", DEFAULT_SCHEDULE)
        result["idle"] = cfg.get("idle", DEFAULT_IDLE)
        result["method"] = cfg.get("method", DEFAULT_METHOD)
        result["key"] = cfg.get("key", DEFAULT_KEY)
    return json.dumps(result)


# ── commands ─────────────────────────────────────────────────────────────────


def cmd_start(
    schedule: str,
    idle: int,
    method: str,
    key: str,
    *,
    sched: SchedulerDriver | None = None,
) -> None:
    """Install and start the OS-level scheduler agent."""
    if sched is None:
        sched = create_scheduler()

    if sched.is_running():
        print("⚠️  Agent already installed. Run 'keepalive-cli stop' first to reconfigure.")
        sys.exit(1)

    save_settings(schedule, idle, method, key)
    sched.install(binary=sys.argv[0], schedule=schedule, idle=idle, method=method, key=key)

    extra = f", key={key}" if method in ("key", "both") else ""
    print(f"✅ Agent started — schedule {schedule}, idle {idle}s, method={method}{extra}")


def cmd_stop(*, sched: SchedulerDriver | None = None) -> None:
    """Unload and remove the OS-level scheduler agent."""
    if sched is None:
        sched = create_scheduler()

    if sched.is_running():
        sched.uninstall()
        log.info("Stopped and uninstalled")
        print("✅ Agent stopped")
    else:
        print("ℹ️  Agent is not installed")


def cmd_status(
    json_output: bool = False,
    *,
    sched: SchedulerDriver | None = None,
) -> None:
    """Show agent status + current settings from settings.json."""
    if sched is None:
        sched = create_scheduler()

    running = sched.is_running()
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


def cmd_run(
    schedule: str,
    idle: int,
    method: str,
    key: str,
    *,
    input_drv: InputDriver | None = None,
    daemon_fn: object = daemon,
) -> None:
    """Run daemon in foreground for testing."""
    if input_drv is None:
        input_drv = create_input_driver()

    extra = f", key={key}" if method in ("key", "both") else ""
    print(
        f"🟢 Foreground mode — schedule {schedule}, idle {idle}s, "
        f"method={method}{extra} (Ctrl+C to stop)"
    )
    daemon_fn(schedule, idle, method, key, input_drv)  # type: ignore[operator]


# ── shared args ──────────────────────────────────────────────────────────────


def _add_common_args(
    parser: argparse.ArgumentParser, defaults: dict[str, Any] | None = None
) -> None:
    """Add --schedule/--idle/--method/--key."""
    ds: dict[str, Any] = defaults if defaults is not None else {}
    schedule_default = ds.get("schedule", DEFAULT_SCHEDULE)
    idle_default = ds.get("idle", DEFAULT_IDLE)
    method_default = ds.get("method", DEFAULT_METHOD)
    key_default = ds.get("key", DEFAULT_KEY)

    parser.add_argument(
        "--schedule",
        default=schedule_default,
        help=f"Active window (default: {schedule_default})",
    )
    parser.add_argument(
        "--idle",
        type=int,
        default=idle_default,
        help=f"Idle threshold in seconds (default: {idle_default})",
    )
    parser.add_argument(
        "--method",
        choices=("mouse", "key", "both"),
        default=method_default,
        help=f"Activity method (default: {method_default})",
    )
    parser.add_argument(
        "--key",
        choices=list(KEY_CODES),
        default=key_default,
        help=f"Key to press (default: {key_default})",
    )


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="keepalive-cli",
        description=(
            "Keep macOS awake during work hours — stays green in messengers "
            "(Slack, Teams, Discord)."
        ),
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
