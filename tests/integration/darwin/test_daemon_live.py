"""Integration test — daemon loop with real macOS drivers (1 iteration)."""

import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only — Quartz + launchd")


class TestLiveDaemon:
    def test_one_iteration_does_not_crash(self, monkeypatch):
        """Run daemon for 1 iteration with real MacOSInput — just confirm
        it doesn't throw."""
        from keepalive.drivers.macos import MacOSInput

        monkeypatch.setattr(time, "sleep", lambda s: None)
        drv = MacOSInput()
        # idle_seconds always returns a real value — daemon should handle it
        from keepalive.daemon import daemon

        daemon(
            10_000,
            "mouse",
            "f13",
            drv,
            schedule="00:00-23:59",
            max_iterations=1,
        )
        # if we get here without exception, test passes
