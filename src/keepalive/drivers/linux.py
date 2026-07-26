"""Linux drivers — not yet implemented."""


class LinuxInput:
    def __init__(self) -> None:
        raise NotImplementedError(
            "Linux support is not yet implemented. "
            "Track progress: https://github.com/skozar/keepalive"
        )

    def check_permissions(self) -> dict[str, bool]:
        raise NotImplementedError("Linux support is not yet implemented")


class SystemdScheduler:
    def __init__(self) -> None:
        raise NotImplementedError(
            "Linux support is not yet implemented. "
            "Track progress: https://github.com/skozar/keepalive"
        )
