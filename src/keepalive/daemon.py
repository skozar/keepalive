"""Daemon loop — multi-platform idle blocker.

The core loop checks conditions (triggers) and fires input events when
the machine has been idle longer than the threshold.

Supports:
- OR-condition logic: schedule / wifi / app triggers
- Caffeinate: prevent system/display sleep via subprocess ``caffeinate``
"""

from __future__ import annotations

import random
import subprocess
import time
from collections.abc import Callable

from keepalive.config import parse_schedule as _parse_schedule
from keepalive.log_config import log
from keepalive.protocols import InputDriver
from keepalive.triggers import combine_or
from keepalive.triggers.schedule import in_active_window

# ── public API ─────────────────────────────────────────────────────────────


def daemon(  # noqa: C901 (loop + condition dispatch + caffeinate)
    idle_threshold: int,
    method: str,
    key: str,
    input_drv: InputDriver,
    *,
    schedule: str | None = None,
    conditions: list[Callable[[], bool]] | None = None,
    caffeinate_mode: str | None = None,
    max_iterations: int | None = None,
) -> None:
    """Run the main daemon loop.

    Parameters
    ----------
    idle_threshold:
        Seconds of idle time before keepalive fires.
    method:
        ``"mouse"``, ``"key"``, ``"both"``, or ``"boost"`` (future).
    key:
        Function key name (``"f13"``, ``"f14"``, ``"f15"``).
    input_drv:
        Platform-specific ``InputDriver`` implementation.
    schedule:
        **Legacy.**  ``"08:00-17:00"`` string — triggers only during
        those hours.  Ignored when *conditions* is provided.
    conditions:
        **New.**  List of OR'd ``Condition`` callables.  The daemon
        fires whenever **any** single condition is ``True``.  Built
        by the CLI from the config triggers section.
    caffeinate_mode:
        ``"display"`` or ``"system"`` — spawns ``caffeinate`` subprocess
        for the lifetime of the daemon.  ``None`` means disabled.
    max_iterations:
        For testing only — exit after N iterations instead of
        running forever.
    """
    # --- resolve the "should I fire?" check ---
    if conditions:
        checker: Callable[[], bool] = combine_or(*conditions)
    elif schedule:
        start_hour, end_hour = _parse_schedule(schedule)

        def _sched_check() -> bool:
            return in_active_window((start_hour, end_hour))

        checker = _sched_check
    else:
        raise ValueError("Either schedule (legacy) or conditions is required")

    # --- caffeinate (OS power assertion) ---
    _caf: subprocess.Popen[bytes] | None = None
    if caffeinate_mode:
        _caf = _start_caffeinate(caffeinate_mode)

    log.info(
        "Daemon started — idle %ds, method=%s, key=%s, caffeinate=%s",
        idle_threshold,
        method,
        key,
        caffeinate_mode or "off",
    )

    iteration = 0
    try:
        while True:
            if max_iterations is not None and iteration >= max_iterations:
                break
            iteration += 1

            try:
                if checker():
                    idle_secs = input_drv.idle_seconds()
                    if idle_secs >= idle_threshold:
                        if method in ("mouse", "both"):
                            input_drv.jiggle()
                        if method in ("key", "both"):
                            input_drv.press_key(key)
                        log.info(
                            "Keepalive fired (method=%s, idle %.0fs)",
                            method,
                            idle_secs,
                        )
                    else:
                        log.info("Active (idle %.0fs), skipping", idle_secs)
                    time.sleep(random.randint(30, 60))
                else:
                    time.sleep(300)
            except Exception:
                log.exception("Error — restarting loop in 30s")
                time.sleep(30)
    finally:
        if _caf is not None:
            _caf.terminate()
            try:
                _caf.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _caf.kill()


# ── internal helpers ───────────────────────────────────────────────────────


def _start_caffeinate(mode: str) -> subprocess.Popen[bytes] | None:
    """Spawn ``caffeinate`` subprocess to prevent sleep."""
    import platform

    if platform.system() != "Darwin":
        log.info("Caffeinate not supported on this platform")
        return None

    if mode == "system":
        proc = subprocess.Popen(
            ["caffeinate", "-s"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            ["caffeinate", "-d"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    log.info("Caffeinate %s mode enabled (pid %d)", mode, proc.pid)
    return proc
