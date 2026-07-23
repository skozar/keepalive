# keepalive

[![tests](https://github.com/skozar/keepalive/actions/workflows/test.yml/badge.svg)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![21 tests](https://img.shields.io/badge/tests-21-success)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![sponsor](https://img.shields.io/badge/sponsor-30363D?logo=github-sponsors&style=flat)](https://github.com/sponsors/skozar)
[![buy me a coffee](https://img.shields.io/badge/buy_me_a_coffee-FF813F?logo=buymeacoffee&style=flat)](https://buymeacoffee.com/skozar)
[![ko-fi](https://img.shields.io/badge/ko--fi-FF5E5B?logo=kofi&style=flat)](https://ko-fi.com/skozar)

Stay green. Simulates macOS input activity only when you're away — so messengers don't mark you "Away."

---

## How it works

- Checks system idle time via Quartz every 30–60 seconds.
- If you haven't touched the mouse or keyboard for **180 seconds** (default) and
  the current time falls within your configured window — it fires.
- Firing means either nudging the cursor 1 px, pressing a harmless key (F13), or
  both with a 50 ms gap — imperceptible while you actually work.
- Runs as a launchd agent. Survives reboots. Logs to
  `~/Library/Logs/keepalive/keepalive.log` (auto‑rotated, 5 × 1 MB).

| Messenger | Away after | keepalive beats it? |
|---|---|---|
| Slack | ~10 min | ✅ fires at 3 min |
| Discord | ~5 min | ✅ fires at 3 min |
| Microsoft Teams | ~5 min | ✅ fires at 3 min |
| Mattermost | configurable | ✅ fires at 3 min |

The `--idle` threshold sits well below every messenger's away timer — you stay
visible without unnecessary jiggling.

### What it will NOT do

- Prevent display sleep — use `caffeinate` or Amphetamine.
- Simulate activity in browser apps (Figma, Google Docs) — they watch DOM
  events, not macOS idle.
- Keep SSH or VPN sessions alive — use protocol‑level keepalives.
- Run on cloud VMs without a GUI.

---

## Install

### Recommended — menu bar app

```bash
brew install keepalive
```

You get:

- A menu bar icon that shows whether the agent is running (green dot) or
  stopped (grey dot).
- A native **Settings…** dialog to pick your schedule, method, key, and idle
  threshold — saved to `~/.config/keepalive/settings.json`.
- Auto‑start on login (the app launches the CLI agent for you).
- **Keepalive** appears in Spotlight and Launchpad — launch it, forget it.

```text
┌────── keepalive ──────┐
│                       │
│         ●             │   ● = running
│                       │   ○ = stopped
├───────────────────────┤
│ Start                │   hidden when running
│ Stop                 │   hidden when stopped
│ Settings…            │
│ Quit                │
└───────────────────────┘
```

Grant Accessibility permission once: **System Settings → Privacy & Security →
Accessibility** → add `/opt/homebrew/bin/keepalive-cli`.

### CLI only — for minimalists

```bash
brew install keepalive-cli
```

No menu bar, no GUI. Just the binary on your PATH.

```bash
keepalive-cli start                   # defaults: 08:00–17:00, 180 s idle, mouse
keepalive-cli start --schedule 09:00-18:00 --method key
keepalive-cli status                  # is it running? what are the settings?
keepalive-cli status --json           # machine‑readable for scripts
keepalive-cli stop                    # unload the agent
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
make gui                           # PyInstaller → dist/Keepalive.app
make test                          # 21 tests, 7 files
make release VERSION=0.6.0         # Test, build, tag, GitHub Release, update tap
```

The release packages `keepalive-cli-{version}.tar.gz` (CLI) and
`Keepalive-{version}.zip` (GUI). Both are uploaded to GitHub Releases and served
by the Homebrew tap.

CI runs on **Ubuntu** (pure Python, ~30 s) and **macOS** (GUI imports, ~2 min).
Public repo — unlimited free minutes.
