# Architecture

## Overview

keepalive-cli is built around two principles:

1. **Protocol + Dependency Injection** — the core (daemon, CLI commands) depends
   on abstract `InputDriver` / `SchedulerDriver` protocols, never on
   platform‑specific modules. Concrete drivers are injected at runtime or swap
   freely in tests.
2. **Formatter‑driven output** — every user‑visible message goes through a
   `Formatter` object. Text mode (interactive terminal), JSON mode
   (scripts/services), and capture mode (tests) share the same code paths.

```
                   ┌──────────────────────────┐
                   │      protocols.py        │
                   │  InputDriver             │
                   │  SchedulerDriver         │
                   └───────────┬──────────────┘
                               │ depends on
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
      daemon.py            cli.py              tests/
    (pure logic)      (Click wrappers)   FakeInput / FakeScheduler
           │                   │                   │
           │                   │ runtime           │ test only
           ▼                   ▼                   ▼
    drivers/factory.py    formatters.py      нет реальных драйверов
       ┌───┼───┐
       ▼   ▼   ▼
     macOS Linux Win
```

---

## Module tree

```
src/keepalive/
├── __init__.py        # re-exports, version
├── __main__.py        # python -m keepalive entry point
├── protocols.py       # InputDriver, SchedulerDriver (Protocol)
├── daemon.py          # platform‑independent loop (sleep/jiggle/key)
├── cli.py             # Click CLI: start, stop, status, run, setup, demo
├── config.py          # settings.json, constants
├── log_config.py      # rotating file logger
├── formatters.py      # TextFormatter, JsonFormatter, CaptureFormatter
├── permissions.py     # platform‑specific permission help texts
├── drivers/
│   ├── __init__.py
│   ├── factory.py     # create_input_driver() / create_scheduler()
│   ├── macos.py       # MacOSInput (Quartz) + LaunchdScheduler
│   ├── linux.py       # LinuxInput + SystemdScheduler (stub)
│   └── windows.py     # WindowsInput + TaskScheduler (stub)
```

---

## Protocols

### InputDriver

```python
class InputDriver(Protocol):
    def idle_seconds(self) -> float: ...
    def jiggle(self) -> None: ...
    def press_key(self, key_name: str) -> None: ...
    def check_permissions(self) -> dict[str, bool]: ...
```

Every platform provides a concrete implementation:

| Platform | Class | Idle source | Jiggle | Key press | Permissions |
|---|---|---|---|---|---|
| macOS | `MacOSInput` | `Quartz.CGEventSourceSecondsSinceLastEventType` | `CGEventPost(kCGEventMouseMoved)` | `osascript key code` | `osascript -e ""` probe |
| Linux | `LinuxInput` | (stub) | (stub) | (stub) | (stub) |
| Windows | `WindowsInput` | (stub) | (stub) | (stub) | (stub) |

### SchedulerDriver

```python
class SchedulerDriver(Protocol):
    def install(self, binary, schedule, idle, method, key) -> None: ...
    def uninstall(self) -> None: ...
    def is_running(self) -> bool: ...
```

| Platform | Class | Mechanism |
|---|---|---|
| macOS | `LaunchdScheduler` | plist in `~/Library/LaunchAgents/`, `launchctl load/unload` |
| Linux | `SystemdScheduler` | (stub) |
| Windows | `TaskScheduler` | (stub) |

---

## Dependency Injection

All CLI commands accept keyword‑only parameters for drivers and formatter:

```python
def cmd_start(schedule, idle, method, key, *,
              sched: SchedulerDriver | None = None,
              input_drv: InputDriver | None = None,
              fmt: Formatter | None = None) -> None:
```

- If `None`, defaults are created via factories (`create_input_driver()`,
  `create_scheduler()`).
- In tests, `FakeInput` / `FakeScheduler` / `CaptureFormatter` are injected
  instead — no global state, no `unittest.mock`.

The Click layer (CLI) populates `ctx.obj` once in `@click.group` callback and
wrapper commands forward to the DI‑enabled functions:

```python
@cli.command()
@click.pass_context
def start(ctx, schedule, idle, method, key):
    cmd_start(schedule, idle, method, key,
              sched=ctx.obj["sched"],
              input_drv=ctx.obj["input_drv"],
              fmt=ctx.obj["fmt"])
```

---

## Formatters

Three implementations, one interface:

| Class | info/success/warning/error | prompt | result | Use case |
|---|---|---|---|---|
| `TextFormatter` | `click.secho` with colour/emoji | `click.prompt` | no‑op | Interactive terminal |
| `JsonFormatter` | All suppressed | raises `RuntimeError` | `json.dumps` to stdout | `--json` flag |
| `CaptureFormatter` | Records to `self.calls` list | returns from `_prompt_responses` | Records to `self.results` | Unit tests |

Every command routes ALL user‑visible output through `fmt`:

```python
fmt.success("Agent started")
fmt.error("Already installed — stop first")
fmt.result({"status": "installed"})
```

---

## Permissions

The driver only reports factuality — `check_permissions()` returns
`{"accessibility": True/False}`. The CLI layer (`permissions.py`) adds
human‑readable help texts per platform:

```
drivers/macos.py     → "accessibility: False"
permissions.py       → "System Settings → Privacy & Security → Accessibility
                        → Add your terminal app"
cli.py (cmd_setup)   → shows instruction + retry loop
```

When a new platform is added, only the help‑text dictionary needs updating.

---

## Testing

```
tests/
├── conftest.py          # fixtures: fake_input, fake_scheduler, spy_daemon
├── fake_drivers.py      # FakeInput, FakeScheduler
├── unit/                # 56 tests — no real drivers, no OS calls
│   ├── test_config.py
│   ├── test_settings_file.py
│   ├── test_daemon.py           # daemon loop with FakeInput
│   ├── test_cli_dispatch.py     # CLI commands with CaptureFormatter
│   ├── test_formatters.py       # Text/Json/Capture
│   └── test_permissions.py      # help texts + FakeInput check
├── integration/         # macOS only (skipif on other platforms)
│   └── darwin/
│       ├── test_idle.py         # MacOSInput.idle_seconds() ≥ 0
│       └── test_daemon_live.py  # daemon + real drivers, 1 iteration
└── cli/                 # subprocess, slow, platform‑dependent
    └── test_cli_commands.py     # --help, --json status, setup, settings
```

### What gets tested where

| Layer | Isolated? | Drivers | Formatter | How |
|---|---|---|---|---|
| Unit (daemon) | ✅ | FakeInput | CaptureFormatter | `daemon(..., max_iterations=1)` |
| Unit (CLI dispatch) | ✅ | FakeInput/FakeScheduler | CaptureFormatter | Direct function calls |
| Integration (macOS) | ❌ | Real MacOSInput | N/A | `skipif` not darwin |
| CLI (subprocess) | ❌ | Real (factory) | Real (Text/Json) | `subprocess.run` |

### Testing philosophy

- Subagents are **not mocked** — Fake objects (`FakeInput`, `FakeScheduler`) are
  passed as real dependencies via DI. This avoids the fragility and magic of
  `unittest.mock`.
- The daemon loop uses `max_iterations` to exit after one cycle instead of
  running forever — no thread‑killing or timeout hacks.
- `spy_daemon` captures arguments into a mutable dict without executing the real
  loop.

---

## Adding a new platform

1. Implement `drivers/<platform>.py` — a class with `idle_seconds`,
   `jiggle`, `press_key`, `check_permissions`, and a scheduler class with
   `install`, `uninstall`, `is_running`.
2. Register in `drivers/factory.py` under the appropriate `sys.platform` check.
3. Add permission help text to `permissions.py`.
4. Add integration tests in `tests/integration/<platform>/` with `skipif`.
5. Done — no changes needed in `daemon.py`, `cli.py`, `formatters.py`, or
   existing tests.

---

## Key decisions

| Decision | Why |
|---|---|
| Protocol + DI over module‑switch | Testable without mocks; platform code stays isolated |
| Click over argparse | `--help` auto‑generated, `click.prompt` for interactive, `CliRunner` for testing |
| No Rich | Click already provides `secho`/`style`/`prompt` — enough for 6 commands |
| Plist in `macos.py` not `plist.py` | Scheduler is platform‑specific; shared code doesn't need plist logic |
| `check_permissions` in protocol | Driver reports factuality; help text stays in CLI layer |
| `max_iterations` in daemon | One knob lets unit tests exercise the loop without threads or timeouts |
