"""macOS drivers: Quartz-based input simulation + launchd scheduler."""

import subprocess
import time
from typing import cast

from keepalive.config import (
    KEY_CODES,
    LAUNCHD_LABEL,
    LOG_FILE,
    PLIST_PATH,
)
from keepalive.log_config import log

# ── InputDriver ──────────────────────────────────────────────────────────────


class MacOSInput:
    """Mouse jiggle + function-key press via Quartz and AppleScript."""

    def idle_seconds(self) -> float:
        import Quartz

        return cast(
            float,
            Quartz.CGEventSourceSecondsSinceLastEventType(
                Quartz.kCGEventSourceStateCombinedSessionState,
                Quartz.kCGAnyInputEventType,
            ),
        )

    def jiggle(self) -> None:
        """Move cursor 1 px right and back — resets idle timer imperceptibly."""
        import Quartz

        pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        x, y = int(pos.x), int(pos.y)

        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x + 1, y), 0)
        Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)
        time.sleep(0.05)

        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
        Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)

    def press_key(self, key_name: str) -> None:
        """Press a function key via AppleScript."""
        code = KEY_CODES.get(key_name)
        if code is None:
            log.error("Unknown key: %s", key_name)
            return
        subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to key code {code}'],
            capture_output=True,
            timeout=5,
        )

    def check_permissions(self) -> dict[str, bool]:
        """Probe whether Accessibility is granted.

        We try a no-op osascript call — if it hangs or fails, permissions
        are missing.
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", ""],
                capture_output=True,
                timeout=3,
            )
            ok = result.returncode == 0
        except subprocess.TimeoutExpired, FileNotFoundError:
            ok = False
        return {"accessibility": ok}


# ── SchedulerDriver ─────────────────────────────────────────────────────────

_PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
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


class LaunchdScheduler:
    """Manage the launchd agent plist."""

    def install(self, binary: str, schedule: str, idle: int, method: str, key: str) -> None:
        PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        plist_xml = _PLIST_TEMPLATE.format(
            label=LAUNCHD_LABEL,
            binary=binary,
            schedule=schedule,
            idle=str(idle),
            method=method,
            key=key,
            log_file=str(LOG_FILE),
        )
        PLIST_PATH.write_text(plist_xml)
        subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=True)
        log.info("Launchd agent installed — %s", LAUNCHD_LABEL)

    def uninstall(self) -> None:
        if PLIST_PATH.exists():
            subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
            PLIST_PATH.unlink()
            log.info("Launchd agent uninstalled — %s", LAUNCHD_LABEL)

    def is_running(self) -> bool:
        try:
            result = subprocess.run(
                ["launchctl", "list", LAUNCHD_LABEL],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except FileNotFoundError:
            return False
