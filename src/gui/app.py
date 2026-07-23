"""Menu bar app — start/stop keepalive, configure settings."""

import json
import subprocess
import sys
from pathlib import Path

import rumps

CONFIG_DIR = Path.home() / ".config" / "keepalive"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS = {
    "schedule_from": "08:00",
    "schedule_to": "17:00",
    "idle": 180,
    "method": "mouse",
    "key": "f13",
}


def _assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).parent / "assets"


def load_settings() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return dict(DEFAULTS)


def save_settings(settings: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(settings, indent=2))


def run_cli(*args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["/opt/homebrew/bin/keepalive", *args],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def is_running() -> bool:
    rc, stdout, _ = run_cli("status", "--json")
    if rc != 0:
        return False
    try:
        data = json.loads(stdout)
        return data.get("running", False)
    except json.JSONDecodeError:
        return False


def get_cli_settings() -> dict | None:
    rc, stdout, _ = run_cli("status", "--json")
    if rc != 0:
        return None
    try:
        data = json.loads(stdout)
        if data.get("running"):
            return {
                "schedule": data.get("schedule"),
                "idle": data.get("idle"),
                "method": data.get("method"),
                "key": data.get("key"),
            }
    except json.JSONDecodeError:
        pass
    return None


class KeepaliveApp(rumps.App):
    def __init__(self):
        super().__init__(
            "keepalive",
            quit_button=None,
            icon=str(_assets_dir() / "icon_stopped.png"),
            template=True,
        )
        self.icon_running = str(_assets_dir() / "icon_running.png")
        self.icon_stopped = str(_assets_dir() / "icon_stopped.png")
        self.settings = load_settings()
        # Auto-start keepalive if not running
        if not is_running():
            run_cli(*self._cli_args())

    def _update_state(self):
        running = is_running()
        self.icon = self.icon_running if running else self.icon_stopped
        self.menu["Start"]._menuitem.setHidden_(running)
        self.menu["Stop"]._menuitem.setHidden_(not running)

    def _cli_args(self) -> list[str]:
        s = self.settings
        schedule = f"{s['schedule_from']}-{s['schedule_to']}"
        return [
            "start", "--schedule", schedule,
            "--idle", str(s["idle"]),
            "--method", s["method"],
            "--key", s["key"],
        ]

    def _ensure_running(self):
        cli_cfg = get_cli_settings()
        if cli_cfg is None:
            run_cli(*self._cli_args())
            return
        expected_schedule = f"{self.settings['schedule_from']}-{self.settings['schedule_to']}"
        if (cli_cfg.get("schedule") != expected_schedule or
            str(cli_cfg.get("idle")) != str(self.settings["idle"]) or
            cli_cfg.get("method") != self.settings["method"] or
            cli_cfg.get("key") != self.settings["key"]):
            run_cli("stop")
            run_cli(*self._cli_args())

    # ── timer: check state every 30s ──────────────────────────────────────

    @rumps.timer(30)
    def monitor(self, _):
        self._ensure_running()
        self._update_state()

    # ── menu actions ──────────────────────────────────────────────────────

    @rumps.clicked("Start")
    def start(self, _):
        rc, stdout, stderr = run_cli(*self._cli_args())
        if rc == 0:
            rumps.notification("keepalive", "Started", stdout.strip())
        else:
            rumps.alert(f"Error starting keepalive:\n{stderr}")
        self._update_state()

    @rumps.clicked("Stop")
    def stop(self, _):
        rc, stdout, stderr = run_cli("stop")
        if rc == 0:
            rumps.notification("keepalive", "Stopped", stdout.strip())
        else:
            rumps.alert(f"Error:\n{stderr}")
        self._update_state()

    @rumps.clicked("Settings...")
    def open_settings(self, _):
        try:
            from gui.settings_window import SettingsWindow
        except ImportError as e:
            rumps.alert(f"Failed to load settings window:\n{e}")
            return

        try:
            win = SettingsWindow(self.settings)
            result = win.show()
            if result is not None:
                self.settings = result
                save_settings(result)
                if is_running():
                    run_cli("stop")
                    run_cli(*self._cli_args())
                self._update_state()
        except Exception as e:
            rumps.alert(f"Settings error:\n{e}")

    @rumps.clicked("Quit")
    def quit_app(self, _):
        run_cli("stop")
        rumps.quit_application()
