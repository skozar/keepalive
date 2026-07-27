"""Abstract driver contracts for multi-platform support.

Every platform (macOS / Linux / Windows) provides concrete implementations
of InputDriver and SchedulerDriver. The core daemon and CLI depend only on
these protocols — never on platform-specific modules.
"""

from typing import Protocol


class InputDriver(Protocol):
    """Simulate user activity and measure idle time."""

    def idle_seconds(self) -> float:
        """Seconds since the last real keyboard/mouse event."""
        ...

    def jiggle(self) -> None:
        """Move the mouse imperceptibly — resets the idle timer."""
        ...

    def press_key(self, key_name: str) -> None:
        """Press a function key (f13, f14, f15)."""
        ...

    def check_permissions(self) -> dict[str, bool]:
        """Return {permission_name: granted} for all required OS permissions.

        Keepalive needs Accessibility on macOS, ``input`` group on Linux.
        The driver only reports factuality — *how* to explain to the user
        lives in ``permissions.py`` at the CLI layer.
        """
        ...

    def request_accessibility(self) -> None:
        """Trigger OS permission dialog (macOS only).

        Only the daemon (launchd → keepalive-cli) calls this — once at
        startup.  CLI commands use check_permissions() instead to avoid
        showing a dialog for the terminal app.
        """
        ...


class SchedulerDriver(Protocol):
    """Install / uninstall / check the OS-level scheduler agent."""

    def install(self, binary: str, schedule: str, idle: int, method: str, key: str) -> None:
        """Create the scheduler unit / plist / task to run keepalive on boot."""
        ...

    def uninstall(self) -> None:
        """Remove the scheduler entry."""
        ...

    def is_running(self) -> bool:
        """Return True if the agent is currently loaded by the OS scheduler."""
        ...
