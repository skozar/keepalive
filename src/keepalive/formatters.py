"""User-facing output formatters.

Three implementations:

    TextFormatter   — coloured emoji output via click (interactive terminal).
    JsonFormatter   — JSON lines to stdout (for scripts / services).
    CaptureFormatter — records every call (for tests).
"""

import json
from typing import Any, Protocol

import click


class Formatter(Protocol):
    """Abstract output sink for CLI commands."""

    def info(self, msg: str) -> None: ...

    def success(self, msg: str) -> None: ...

    def warning(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...

    def result(self, data: dict[str, Any]) -> None: ...

    def prompt(self, msg: str) -> str: ...


# ── text (click-powered) ─────────────────────────────────────────────────────


class TextFormatter:
    """Uses click.secho / click.style for colours. Prompts via click.prompt."""

    def info(self, msg: str) -> None:
        click.echo(msg)

    def success(self, msg: str) -> None:
        click.secho(f"[OK] {msg}", fg="green")

    def warning(self, msg: str) -> None:
        click.secho(f"[!!] {msg}", fg="yellow")

    def error(self, msg: str) -> None:
        click.secho(f"[FAIL] {msg}", fg="red", err=True)

    def result(self, data: dict[str, Any]) -> None:
        """No-op — structured data is for JSON mode only."""

    def prompt(self, msg: str) -> str:
        return str(click.prompt(msg, default="", show_default=False))


# ── json ─────────────────────────────────────────────────────────────────────


class JsonFormatter:
    """All user-visible output suppressed. ``result()`` emits a single JSON
    object to stdout — one per command invocation."""

    def __init__(self) -> None:
        self._emitted = False

    def info(self, msg: str) -> None:
        pass

    def success(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass

    def result(self, data: dict[str, Any]) -> None:
        if not self._emitted:
            click.echo(json.dumps(data))
            self._emitted = True

    def prompt(self, msg: str) -> str:
        raise RuntimeError("JsonFormatter does not support interactive prompts")


# ── capture (test) ───────────────────────────────────────────────────────────


class CaptureFormatter:
    """Records every call as (method_name, *args) tuples for assertions."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.results: list[dict[str, Any]] = []
        self._prompt_responses: list[str] = []

    def info(self, msg: str) -> None:
        self.calls.append(("info", msg))

    def success(self, msg: str) -> None:
        self.calls.append(("success", msg))

    def warning(self, msg: str) -> None:
        self.calls.append(("warning", msg))

    def error(self, msg: str) -> None:
        self.calls.append(("error", msg))

    def result(self, data: dict[str, Any]) -> None:
        self.results.append(data)

    def prompt(self, msg: str) -> str:
        self.calls.append(("prompt", msg))
        if self._prompt_responses:
            return self._prompt_responses.pop(0)
        return ""
