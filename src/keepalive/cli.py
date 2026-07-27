"""CLI: start, stop, status, run, setup, demo."""

import subprocess
import sys
import threading
import time
from typing import Any

import click

from keepalive.config import (
    DEFAULT_IDLE,
    DEFAULT_KEY,
    DEFAULT_METHOD,
    DEFAULT_SCHEDULE,
    KEY_CODES,
    LOG_FILE,
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
    perms = input_drv.check_permissions()
    missing = [k for k, v in perms.items() if not v]
    if missing:
        names = ", ".join(missing)
        fmt.error(f"Missing permissions: {names}")
        fmt.info("  Run: keepalive-cli setup")
        sys.exit(1)
    return perms


# ── commands (platform-independent, formatter + DI-driven) ───────────────────

# These receive injected dependencies via keyword-only arguments so they
# can be tested with FakeInput / FakeScheduler / CaptureFormatter.


def cmd_setup(
    *,
    input_drv: InputDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    if input_drv is None:
        input_drv = create_input_driver()
    if fmt is None:
        fmt = TextFormatter()

    if isinstance(fmt, JsonFormatter):
        perms = input_drv.check_permissions()
        ready = all(perms.values())
        fmt.result({"permissions": perms, "ready": ready})
        return

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
        click.echo()


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

    if isinstance(fmt, JsonFormatter):
        data: dict[str, Any] = {"running": running}
        if running:
            data["schedule"] = cfg.get("schedule", DEFAULT_SCHEDULE)
            data["idle"] = cfg.get("idle", DEFAULT_IDLE)
            data["method"] = method
            data["key"] = cfg.get("key", DEFAULT_KEY)
        fmt.result(data)
        return

    extra = f", key={cfg['key']}" if method in ("key", "both") and "key" in cfg else ""
    if running:
        fmt.success("keepalive-cli is running")
    else:
        fmt.info("🔴 keepalive-cli is not running")
    fmt.info(f"   schedule : {cfg.get('schedule', DEFAULT_SCHEDULE)}")
    fmt.info(f"   idle     : {cfg.get('idle', DEFAULT_IDLE)}s")
    fmt.info(f"   method   : {method}{extra}")


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


# ── demo ─────────────────────────────────────────────────────────────────────


def _demo_check_perms(input_drv: InputDriver, fmt: Formatter) -> None:
    perms = input_drv.check_permissions()
    if perms.get("accessibility"):
        fmt.success("Accessibility — granted")
    else:
        fmt.error("Accessibility — NOT granted")
        help_text = help_for_platform("accessibility")
        for line in help_text.split("\n"):
            fmt.info(f"  {line}")


def _demo_idle_live(input_drv: InputDriver) -> None:
    """Live idle counter — updates every second, Enter to stop."""
    click.echo("Watching idle time... (move mouse to reset, Enter to stop)")  # noqa: E501
    click.echo()
    stop = threading.Event()

    def _update() -> None:
        import shutil

        while not stop.is_set():
            idle = input_drv.idle_seconds()
            width = shutil.get_terminal_size().columns - 20
            bar = "#" * min(int(idle), width)
            print(
                f"\r  Idle: {idle:5.1f}s  {bar}",
                end="",
                flush=True,
            )
            time.sleep(1)

    t = threading.Thread(target=_update, daemon=True)
    t.start()
    try:
        input()
    except EOFError:
        pass
    stop.set()
    t.join(timeout=1)
    click.echo("\n")


def _demo_mouse_visible() -> None:
    """Draw a visible 50×50px square with the cursor."""
    import Quartz

    click.secho("Moving cursor in a 50×50px square in:", fg="yellow")
    for i in range(3, 0, -1):
        click.echo(f"  {i}...")
        time.sleep(1)

    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    x, y = int(pos.x), int(pos.y)
    size = 50

    for dx, dy in [(size, 0), (0, size), (-size, 0), (0, -size)]:
        steps = 10
        for step in range(steps):
            mx = x + dx * (step + 1) // steps
            my = y + dy * (step + 1) // steps
            move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (mx, my), 0)
            Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)
            time.sleep(0.01)
        x += dx
        y += dy

    click.secho("Done — cursor should have drawn a square", fg="green")


def _demo_key_visible() -> None:
    """Type a visible ● character in the active field."""
    click.secho("Will type '●' in the active field in:", fg="yellow")
    for i in range(3, 0, -1):
        click.echo(f"  {i}...")
        time.sleep(1)
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell app "System Events" to keystroke "●"',
        ],
        capture_output=True,
        timeout=5,
    )
    click.secho("Done — you should see '●' in the active field", fg="green")  # noqa: E501


def _demo_cycle(input_drv: InputDriver, fmt: Formatter) -> None:
    """Full cycle: idle → jiggle → verify reset."""
    fmt.info("Don't touch mouse/keyboard for 3 seconds...")
    time.sleep(3)
    before = input_drv.idle_seconds()
    fmt.info(f"Idle before: {before:.1f}s")
    input_drv.jiggle()
    time.sleep(0.2)
    after = input_drv.idle_seconds()
    fmt.info(f"Idle after:  {after:.1f}s")
    if after < before:
        fmt.success(f"Idle reset from {before:.1f}s → {after:.1f}s ✅")
    else:
        fmt.error("Idle did not reset. Check Accessibility permission.")


def _demo_scheduler(sched: SchedulerDriver, fmt: Formatter) -> None:
    if sched.is_running():
        fmt.success("Launchd agent: loaded")
    else:
        fmt.info("Launchd agent: not loaded")


def _demo_config(fmt: Formatter) -> None:
    cfg = load_settings()
    click.secho("Current Config:", fg="cyan", bold=True)
    rows = [
        ("schedule", cfg.get("schedule", DEFAULT_SCHEDULE)),
        ("idle", f"{cfg.get('idle', DEFAULT_IDLE)}s"),
        ("method", cfg.get("method", DEFAULT_METHOD)),
        ("key", cfg.get("key", DEFAULT_KEY)),
    ]
    w = max(len(k) for k, _v in rows)
    for k, v in rows:
        click.echo(f"  {k:<{w}}  {v}")


def _demo_log(fmt: Formatter) -> None:
    fmt.info(f"Log file: {LOG_FILE}")
    try:
        lines = LOG_FILE.read_text().splitlines()[-10:]
        if not lines:
            fmt.info("  (empty)")
        for line in lines:
            click.echo(f"  {line}")
    except Exception:
        fmt.info("  (unreadable)")


# Menu mapping: choice -> (label, handler)
_MENU = {
    "1": ("Check Accessibility permission", _demo_check_perms),
    "2": ("Show idle time — live counter", _demo_idle_live),
    "3": ("Test mouse movement — visible square", _demo_mouse_visible),
    "4": ("Test key press — visible character", _demo_key_visible),
    "5": ("Test full cycle — idle → jiggle → reset", _demo_cycle),
    "6": ("Scheduler status — launchd is_running", _demo_scheduler),
    "7": ("Show current config — settings.json", _demo_config),
    "8": ("Show log — location + tail", _demo_log),
}


def cmd_demo(  # noqa: C901 (menu dispatch is inherently branchy)
    *,
    input_drv: InputDriver | None = None,
    sched: SchedulerDriver | None = None,
    fmt: Formatter | None = None,
) -> None:
    if input_drv is None:
        input_drv = create_input_driver()
    if sched is None:
        sched = create_scheduler()
    if fmt is None:
        fmt = TextFormatter()

    if isinstance(fmt, JsonFormatter):
        fmt.result({"available": [label for label, _handler in _MENU.values()]})
        return

    while True:
        click.clear()
        click.secho("🧪 keepalive Demo", fg="cyan", bold=True)
        click.echo("─" * 36)
        for key, (label, _handler) in _MENU.items():
            click.echo(f"  {key}. {label}")
        click.echo("  0. Exit")
        click.echo()

        choice = click.prompt(
            "Choice",
            type=click.Choice(["0", "1", "2", "3", "4", "5", "6", "7", "8"]),
            default="0",
            show_default=False,
        )

        if choice == "0":
            fmt.success("Demo finished.")
            break

        _label, handler = _MENU[choice]

        # Some handlers use different signatures — dispatch accordingly
        if handler is _demo_check_perms:
            handler(input_drv, fmt)
        elif handler is _demo_idle_live:
            handler(input_drv)
        elif handler in (_demo_mouse_visible, _demo_key_visible):
            handler()
        elif handler is _demo_cycle:
            handler(input_drv, fmt)
        elif handler is _demo_scheduler:
            handler(sched, fmt)
        elif handler is _demo_config:
            handler(fmt)
        elif handler is _demo_log:
            handler(fmt)

        click.prompt("\nPress Enter to return to menu", default="", show_default=False)


# ── Click CLI layer ─────────────────────────────────────────────────────────


@click.group()
@click.option("--json", "json_mode", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(ctx: click.Context, json_mode: bool) -> None:
    """Keep macOS awake during work hours — stay green in messengers."""
    ctx.ensure_object(dict)
    ctx.obj["input_drv"] = create_input_driver()
    ctx.obj["sched"] = create_scheduler()
    ctx.obj["fmt"] = JsonFormatter() if json_mode else TextFormatter()


@cli.command()
@click.option("--schedule", default=DEFAULT_SCHEDULE, help="Active window")
@click.option("--idle", type=int, default=DEFAULT_IDLE, help="Idle threshold in seconds")
@click.option(
    "--method",
    type=click.Choice(["mouse", "key", "both"]),
    default=DEFAULT_METHOD,
    help="Activity method",
)
@click.option(
    "--key",
    type=click.Choice(list(KEY_CODES)),
    default=DEFAULT_KEY,
    help="Key to press",
)
@click.pass_context
def start(
    ctx: click.Context,
    schedule: str,
    idle: int,
    method: str,
    key: str,
) -> None:
    """Install and start the agent."""
    cmd_start(
        schedule,
        idle,
        method,
        key,
        sched=ctx.obj["sched"],
        input_drv=ctx.obj["input_drv"],
        fmt=ctx.obj["fmt"],
    )


@cli.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop and uninstall the agent."""
    cmd_stop(sched=ctx.obj["sched"], fmt=ctx.obj["fmt"])


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show agent status."""
    cmd_status(sched=ctx.obj["sched"], fmt=ctx.obj["fmt"])


@cli.command()
@click.option("--schedule", default=DEFAULT_SCHEDULE, help="Active window")
@click.option("--idle", type=int, default=DEFAULT_IDLE, help="Idle threshold in seconds")
@click.option(
    "--method",
    type=click.Choice(["mouse", "key", "both"]),
    default=DEFAULT_METHOD,
    help="Activity method",
)
@click.option(
    "--key",
    type=click.Choice(list(KEY_CODES)),
    default=DEFAULT_KEY,
    help="Key to press",
)
@click.pass_context
def run(
    ctx: click.Context,
    schedule: str,
    idle: int,
    method: str,
    key: str,
) -> None:
    """Run in foreground (Ctrl+C to stop)."""
    cmd_run(
        schedule,
        idle,
        method,
        key,
        input_drv=ctx.obj["input_drv"],
        fmt=ctx.obj["fmt"],
    )


@cli.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Interactive permission check and setup."""
    cmd_setup(input_drv=ctx.obj["input_drv"], fmt=ctx.obj["fmt"])


@cli.command()
@click.pass_context
def demo(ctx: click.Context) -> None:
    """Interactive test — verify drivers and permissions manually."""
    cmd_demo(
        input_drv=ctx.obj["input_drv"],
        sched=ctx.obj["sched"],
        fmt=ctx.obj["fmt"],
    )
