"""Unit tests for CLI dispatch — CaptureFormatter, FakeInput, spy_daemon."""

from keepalive.cli import cmd_setup, cmd_start, cmd_stop
from keepalive.formatters import CaptureFormatter
from tests.fake_drivers import FakeInput, FakeScheduler

# ── helpers ──────────────────────────────────────────────────────────────────


def _fmt() -> CaptureFormatter:
    return CaptureFormatter()


def _success_msgs(fmt: CaptureFormatter) -> list[str]:
    return [m[1] for m in fmt.calls if m[0] == "success"]


def _error_msgs(fmt: CaptureFormatter) -> list[str]:
    return [m[1] for m in fmt.calls if m[0] == "error"]


def _warning_msgs(fmt: CaptureFormatter) -> list[str]:
    return [m[1] for m in fmt.calls if m[0] == "warning"]


# ── start ────────────────────────────────────────────────────────────────────


class TestCmdStartDispatch:
    def test_installs_scheduler(self):
        sched = FakeScheduler()
        fake = FakeInput()
        fmt = _fmt()
        cmd_start("09:00-18:00", 120, "mouse", "f13", sched=sched, input_drv=fake, fmt=fmt)
        assert sched.last_install is not None
        assert sched.last_install["schedule"] == "09:00-18:00"
        assert "Agent started" in _success_msgs(fmt)[0]
        assert fmt.results[0]["status"] == "installed"

    def test_refuses_when_already_running(self):
        sched = FakeScheduler(running=True)
        fake = FakeInput()
        fmt = _fmt()
        try:
            cmd_start("09:00-18:00", 120, "mouse", "f13", sched=sched, input_drv=fake, fmt=fmt)
        except SystemExit as e:
            assert e.code == 1
        assert any("already" in m.lower() for m in _error_msgs(fmt))

    def test_warns_when_permissions_missing(self):
        sched = FakeScheduler()
        fake = FakeInput(permissions={"accessibility": False})
        fmt = _fmt()
        cmd_start("09:00-18:00", 120, "mouse", "f13", sched=sched, input_drv=fake, fmt=fmt)
        # Should install anyway
        assert sched.last_install is not None
        # But warn about accessibility
        assert any("Accessibility not granted" in m for m in _warning_msgs(fmt))


# ── stop ─────────────────────────────────────────────────────────────────────


class TestCmdStopDispatch:
    def test_uninstalls_running_scheduler(self):
        sched = FakeScheduler(running=True)
        fmt = _fmt()
        cmd_stop(sched=sched, fmt=fmt)
        assert sched.is_running() is False
        assert "Agent stopped" in _success_msgs(fmt)[0]

    def test_noop_when_not_running(self):
        sched = FakeScheduler(running=False)
        fmt = _fmt()
        cmd_stop(sched=sched, fmt=fmt)
        assert sched.is_running() is False
        assert any("not installed" in m.lower() for m in [x[1] for x in fmt.calls])


# ── setup ────────────────────────────────────────────────────────────────────


class TestCmdSetupDispatch:
    def test_json_mode_returns_dict(self):
        """In JSON mode, setup does one check and returns result."""
        fake = FakeInput(permissions={"accessibility": True})
        from keepalive.formatters import JsonFormatter

        json_fmt = JsonFormatter()
        cmd_setup(input_drv=fake, fmt=json_fmt)
        # result was stored internally — check via a side channel
        assert json_fmt._emitted is True

    def test_text_loop_when_missing_then_quit(self):
        """Interactive loop with 'q' exits."""
        fake = FakeInput(permissions={"accessibility": False})
        fmt = _fmt()
        fmt._prompt_responses = ["q"]

        try:
            cmd_setup(input_drv=fake, fmt=fmt)
        except SystemExit:
            pass
        assert any("Setup aborted" in m for m in [x[1] for x in fmt.calls])

    def test_text_loop_when_all_ok(self):
        """When all permissions are granted, loop exits immediately."""
        fake = FakeInput(permissions={"accessibility": True})
        fmt = _fmt()
        cmd_setup(input_drv=fake, fmt=fmt)
        assert any("All permissions OK" in m for m in [x[1] for x in fmt.calls])
