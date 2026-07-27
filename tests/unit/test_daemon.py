"""Unit tests for daemon loop (fake drivers, conditions)."""

import time
from datetime import datetime

import pytest

from keepalive.daemon import daemon
from keepalive.triggers.schedule import in_active_window

# ── schedule trigger (standalone) ──────────────────────────────────────────


class TestInActiveWindow:
    @staticmethod
    def _dt(hour: int) -> datetime:
        return datetime(2026, 7, 1, hour, 0)

    def test_inside_window(self) -> None:
        assert in_active_window((9, 17), now=self._dt(10)) is True  # type: ignore[call-arg]

    def test_before_window(self) -> None:
        assert in_active_window((9, 17), now=self._dt(8)) is False  # type: ignore[call-arg]

    def test_overnight(self) -> None:
        assert in_active_window((22, 2), now=self._dt(23)) is True  # type: ignore[call-arg]
        assert in_active_window((22, 2), now=self._dt(1)) is True  # type: ignore[call-arg]
        assert in_active_window((22, 2), now=self._dt(3)) is False  # type: ignore[call-arg]


# ── daemon loop with fake driver ───────────────────────────────────────────


class FakeDriver:
    def __init__(self, idle: float = 500):
        self._idle = idle
        self.jiggle_calls = 0
        self.key_presses: list[str] = []

    def idle_seconds(self) -> float:
        return self._idle

    def jiggle(self) -> None:
        self.jiggle_calls += 1

    def press_key(self, name: str) -> None:
        self.key_presses.append(name)

    def check_permissions(self) -> dict[str, bool]:
        return {"accessibility": True}


@pytest.fixture
def fake_drv() -> FakeDriver:
    return FakeDriver(idle=500)


class TestDaemonLoop:
    def test_fires_when_idle_exceeded(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            schedule="08:00-17:00",
            max_iterations=1,
        )
        assert fake.jiggle_calls == 1

    def test_skips_when_active(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=10)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            schedule="08:00-17:00",
            max_iterations=1,
        )
        assert fake.jiggle_calls == 0

    def test_key_method_presses_key(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "key",
            "f14",
            fake,  # type: ignore[arg-type]
            schedule="08:00-17:00",
            max_iterations=1,
        )
        assert "f14" in fake.key_presses
        assert fake.jiggle_calls == 0

    def test_both_method_calls_both(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "both",
            "f15",
            fake,  # type: ignore[arg-type]
            schedule="08:00-17:00",
            max_iterations=1,
        )
        assert fake.jiggle_calls == 1
        assert "f15" in fake.key_presses

    def test_outside_window_skips(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            schedule="02:00-03:00",
            max_iterations=1,
        )
        assert fake.jiggle_calls == 0

    def test_max_iterations_limits_loop(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            schedule="08:00-17:00",
            max_iterations=3,
        )
        assert fake.jiggle_calls == 3

    def test_conditions_or_logic(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            conditions=[
                lambda: False,
                lambda: True,
            ],
            max_iterations=1,
        )
        assert fake.jiggle_calls == 1

    def test_conditions_all_false_skips(self, monkeypatch) -> None:
        monkeypatch.setattr(time, "sleep", lambda s: None)
        fake = FakeDriver(idle=500)
        daemon(
            300,
            "mouse",
            "f13",
            fake,  # type: ignore[arg-type]
            conditions=[lambda: False, lambda: False],
            max_iterations=1,
        )
        assert fake.jiggle_calls == 0
