import datetime

from keepalive.config import parse_schedule
from keepalive.daemon import in_active_window


class TestParseSchedule:
    def test_valid(self):
        assert parse_schedule("04:00-12:00") == (4, 12)

    def test_single_digit_hours(self):
        assert parse_schedule("9:00-17:00") == (9, 17)

    def test_over_midnight(self):
        assert parse_schedule("22:00-02:00") == (22, 2)


class TestInActiveWindow:
    def _dt(self, hour: int) -> datetime.datetime:
        return datetime.datetime(2026, 1, 1, hour, 0)

    def test_inside(self):
        assert in_active_window(4, 12, now=self._dt(10)) is True

    def test_after_end(self):
        assert in_active_window(4, 12, now=self._dt(13)) is False

    def test_before_start(self):
        assert in_active_window(4, 12, now=self._dt(3)) is False

    def test_exact_start(self):
        assert in_active_window(4, 12, now=self._dt(4)) is True

    def test_exact_end(self):
        assert in_active_window(4, 12, now=self._dt(12)) is False
