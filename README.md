# keepalive-cli

[![tests](https://github.com/skozar/keepalive/actions/workflows/test.yml/badge.svg)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![25 tests](https://img.shields.io/badge/tests-25-success)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![sponsor](https://img.shields.io/badge/sponsor-30363D?logo=github-sponsors&style=flat)](https://github.com/sponsors/skozar)
[![buy me a coffee](https://img.shields.io/badge/buy_me_a_coffee-FF813F?logo=buymeacoffee&style=flat)](https://buymeacoffee.com/skozar)
[![ko-fi](https://img.shields.io/badge/ko--fi-FF5E5B?logo=kofi&style=flat)](https://ko-fi.com/skozar)

Stay green in messengers — without touching your Mac. Simulates input activity
only when you're away so Slack / Teams / Discord never mark you "Away."

---

## How it works

- Checks system idle time via Quartz every 30–60 seconds.
- If you haven't touched the mouse or keyboard for **180 seconds** (default) and
  the current time falls within your configured window — it fires.
- Firing means: nudging the cursor 1 px, pressing a harmless key (F13), or both
  with a 50 ms gap — imperceptible while you actually work.
- Runs as a launchd agent. Survives reboots. Logs to
  `~/Library/Logs/keepalive/keepalive.log` (auto‑rotated, 5 × 1 MB).
- Configuration is stored in `~/.config/keepalive/settings.json` — readable,
  editable, survives reinstalls.

| Messenger | Away after | keepalive beats it? |
|---|---|---|
| Slack | ~10 min | ✅ fires at 3 min |
| Discord | ~5 min | ✅ fires at 3 min |
| Microsoft Teams | ~5 min | ✅ fires at 3 min |
| Mattermost | configurable | ✅ fires at 3 min |

### What it will NOT do

- Prevent display sleep — use `caffeinate` or Amphetamine.
- Simulate activity in browser apps (Figma, Google Docs) — they watch DOM
  events, not macOS idle.
- Keep SSH or VPN sessions alive — use protocol‑level keepalives.
- Run on cloud VMs without a GUI.

---

## Install

```bash
brew install keepalive-cli
```

Starts in ~0.07s (`--onedir` build). Binaries are on your PATH.

```bash
keepalive-cli start                   # defaults: 08:00–17:00, 180 s idle, mouse
keepalive-cli start --schedule 09:00-18:00 --method key
keepalive-cli status                  # is it running? what are the settings?
keepalive-cli status --json           # machine‑readable for scripts
keepalive-cli stop                    # unload the agent
keepalive-cli run                     # foreground test mode (Ctrl+C to exit)
```

Grant Accessibility permission once: **System Settings → Privacy & Security →
Accessibility** → add `/opt/homebrew/bin/keepalive-cli`.

---

## Configure

On first start, keepalive-cli writes its defaults to
`~/.config/keepalive/settings.json`:

```json
{
  "schedule_from": "08:00",
  "schedule_to": "17:00",
  "idle": 180,
  "method": "mouse",
  "key": "f13"
}
```

Edit this file to change settings permanently — no more CLI flags needed:

```bash
# Change schedule to 09:00–18:00 and switch to key press
keepalive-cli stop
# edit ~/.config/keepalive/settings.json …
keepalive-cli start   # picks up new settings
```

---

## Options

| Flag | Values | Default | Description |
|---|---|---|---|
| `--schedule` | `HH:MM-HH:MM` | `08:00-17:00` | Hours when keepalive is active |
| `--idle` | seconds | `180` | System-idle threshold before firing |
| `--method` | `mouse` / `key` / `both` | `mouse` | How to reset the idle timer |
| `--key` | `f13` / `f14` / `f15` | `f13` | Key to press (for `key` and `both`) |

---

## Build (dev)

```bash
pdm install --dev                  # one-time setup
make build                         # PyInstaller → dist/keepalive-cli/
make test                          # 25 tests, 5 files
make release VERSION=0.7.0         # Test, build, tag, GitHub Release, update tap
```

CI runs on **Ubuntu** (22 tests, ~30 s). Public repo — unlimited free minutes.
