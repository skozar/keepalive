"""Platform-aware driver factory.

Imports happen lazily so that non-macOS platforms don't crash on
import keepalive (Quartz is macOS-only and can't even be installed
on Linux/Windows).
"""

import sys

from keepalive.protocols import InputDriver, SchedulerDriver


def create_input_driver() -> InputDriver:
    if sys.platform == "darwin":
        from keepalive.drivers.macos import MacOSInput

        return MacOSInput()
    elif sys.platform.startswith("linux"):
        from keepalive.drivers.linux import LinuxInput

        return LinuxInput()  # type: ignore[return-value]
    elif sys.platform == "win32":
        from keepalive.drivers.windows import WindowsInput

        return WindowsInput()  # type: ignore[return-value]
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def create_scheduler() -> SchedulerDriver:
    if sys.platform == "darwin":
        from keepalive.drivers.macos import LaunchdScheduler

        return LaunchdScheduler()
    elif sys.platform.startswith("linux"):
        from keepalive.drivers.linux import SystemdScheduler

        return SystemdScheduler()  # type: ignore[return-value]
    elif sys.platform == "win32":
        from keepalive.drivers.windows import TaskScheduler

        return TaskScheduler()  # type: ignore[return-value]
    raise RuntimeError(f"Unsupported platform: {sys.platform}")
