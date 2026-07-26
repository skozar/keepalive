"""Windows drivers — not yet implemented."""


class WindowsInput:
    def __init__(self) -> None:
        raise NotImplementedError(
            "Windows support is not yet implemented. "
            "Track progress: https://github.com/skozar/keepalive"
        )

    def check_permissions(self) -> dict[str, bool]:
        raise NotImplementedError("Windows support is not yet implemented")


class TaskScheduler:
    def __init__(self) -> None:
        raise NotImplementedError(
            "Windows support is not yet implemented. "
            "Track progress: https://github.com/skozar/keepalive"
        )
