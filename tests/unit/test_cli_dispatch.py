"""Unit tests for CLI dispatch — spy_daemon, FakeInput, no subprocess."""

from keepalive.cli import cmd_run, cmd_start, cmd_stop
from tests.fake_drivers import FakeInput, FakeScheduler


class TestCmdRunDispatch:
    def test_passes_all_args_to_daemon(self, spy_daemon):
        fake = FakeInput(idle=0)
        cmd_run(
            "09:00-18:00",
            120,
            "key",
            "f15",
            input_drv=fake,
            daemon_fn=spy_daemon,
        )
        r = spy_daemon.received
        assert r["schedule"] == "09:00-18:00"
        assert r["idle"] == 120
        assert r["method"] == "key"
        assert r["key"] == "f15"

    def test_uses_input_drv_from_factory_by_default(self, spy_daemon, monkeypatch):
        """When input_drv is None, create_input_driver() is called."""
        fake = FakeInput(idle=0)
        monkeypatch.setattr("keepalive.cli.create_input_driver", lambda: fake)
        cmd_run("08:00-17:00", 300, "mouse", "f13", daemon_fn=spy_daemon)
        assert spy_daemon.received["input_drv"] is fake


class TestCmdStartDispatch:
    def test_installs_scheduler(self):
        sched = FakeScheduler()
        cmd_start("09:00-18:00", 120, "mouse", "f13", sched=sched)
        assert sched.last_install is not None
        assert sched.last_install["schedule"] == "09:00-18:00"
        assert sched.last_install["idle"] == 120
        assert sched.last_install["method"] == "mouse"
        assert sched.last_install["key"] == "f13"

    def test_refuses_when_already_running(self):
        sched = FakeScheduler(running=True)
        try:
            cmd_start("09:00-18:00", 120, "mouse", "f13", sched=sched)
        except SystemExit as e:
            assert e.code == 1
        else:
            assert False, "Expected SystemExit(1)"


class TestCmdStopDispatch:
    def test_uninstalls_running_scheduler(self):
        sched = FakeScheduler(running=True)
        cmd_stop(sched=sched)
        assert sched.is_running() is False

    def test_noop_when_not_running(self):
        sched = FakeScheduler(running=False)
        cmd_stop(sched=sched)
        assert sched.is_running() is False  # still not running
