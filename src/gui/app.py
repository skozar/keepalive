"""Menu bar app — start/stop keepalive, configure settings."""

import json
import subprocess
from pathlib import Path

import rumps

CONFIG_DIR = Path.home() / ".config" / "keepalive"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS = {
    "schedule": "04:00-12:00",
    "idle": 180,
    "method": "mouse",
    "key": "f13",
}


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
    rc, stdout, _ = run_cli("status")
    return rc == 0 and "running" in stdout and "🟢" in stdout


class KeepaliveApp(rumps.App):
    def __init__(self):
        super().__init__("keepalive", title="●")
        self.settings = load_settings()
        self._update_icon()

    def _update_icon(self):
        if is_running():
            self.title = "●"
        else:
            self.title = "○"

    @rumps.clicked("Start")
    def start(self, _):
        s = self.settings
        rc, stdout, stderr = run_cli(
            "start",
            "--schedule", s["schedule"],
            "--idle", str(s["idle"]),
            "--method", s["method"],
            "--key", s["key"],
        )
        if rc == 0:
            rumps.notification("keepalive", "Started", stdout.strip())
        else:
            rumps.alert(f"Error starting keepalive:\n{stderr}")
        self._update_icon()

    @rumps.clicked("Stop")
    def stop(self, _):
        rc, stdout, stderr = run_cli("stop")
        if rc == 0:
            rumps.notification("keepalive", "Stopped", stdout.strip())
        else:
            rumps.alert(f"Error: {stderr}")
        self._update_icon()

    @rumps.clicked("Settings...")
    def open_settings(self, _):
        from gui.settings_window import SettingsWindow

        win = SettingsWindow(self.settings)
        result = win.show()
        if result is not None:
            self.settings = result
            save_settings(result)

    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()
