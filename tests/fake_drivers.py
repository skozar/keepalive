"""Fake implementations of InputDriver and SchedulerDriver for unit tests."""


class FakeInput:
    """Records every call — no real I/O."""

    def __init__(self, idle: float = 0, permissions: dict[str, bool] | None = None) -> None:
        self._idle = idle
        self._permissions = permissions or {"accessibility": True}
        self.jiggle_calls = 0
        self.pressed_keys: list[str] = []
        self.key_errors: list[str] = []

    def idle_seconds(self) -> float:
        return self._idle

    def jiggle(self) -> None:
        self.jiggle_calls += 1

    def press_key(self, key_name: str) -> None:
        self.pressed_keys.append(key_name)

    def check_permissions(self) -> dict[str, bool]:
        return dict(self._permissions)


class FakeScheduler:
    """In-memory scheduler — no launchd/systemd/task-scheduler."""

    def __init__(self, running: bool = False) -> None:
        self._running = running
        self._installed: bool = running
        self.last_install: dict[str, object] | None = None

    def install(self, binary: str, schedule: str, idle: int, method: str, key: str) -> None:
        self._installed = True
        self._running = True
        self.last_install = {
            "binary": binary,
            "schedule": schedule,
            "idle": idle,
            "method": method,
            "key": key,
        }

    def uninstall(self) -> None:
        self._installed = False
        self._running = False

    def is_running(self) -> bool:
        return self._running
