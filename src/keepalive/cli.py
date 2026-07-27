"""CLI: start, stop, status, run, setup, demo."""

import json
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from keepalive.config import (
    CAFFEINATE_MODES,
    DEFAULT_IDLE,
    DEFAULT_KEY,
    DEFAULT_METHOD,
    DEFAULT_SCHEDULE,
    KEY_CODES,
    LOG_FILE,
    METHODS,
    get_system_sleep,
    load_settings,
    save_settings,
    write_config,
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


# ── trigger conditions builder ────────────────────────────────────────────


def _build_conditions(cfg: dict[str, Any]) -> list[Callable[[], bool]]:
    """Assemble OR-conditions from the triggers section of the config."""
    from keepalive.triggers.app import get_running_apps
    from keepalive.triggers.schedule import in_active_window as _schedule_check
    from keepalive.triggers.wifi import get_current_ssid

    conditions: list[Callable[[], bool]] = []
    triggers = cfg.get("triggers", {})

    sch = triggers.get("schedule", {})
    if sch.get("enabled", True):
        hours = (
            int(str(sch.get("from", "08:00")).split(":")[0]),
            int(str(sch.get("to", "17:00")).split(":")[0]),
        )

        def _sched() -> bool:
            return _schedule_check(hours)

        conditions.append(_sched)

    wf = triggers.get("wifi", {})
    if wf.get("enabled") and wf.get("ssids"):
        target_ssids = set(str(s) for s in wf["ssids"])

        def _wifi() -> bool:
            ssid = get_current_ssid()
            return ssid is not None and ssid in target_ssids

        conditions.append(_wifi)

    ap = triggers.get("app", {})
    if ap.get("enabled") and ap.get("apps"):
        target_apps = set(str(a) for a in ap["apps"])

        def _app() -> bool:
            running = set(get_running_apps())
            return bool(running & target_apps)

        conditions.append(_app)

    return conditions


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

    # --- idle vs system sleep warning ---
    sys_sleep = get_system_sleep()
    if sys_sleep and idle > sys_sleep:
        fmt.warning(
            f"idle ({idle}s) > system sleep ({sys_sleep}s / {sys_sleep // 60}min) — "
            "agent may miss before sleep. Enable Caffeinate: "
            "keepalive-cli config setup"
        )

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

    # --- build conditions from config ---
    cfg = load_settings()
    conditions = _build_conditions(cfg)

    # --- caffeinate ---
    caf = cfg.get("caffeinate", {})
    caf_mode: str | None = None
    if caf.get("enabled"):
        caf_mode = str(caf.get("mode", "display"))

    # --- idle vs system sleep warning ---
    sys_sleep = get_system_sleep()
    if sys_sleep and idle > sys_sleep:
        fmt.warning(
            f"idle ({idle}s) > system sleep ({sys_sleep}s / {sys_sleep // 60}min) — "
            "agent may miss before sleep. Enable Caffeinate: "
            "keepalive-cli config setup"
        )

    extra = f", key={key}" if method in ("key", "both") else ""
    fmt.info(
        f"🟢 Foreground mode — schedule {schedule}, idle {idle}s, "
        f"method={method}{extra} (Ctrl+C to stop)"
    )
    daemon_fn(idle, method, key, input_drv, conditions=conditions, caffeinate_mode=caf_mode)  # type: ignore[operator]


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


# ── config commands ────────────────────────────────────────────────────────


def _edit_str(label: str, default: str) -> str:
    import questionary

    return questionary.text(f"{label}:", default=default).ask() or default


def _edit_int(label: str, default: int, min_v: int = 10, max_v: int = 3600) -> int:
    import questionary

    while True:
        raw = questionary.text(f"{label} [{min_v}–{max_v}]:", default=str(default)).ask()
        try:
            val = int(raw)
            if min_v <= val <= max_v:
                return val
        except TypeError, ValueError:
            pass


def _select_one(label: str, choices: list[str], default: str) -> str:
    import questionary

    return questionary.select(label, choices=choices, default=default).ask() or default


def _select_checkbox(label: str, choices: list[str], defaults: list[str]) -> list[str]:
    import questionary

    styled = [questionary.Choice(c, checked=c in defaults) for c in choices]
    return questionary.checkbox(label, choices=styled).ask() or []


def _autocomplete(label: str, choices: list[str], default: str = "") -> str:
    import questionary

    result = questionary.autocomplete(label, choices=choices, default=default).ask()
    return result or default


def cmd_config_setup(*, fmt: Formatter | None = None) -> None:  # noqa: C901 (dashboard UI)
    """Interactive configuration dashboard using questionary."""
    import questionary

    if fmt is None:
        fmt = TextFormatter()

    if isinstance(fmt, JsonFormatter):
        fmt.result({"available": False, "reason": "interactive only"})
        return

    cfg = load_settings()

    while True:
        # --- read current state ---
        sys_sleep = get_system_sleep()
        idle = cfg["activity"]["idle"]
        method = cfg["activity"]["method"]
        key_ = cfg["activity"]["key"]
        caf_enabled = cfg["caffeinate"]["enabled"]
        caf_mode = cfg["caffeinate"]["mode"]
        lid = cfg["caffeinate"]["lid_closed"]
        sch_enabled = cfg["triggers"]["schedule"]["enabled"]
        sch_from = cfg["triggers"]["schedule"]["from"]
        sch_to = cfg["triggers"]["schedule"]["to"]
        wifi_enabled = cfg["triggers"]["wifi"]["enabled"]
        wifi_ssids = cfg["triggers"]["wifi"]["ssids"]
        app_enabled = cfg["triggers"]["app"]["enabled"]
        app_apps = cfg["triggers"]["app"]["apps"]

        # --- build menu ---
        sections: list[dict[str, str]] = [
            {"name": "⚙️  ACTIVITY — how keepalive simulates input", "value": "activity"},
            {"name": "🔋 POWER — sleep prevention", "value": "power"},
            {"name": "⏰ TRIGGERS — when keepalive fires", "value": "triggers"},
            {"name": "💾 Save & Exit", "value": "save"},
            {"name": "Exit without saving", "value": "exit"},
        ]

        click.clear()
        click.secho("keepalive configuration", fg="cyan", bold=True)
        click.echo("─" * 40)

        # ACTIVITY summary
        warns = ""
        if sys_sleep and idle > sys_sleep:
            warns = click.style(
                f"  ⚠ idle > system sleep ({sys_sleep // 60} min) — may miss!", fg="red"
            )
        click.echo(f"  Idle:       {idle}s{warns}")
        click.echo(f"  Method:     {method}")
        click.echo(f"  Key:        {key_}")
        click.echo()

        # POWER summary
        status = "enabled" if caf_enabled else "disabled"
        lid_str = " + lid-closed" if lid else ""
        click.echo(f"  Caffeinate: {status} ({caf_mode}{lid_str})")
        click.echo()

        # TRIGGERS summary
        sch_str = f"{sch_from}–{sch_to}" if sch_enabled else "disabled"
        click.echo(f"  Schedule:   {sch_str}")
        wf_str = ", ".join(wifi_ssids) if wifi_ssids else "no networks"
        click.echo(f"  WiFi:       {'enabled' if wifi_enabled else 'disabled'} ({wf_str})")
        ap_str = ", ".join(app_apps[:3]) if app_apps else "none"
        if len(app_apps) > 3:
            ap_str += f" +{len(app_apps) - 3}"
        click.echo(f"  App:        {'enabled' if app_enabled else 'disabled'} ({ap_str})")
        click.echo()

        choice = questionary.select("Section:", choices=[s["name"] for s in sections]).ask()

        if choice is None or choice == "Exit without saving":
            fmt.info("Setup aborted — no changes saved.")
            return

        if choice == "💾 Save & Exit":
            errors = write_config(cfg)
            if errors:
                for e in errors:
                    fmt.error(e)
            else:
                fmt.success("Configuration saved.")
            return

        # --- sub-menus ---
        if choice == "⚙️  ACTIVITY — how keepalive simulates input":
            sub = questionary.select(
                "Edit:",
                choices=["Idle", "Method", "Key", "Back"],
            ).ask()
            if sub == "Idle":
                cfg["activity"]["idle"] = _edit_int("Idle threshold (seconds)", idle)
            elif sub == "Method":
                cfg["activity"]["method"] = _select_one("Method", list(METHODS), method)
            elif sub == "Key":
                cfg["activity"]["key"] = _select_one("Key", sorted(KEY_CODES), key_)

        elif choice == "🔋 POWER — sleep prevention":
            sub = questionary.select(
                "Edit:",
                choices=[
                    f"Caffeinate ({'on' if caf_enabled else 'off'})",
                    "Caffeinate mode",
                    f"Lid-Closed ({'on' if lid else 'off'})",
                    "Back",
                ],
            ).ask()
            if sub and "Caffeinate " in sub and "mode" not in sub:
                cfg["caffeinate"]["enabled"] = not caf_enabled
                if not cfg["caffeinate"]["enabled"]:
                    cfg["caffeinate"]["lid_closed"] = False
            elif sub == "Caffeinate mode":
                if caf_enabled:
                    cfg["caffeinate"]["mode"] = _select_one(
                        "Mode", list(CAFFEINATE_MODES), caf_mode
                    )
            elif sub and "Lid-Closed" in sub:
                if not caf_enabled:
                    fmt.warning("Caffeinate must be enabled first.")
                    click.prompt("Press Enter", default="")
                else:
                    cfg["caffeinate"]["lid_closed"] = not lid
                    if cfg["caffeinate"]["lid_closed"]:
                        cfg["caffeinate"]["mode"] = "system"

        elif choice == "⏰ TRIGGERS — when keepalive fires":
            sub = questionary.select(
                "Edit:",
                choices=[
                    "Schedule",
                    f"WiFi ({'on' if wifi_enabled else 'off'})",
                    f"App ({'on' if app_enabled else 'off'})",
                    "Back",
                ],
            ).ask()
            if sub == "Schedule":
                cfg["triggers"]["schedule"]["enabled"] = not sch_enabled
                if cfg["triggers"]["schedule"]["enabled"]:
                    sch_edit = questionary.select(
                        "Edit schedule?",
                        choices=["Edit from/to", "Back"],
                    ).ask()
                    if sch_edit == "Edit from/to":
                        cfg["triggers"]["schedule"]["from"] = _edit_str("From (HH:MM)", sch_from)
                        cfg["triggers"]["schedule"]["to"] = _edit_str("To (HH:MM)", sch_to)
            elif sub and "WiFi" in sub:
                cfg["triggers"]["wifi"]["enabled"] = not wifi_enabled
                if cfg["triggers"]["wifi"]["enabled"]:
                    _wifi_submenu(cfg)
            elif sub and "App" in sub:
                cfg["triggers"]["app"]["enabled"] = not app_enabled
                if cfg["triggers"]["app"]["enabled"]:
                    _app_submenu(cfg)


def _wifi_submenu(cfg: dict[str, Any]) -> None:
    """Add/remove SSIDs with autocomplete from available networks."""
    import questionary

    from keepalive.triggers.wifi import list_available_ssids

    while True:
        ssids = cfg["triggers"]["wifi"]["ssids"]
        networks = list_available_ssids()
        choices = [f"[×] {s}" for s in ssids]
        choices += ["[+ Add network…]", "Back"]

        sel = questionary.select("WiFi SSIDs:", choices=choices).ask()
        if sel == "Back" or sel is None:
            return
        if sel == "[+ Add network…]":
            hint = networks if networks else []
            new_ssid = _autocomplete("SSID (type to search or enter new):", hint)
            if new_ssid and new_ssid not in ssids:
                ssids.append(new_ssid)
                cfg["triggers"]["wifi"]["ssids"] = ssids
        elif sel and sel.startswith("[×] "):
            name = sel[4:]
            ssids.remove(name)
            cfg["triggers"]["wifi"]["ssids"] = ssids


def _app_submenu(cfg: dict[str, Any]) -> None:
    """Add/remove apps with autocomplete from installed bundles."""
    import questionary

    from keepalive.triggers.app import search_apps

    while True:
        apps = cfg["triggers"]["app"]["apps"]
        choices = [f"[×] {a}" for a in apps]
        choices += ["[+ Add app…]", "Back"]

        sel = questionary.select("App bundle IDs:", choices=choices).ask()
        if sel == "Back" or sel is None:
            return
        if sel == "[+ Add app…]":
            matches = search_apps("")
            display = [
                f"{m['name']} ({m['bundle_id']})" if m["bundle_id"] else m["name"]
                for m in matches[:50]
            ]
            new_sel = _autocomplete("App (type to search):", display)
            if new_sel:
                # extract bundle_id from "Name (com.example.app)"
                bid = new_sel.split("(")[-1].rstrip(")") if "(" in new_sel else new_sel
                if bid and bid not in apps:
                    apps.append(bid)
                    cfg["triggers"]["app"]["apps"] = apps
        elif sel and sel.startswith("[×] "):
            name = sel[4:]
            apps.remove(name)
            cfg["triggers"]["app"]["apps"] = apps


# ── config commands ────────────────────────────────────────────────────────


def cmd_config_export(*, fmt: Formatter | None = None) -> None:
    """Export current config to stdout."""
    if fmt is None:
        fmt = TextFormatter()
    cfg = load_settings()
    if isinstance(fmt, JsonFormatter):
        fmt.result(cfg)
    else:
        import json

        click.echo(json.dumps(cfg, indent=2))


def cmd_config_replace(  # noqa: C901 (validation + I/O dispatch)
    *,
    file_path: str | None = None,
    from_stdin: bool = False,
    fmt: Formatter | None = None,
) -> None:
    """Validate and write a full config replacement."""
    if fmt is None:
        fmt = TextFormatter()

    if file_path and from_stdin:
        fmt.error("Use --file OR --stdin, not both")
        sys.exit(1)
    if not file_path and not from_stdin:
        fmt.error("Specify --file or --stdin")
        sys.exit(1)

    try:
        if file_path:
            raw = json.loads(Path(file_path).read_text())
        else:
            raw = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        fmt.error(f"Invalid JSON: {exc}")
        sys.exit(1)

    if not isinstance(raw, dict):
        fmt.error("Config must be a JSON object")
        sys.exit(1)

    errors = write_config(raw)
    if errors:
        if isinstance(fmt, JsonFormatter):
            fmt.result({"valid": False, "errors": errors})
        else:
            for e in errors:
                fmt.error(e)
        sys.exit(1)

    if isinstance(fmt, JsonFormatter):
        fmt.result({"valid": True})
    else:
        fmt.success("Configuration replaced successfully")


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


# ── config sub-group ───────────────────────────────────────────────────────


@cli.group()
def config() -> None:
    """Manage keepalive configuration."""


@config.command("export")
@click.pass_context
def config_export(ctx: click.Context) -> None:
    """Print the full configuration as JSON."""
    cmd_config_export(fmt=ctx.obj["fmt"])


@config.command("replace")
@click.option("--file", "file_path", type=click.Path(exists=True), help="JSON file to read")
@click.option("--stdin", "from_stdin", is_flag=True, help="Read JSON from stdin")
@click.pass_context
def config_replace(
    ctx: click.Context,
    file_path: str | None,
    from_stdin: bool,
) -> None:
    """Replace the full configuration from a JSON file or stdin."""
    cmd_config_replace(file_path=file_path, from_stdin=from_stdin, fmt=ctx.obj["fmt"])


@config.command("setup")
@click.pass_context
def config_setup(ctx: click.Context) -> None:
    """Interactive configuration dashboard."""
    cmd_config_setup(fmt=ctx.obj["fmt"])
