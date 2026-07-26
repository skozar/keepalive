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
        drv.jiggle()

    def test_press_key_lookup_resolves(self):
        from keepalive.config import KEY_CODES
        from keepalive.drivers.macos import MacOSInput

        drv = MacOSInput()
        code = KEY_CODES.get("f13")
        assert code is not None
        assert callable(drv.press_key)


class TestMacOSPermissions:
    def test_check_permissions_returns_bool(self):
        from keepalive.drivers.macos import MacOSInput

        drv = MacOSInput()
        perms = drv.check_permissions()
        assert isinstance(perms, dict)
        assert "accessibility" in perms
        assert isinstance(perms["accessibility"], bool)
