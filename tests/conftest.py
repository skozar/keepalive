"""Shared test fixtures."""

import pytest

from tests.fake_drivers import FakeInput, FakeScheduler


@pytest.fixture
def fake_input() -> FakeInput:
    return FakeInput(idle=500)  # above default 180s threshold


@pytest.fixture
def fake_scheduler() -> FakeScheduler:
    return FakeScheduler()


@pytest.fixture
def spy_daemon():
    """Returns a callable + a mutable dict to capture daemon args."""
    received: dict[str, object] = {}

    def spy(schedule, idle, method, key, input_drv):
        received["schedule"] = schedule
        received["idle"] = idle
        received["method"] = method
        received["key"] = key
        received["input_drv"] = input_drv

    spy.received = received  # type: ignore[attr-defined]
    return spy
