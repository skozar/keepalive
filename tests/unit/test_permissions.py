"""Unit tests for permissions (help texts and mock checks)."""

from keepalive.permissions import help_for_platform
from tests.fake_drivers import FakeInput


class TestHelpForPlatform:
    def test_darwin_accessibility(self):
        text = help_for_platform("accessibility", "darwin")
        assert "System Settings" in text
        assert "Accessibility" in text

    def test_darwin_unknown_returns_empty(self):
        assert help_for_platform("nonexistent", "darwin") == ""

    def test_linux_input_group(self):
        text = help_for_platform("input", "linux")
        assert "usermod" in text

    def test_win32_returns_empty(self):
        assert help_for_platform("anything", "win32") == ""

    def test_defaults_to_current_platform(self):
        # Just smoke — should not raise.
        help_for_platform("accessibility")


class TestFakeCheckPermissions:
    def test_default_all_granted(self):
        fake = FakeInput()
        p = fake.check_permissions()
        assert p == {"accessibility": True}

    def test_custom_permissions(self):
        fake = FakeInput(permissions={"accessibility": False, "input": True})
        p = fake.check_permissions()
        assert p["accessibility"] is False
        assert p["input"] is True
