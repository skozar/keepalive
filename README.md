# keepalive

Keep macOS "active" for Microsoft Teams during chosen hours — moves the cursor or presses a key only when the system is truly idle.

## Install

```bash
brew tap skozar/tap
brew trust skozar/tap
brew install keepalive
```

## Usage

```bash
# Mouse jiggle (default)
keepalive start --schedule 04:00-12:00 --idle 180

# Key press (F13)
keepalive start --method key

# Both — maximum reliability
keepalive start --method both --key f14

# Status and stop
keepalive status
keepalive stop
```

| Option | Values | Default | Description |
|---|---|---|---|
| `--schedule` | `HH:MM-HH:MM` | `04:00-12:00` | Active time window |
| `--idle` | seconds | `180` | Idle threshold before firing |
| `--method` | `mouse`, `key`, `both` | `mouse` | How to reset idle timer |
| `--key` | `f13`, `f14`, `f15` | `f13` | Key to press (when using `key`/`both`) |

## Build (dev)

```bash
make build                       # PyInstaller → dist/keepalive
make release VERSION=0.2.0       # Build, tag, release, and update homebrew-tap
```

## How it works

- Checks system idle time every 30–60 seconds
- If idle exceeds the configured threshold — fires the chosen method (mouse jiggle and/or key press)
- Only active during the configured time window (default: 04:00–12:00)
- Runs as a launchd agent, survives reboots
- Accessibility permission required: add `/opt/homebrew/bin/keepalive` in System Settings → Privacy & Security → Accessibility
