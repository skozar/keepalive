"""CLI: start, stop, status, run, setup."""

import argparse
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
from keepalive.formatters import (
    Formatter,
    JsonFormatter,
    TextFormatter,
)
from keepalive.log_config import log
from keepalive.permissions import help_for_platform
from keepalive.protocols import InputDriver, SchedulerDriver

# ── helpers ──────────────────────────────────────────────────────────────────


def _check_perms_or_die(input_drv: InputDriver, fmt: Formatter) -> dict[str, bool]:
    """Run a quick permission check.  Exit(1) when something is missing."""
    perms = input_drv.check_permissions()
    missing = [k for k, v in perms.items() if not v]
    if missing:
        names = ", ".join(missing)
        fmt.error(f"Missing permissions: {names}")
        fmt.info("  Run: keepalive-cli setup")
        sys.exit(1)
    return perms


# ── setup ────────────────────────────────────────────────────────────────────


def cmd_setup(
    *,
    input_drv: InputDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    """Interactive permission wizard.

    In text mode the user is guided through granting permissions. In JSON
    mode a single check is done and the result is printed.
    """
    if input_drv is None:
        input_drv = create_input_driver()
    if fmt is None:
        fmt = TextFormatter()

    # ── json mode: one-shot, no loop ──
    if isinstance(fmt, JsonFormatter):
        perms = input_drv.check_permissions()
        ready = all(perms.values())
        fmt.result({"permissions": perms, "ready": ready})
        return

    # ── interactive loop ──
    fmt.info("🔍 Checking permissions...\n")
    while True:
        perms = input_drv.check_permissions()
        missing = [(k, v) for k, v in perms.items() if not v]

        if not missing:
            fmt.info("✅ All permissions OK. Run: keepalive-cli start")
            fmt.result({"permissions": perms, "ready": True})
            break

        for name, _granted in missing:
            fmt.warning(f"{name} — not granted")
            help_text = help_for_platform(name)
            if help_text:
                for line in help_text.split("\n"):
                    fmt.info(f"     {line}")

        choice = fmt.prompt("\n  Press Enter to re-check, or 'q' to quit: ")
        if choice.lower() == "q":
            fmt.info("Setup aborted.")
            fmt.result({"permissions": perms, "ready": False})
            sys.exit(0)
        print()  # blank line between attempts


# ── start ────────────────────────────────────────────────────────────────────


def cmd_start(
    schedule: str,
    idle: int,
    method: str,
    key: str,
    *,
    sched: SchedulerDriver | None = None,
    input_drv: InputDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    if sched is None:
        sched = create_scheduler()
    if input_drv is None:
        input_drv = create_input_driver()
    if fmt is None:
        fmt = TextFormatter()

    if sched.is_running():
        fmt.error("Agent already installed. Run 'keepalive-cli stop' first to reconfigure.")
        fmt.result({"status": "already_installed"})
        sys.exit(1)

    _check_perms_or_die(input_drv, fmt)

    save_settings(schedule, idle, method, key)
    sched.install(
        binary=sys.argv[0],
        schedule=schedule,
        idle=idle,
        method=method,
        key=key,
    )

    extra = f", key={key}" if method in ("key", "both") else ""
    msg = f"Agent started — schedule {schedule}, idle {idle}s, method={method}{extra}"
    fmt.success(msg)
    fmt.info("   Logs: ~/Library/Logs/keepalive/")
    fmt.result(
        {
            "status": "installed",
            "schedule": schedule,
            "idle": idle,
            "method": method,
            "key": key,
        }
    )


# ── stop ─────────────────────────────────────────────────────────────────────


def cmd_stop(
    *,
    sched: SchedulerDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    if sched is None:
        sched = create_scheduler()
    if fmt is None:
        fmt = TextFormatter()

    if sched.is_running():
        sched.uninstall()
        log.info("Stopped and uninstalled")
        fmt.success("Agent stopped")
        fmt.result({"status": "stopped"})
    else:
        fmt.info("ℹ️  Agent is not installed")
        fmt.result({"status": "not_installed"})


# ── status ───────────────────────────────────────────────────────────────────


def cmd_status(
    *,
    sched: SchedulerDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    if sched is None:
        sched = create_scheduler()
    if fmt is None:
        fmt = TextFormatter()

    running = sched.is_running()
    cfg = load_settings()

    method = cfg.get("method", DEFAULT_METHOD)
    extra = f", key={cfg['key']}" if method in ("key", "both") and "key" in cfg else ""

    if isinstance(fmt, JsonFormatter):
        data: dict[str, Any] = {"running": running}
        if running:
            data["schedule"] = cfg.get("schedule", DEFAULT_SCHEDULE)
            data["idle"] = cfg.get("idle", DEFAULT_IDLE)
            data["method"] = method
            data["key"] = cfg.get("key", DEFAULT_KEY)
        fmt.result(data)
        return

    if running:
        fmt.success("keepalive-cli is running")
    else:
        fmt.info("🔴 keepalive-cli is not running")
    fmt.info(f"   schedule : {cfg.get('schedule', DEFAULT_SCHEDULE)}")
    fmt.info(f"   idle     : {cfg.get('idle', DEFAULT_IDLE)}s")
    fmt.info(f"   method   : {method}{extra}")


# ── run ──────────────────────────────────────────────────────────────────────


def cmd_run(
    schedule: str,
    idle: int,
    method: str,
    key: str,
    *,
    input_drv: InputDriver | None = None,
    daemon_fn: object = daemon,
    fmt: Formatter | None = None,
) -> None:
    if input_drv is None:
        input_drv = create_input_driver()
    if fmt is None:
        fmt = TextFormatter()

    _check_perms_or_die(input_drv, fmt)

    extra = f", key={key}" if method in ("key", "both") else ""
    fmt.info(
        f"🟢 Foreground mode — schedule {schedule}, idle {idle}s, "
        f"method={method}{extra} (Ctrl+C to stop)"
    )
    daemon_fn(schedule, idle, method, key, input_drv)  # type: ignore[operator]


# ── shared args ──────────────────────────────────────────────────────────────


def _add_common_args(
    parser: argparse.ArgumentParser, defaults: dict[str, Any] | None = None
) -> None:
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (non-interactive, for scripts/services)",
    )
    sub = parser.add_subparsers(dest="command", title="commands")

    # setup
    sub.add_parser("setup", help="Interactive permission check and setup")

    # start — defaults from settings.json
    settings = load_settings()
    p_start = sub.add_parser("start", help="Install and start the agent")
    _add_common_args(p_start, defaults=settings)

    # stop
    sub.add_parser("stop", help="Stop and uninstall the agent")

    # status
    sub.add_parser("status", help="Show agent status")
    # run
    p_run = sub.add_parser("run", help="Run in foreground (Ctrl+C to stop)")
    _add_common_args(p_run, defaults=settings)

    args = parser.parse_args()

    fmt: Formatter = JsonFormatter() if args.json else TextFormatter()

    if args.command == "setup":
        cmd_setup(fmt=fmt)
    elif args.command == "start":
        cmd_start(args.schedule, args.idle, args.method, args.key, fmt=fmt)
    elif args.command == "stop":
        cmd_stop(fmt=fmt)
    elif args.command == "status":
        cmd_status(fmt=fmt)
    elif args.command == "run":
        cmd_run(args.schedule, args.idle, args.method, args.key, fmt=fmt)
    else:
        parser.print_help()
