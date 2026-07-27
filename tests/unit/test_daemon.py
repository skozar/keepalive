"""Unit tests for daemon loop — uses FakeInput, no OS calls."""

import time
from datetime import datetime

from keepalive.daemon import daemon, in_active_window
from tests.fake_drivers import FakeInput


def _always_active(*_a: object, **_kw: object) -> bool:
    return True


class TestInActiveWindow:
    def test_inside_window(self, monkeypatch):
        monkeypatch.setattr(
            "keepalive.daemon.datetime",
            type("FakeDT", (), {"now": staticmethod(lambda: datetime(2026, 7, 28, 12, 0))}),  # noqa: E501
        )
        assert in_active_window(9, 18) is True

    def test_before_window(self, monkeypatch):
        monkeypatch.setattr(
            "keepalive.daemon.datetime",
            type("FakeDT", (), {"now": staticmethod(lambda: datetime(2026, 7, 28, 7, 0))}),  # noqa: E501
        )
        assert in_active_window(9, 18) is False


class TestDaemonLoop:
    def test_fires_when_idle_exceeded(self, monkeypatch):
        """idle > threshold → jiggle called."""
        fake = FakeInput(idle=500)  # above 300s threshold
        monkeypatch.setattr(time, "sleep", lambda s: None)
        monkeypatch.setattr("keepalive.daemon.in_active_window", _always_active)
        daemon("08:00-17:00", 300, "mouse", "f13", fake, max_iterations=1)
        assert fake.jiggle_calls == 1

    def test_skips_when_active(self, monkeypatch):
        """daemon skips when idle < threshold."""
        fake = FakeInput(idle=100)  # below 300s threshold
        monkeypatch.setattr(time, "sleep", lambda s: None)
        monkeypatch.setattr("keepalive.daemon.in_active_window", _always_active)
        daemon("08:00-17:00", 300, "mouse", "f13", fake, max_iterations=1)
        assert fake.jiggle_calls == 0

    def test_key_method_presses_key(self, monkeypatch):
        fake = FakeInput(idle=500)
        monkeypatch.setattr(time, "sleep", lambda s: None)
        monkeypatch.setattr("keepalive.daemon.in_active_window", _always_active)
        daemon("08:00-17:00", 300, "key", "f14", fake, max_iterations=1)
        assert fake.pressed_keys == ["f14"]
        assert fake.jiggle_calls == 0

    def test_both_method_calls_both(self, monkeypatch):
        fake = FakeInput(idle=500)
        monkeypatch.setattr(time, "sleep", lambda s: None)
        monkeypatch.setattr("keepalive.daemon.in_active_window", _always_active)
        daemon("08:00-17:00", 300, "both", "f15", fake, max_iterations=1)
        assert fake.jiggle_calls == 1
        assert "f15" in fake.pressed_keys

    def test_outside_window_skips(self, monkeypatch):
        """At 3 AM (outside 08-17), daemon sleeps without calling jiggle."""
        fake = FakeInput(idle=999)
        monkeypatch.setattr(time, "sleep", lambda s: None)

        def never_active(*_a, **_kw):
            return False

        monkeypatch.setattr("keepalive.daemon.in_active_window", never_active)
        daemon("08:00-17:00", 300, "mouse", "f13", fake, max_iterations=1)
        assert fake.jiggle_calls == 0

    def test_max_iterations_limits_loop(self, monkeypatch):
        """max_iterations=3 runs exactly 3 loop iterations."""
        fake = FakeInput(idle=500)
        monkeypatch.setattr(time, "sleep", lambda s: None)
        monkeypatch.setattr("keepalive.daemon.in_active_window", _always_active)
        daemon("08:00-17:00", 300, "mouse", "f13", fake, max_iterations=3)
        assert fake.jiggle_calls == 3
