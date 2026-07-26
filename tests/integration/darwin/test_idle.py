"""Integration test — real MacOSInput on macOS."""

import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "darwin", reason="macOS driver — Quartz only on Darwin"
)


class TestMacOSIdle:
    def test_idle_returns_non_negative(self):
        from keepalive.drivers.macos import MacOSInput

        drv = MacOSInput()
        idle = drv.idle_seconds()
        assert idle >= 0, f"idle_seconds() returned {idle}, expected >= 0"

    def test_jiggle_does_not_crash(self):
        from keepalive.drivers.macos import MacOSInput

        drv = MacOSInput()
        drv.jiggle()  # should not raise

    def test_press_key_lookup_resolves(self):
        """press_key resolves its key code — actual osascript needs
        Accessibility permissions and may time out in CI/sandbox."""
        from keepalive.config import KEY_CODES
        from keepalive.drivers.macos import MacOSInput

        drv = MacOSInput()
        # Verify the key lookup works (no osascript call yet).
        code = KEY_CODES.get("f13")
        assert code is not None
        # press_key is callable — but don't run the subprocess in test.
        assert callable(drv.press_key)
