# keepalive

[![tests](https://github.com/skozar/keepalive/actions/workflows/test.yml/badge.svg)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![coverage](https://img.shields.io/badge/coverage-21_tests-success)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![sponsor](https://img.shields.io/badge/sponsor-30363D?logo=github-sponsors&style=flat)](https://github.com/sponsors/skozar)
[![buy me a coffee](https://img.shields.io/badge/donate-FF813F?logo=buymeacoffee&style=flat)](https://buymeacoffee.com/skozar)

Stay green. Simulates macOS input activity only when you're away — so messaging apps don't mark you as "Away" or "Idle."

## What it solves

Slack, Discord, Microsoft Teams, and Mattermost all detect user presence through macOS idle time. After 5–10 minutes of inactivity, they switch your status to "Away." keepalive resets the idle timer by moving the cursor a pixel or pressing a harmless key — imperceptible, only when the system is genuinely idle, and only during your configured hours.

| App | Away after |
|---|---|
| Slack | ~10 min |
| Discord | ~5 min |
| Microsoft Teams | ~5 min |
| Mattermost | configurable |

### What it will NOT do

- Prevent display sleep — use `caffeinate` or Amphetamine
- Simulate activity in browser-based apps (Figma, Google Docs) — they use DOM events, not macOS idle
- Keep SSH or VPN sessions alive — use protocol-level keepalives
- Work on cloud VMs without a GUI

## Install

### CLI

```bash
brew tap skozar/tap
brew trust skozar/tap
brew install keepalive
```

Grant Accessibility permission: **System Settings → Privacy & Security → Accessibility** → add `/opt/homebrew/bin/keepalive`.

### GUI (menu bar app)

```bash
brew install keepalive-ui
```

Launch **Keepalive** from Spotlight or Launchpad. Configure schedule, method, and idle threshold from the menu bar icon. Settings are stored in `~/.config/keepalive/settings.json` and survive reinstalls.

## Usage

```bash
# Mouse jiggle (default: 08:00–17:00, idle > 3 min)
keepalive start

# Key press (F13)
keepalive start --method key

# Both — maximum reliability
keepalive start --method both --key f14

# Custom schedule
keepalive start --schedule 04:00-12:00 --idle 180

# Check status and settings
keepalive status

# Machine-readable status
keepalive status --json

# Stop and uninstall
keepalive stop
```

| Option | Values | Default | Description |
|---|---|---|---|
| `--schedule` | `HH:MM-HH:MM` | `08:00-17:00` | Active time window |
| `--idle` | seconds | `180` | Idle threshold before firing |
| `--method` | `mouse`, `key`, `both` | `mouse` | How to reset idle timer |
| `--key` | `f13`, `f14`, `f15` | `f13` | Key to press (when using `key`/`both`) |

## How it works

- Checks system idle time via Quartz every 30–60 seconds
- If idle exceeds the configured threshold and current time is within the active window — fires the chosen method
- When using `both`, mouse jiggle and key press run with a 50ms gap (two separate HID events)
- Runs as a launchd agent, survives reboots
- Logs to `~/Library/Logs/keepalive/keepalive.log` (auto-rotated, 5 × 1 MB)
- CLI binary starts in ~0.07s (PyInstaller `--onedir`, no extraction overhead)

## Tests

```bash
pdm install --dev
pdm run pytest -v
```

21 tests across 7 files. CI runs on both **Ubuntu** (pure Python, ~30s) and **macOS** (GUI imports, ~2min). Public repo — unlimited free minutes.

## Build (dev)

```bash
make build                       # PyInstaller --onedir → dist/keepalive/
make gui                         # PyInstaller --windowed → dist/KeepaliveUI.app
make release VERSION=0.5.2       # Test, build CLI+GUI, tag, GitHub Release, update tap
```

The release packages a `keepalive-{version}.tar.gz` (CLI) and `KeepaliveUI-{version}.zip` (GUI). Both are uploaded to GitHub Releases and served via Homebrew tap.
