# keepalive-cli

[![tests](https://github.com/skozar/keepalive/actions/workflows/test.yml/badge.svg)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![81 tests](https://img.shields.io/badge/tests-81-success)](https://github.com/skozar/keepalive/actions/workflows/test.yml)
[![sponsor](https://img.shields.io/badge/sponsor-30363D?logo=github-sponsors&style=flat)](https://github.com/sponsors/skozar)
[![buy me a coffee](https://img.shields.io/badge/buy_me_a_coffee-FF813F?logo=buymeacoffee&style=flat)](https://buymeacoffee.com/skozar)
[![ko-fi](https://img.shields.io/badge/ko--fi-FF5E5B?logo=kofi&style=flat)](https://ko-fi.com/skozar)
[![license](https://img.shields.io/badge/license-PolyForm_Noncommercial-8A2BE2?style=flat)](LICENSE)

Stay green in messengers — without touching your Mac. Simulates input activity
only when you're away so Slack / Teams / Discord never mark you "Away."

---

## How it works

- Checks system idle time via Quartz every 30–60 seconds.
- If you haven't touched the mouse or keyboard for **180 seconds** (default) and
  any trigger condition is met (schedule / WiFi / app) — it fires.
- Firing means: nudging the cursor 1 px, pressing a harmless key (F13), or both
  with a 50 ms gap — imperceptible while you actually work.
- Runs as a launchd agent. Survives reboots. Logs to
  `~/Library/Logs/keepalive/keepalive.log` (auto‑rotated, 5 × 1 MB).
- Configuration is stored in `~/.config/keepalive/settings.json` — readable,
  editable, survives reinstalls.
- Optional **Caffeinate mode** prevents system or display sleep.
- Three **trigger types** (OR‑logic): schedule, WiFi network, running app.
- Built on a multi‑platform architecture (Protocol + DI) with macOS drivers
  shipped, Linux and Windows stubs ready. See [ARCHITECTURE.md](ARCHITECTURE.md).

| Messenger | Away after | keepalive beats it? |
|---|---|---|
| Slack | ~10 min | ✅ fires at 3 min |
| Discord | ~5 min | ✅ fires at 3 min |
| Microsoft Teams | ~5 min | ✅ fires at 3 min |
| Mattermost | configurable | ✅ fires at 3 min |

### What it will NOT do

- Simulate activity in browser apps (Figma, Google Docs) — they watch DOM
  events, not macOS idle.
- Keep SSH or VPN sessions alive — use protocol‑level keepalives.
- Run on cloud VMs without a GUI.

---

## Quick start

```bash
brew install keepalive-cli
```

```bash
keepalive-cli setup        # interactive permission check
keepalive-cli start        # defaults: 08:00–17:00, 180 s idle, mouse
keepalive-cli status       # is it running?
keepalive-cli stop         # unload the agent
keepalive-cli run          # foreground test mode (Ctrl+C to exit)
```

---

## Commands

| Command | Description |
|---|---|
| `start` | Install and start the agent (launchd). `--schedule`, `--idle`, `--method`, `--key` overrides |
| `stop` | Stop and uninstall the agent |
| `status` | Show agent status and current settings |
| `run` | Foreground test mode (Ctrl+C to stop). Same flags as `start` |
| `setup` | Interactive permission check — guides you through Accessibility grant |
| `demo` | Interactive diagnostic tests (mouse, key, idle, scheduler) |
| `config export` | Print the full configuration as JSON |
| `config replace --file PATH` | Replace config from a JSON file |
| `config replace --stdin` | Replace config from stdin |
| `config setup` | Interactive dashboard — configure everything visually |

All commands support `--json` for scripts:

```bash
keepalive-cli --json status          # {"running": false}
keepalive-cli --json config export   # full config as JSON
keepalive-cli config replace --stdin < my_config.json
```

---

## Configuration

On first start, keepalive writes defaults to `~/.config/keepalive/settings.json`:

```json
{
  "activity": {
    "idle": 180,
    "method": "mouse",
    "key": "f13"
  },
  "caffeinate": {
    "enabled": false,
    "mode": "display",
    "lid_closed": false
  },
  "triggers": {
    "schedule": {
      "enabled": true,
      "from": "08:00",
      "to": "17:00"
    },
    "wifi": {
      "enabled": false,
      "ssids": [],
      "on_match": "start",
      "on_lost": "stop"
    },
    "app": {
      "enabled": false,
      "apps": [],
      "on_active": "start",
      "on_inactive": "schedule"
    }
  }
}
```

Interactive setup:

```bash
keepalive-cli config setup
```

This opens a terminal dashboard where you can toggle settings, add WiFi
networks (with autocomplete from visible networks), add apps
(autocomplete from installed apps), and configure caffeinate mode — all
with arrow keys, no manual JSON editing.

---

## Triggers (OR logic)

The agent fires when **any** trigger condition is True:

| Trigger | Description |
|---|---|
| **Schedule** | Fire during specified hours (e.g. 09:00–18:00) |
| **WiFi** | Fire when connected to a specific network (SSID) |
| **App** | Fire when a specific app is running (bundle ID) |

WiFi and app triggers use `on_match` / `on_active` (what happens when
condition becomes True) and `on_lost` / `on_inactive` (what happens when
condition becomes False). Currently supported actions: `start`, `stop`,
`schedule`.

---

## Caffeinate mode

Prevents the system from sleeping while keepalive is running.

| Mode | Prevents | Use case |
|---|---|---|
| `display` | Display sleep | You're away but want the screen on |
| `system` | System sleep (includes display) | Lid-closed operation, long-running tasks |

When `lid_closed` is enabled, Caffeinate automatically switches to
`system` mode. The dashboard (`config setup`) warns if your idle
threshold is longer than the system sleep timer and suggests enabling
Caffeinate.

---

## GUI Integration

External tools (shell scripts, GUI apps, automation) can manage the
configuration through `config export` / `config replace`:

```bash
# Read current config
cfg=$(keepalive-cli --json config export)

# Modify with jq
echo "$cfg" | jq '.activity.idle = 300' > new.json

# Write back
keepalive-cli config replace --file new.json
```

`config replace` validates the entire config before writing — if any
field is missing or invalid, it prints errors and exits with code 1.

---

## Options

| Flag | Values | Default | Description |
|---|---|---|---|
| `--json` | flag | off | JSON output for all commands |
| `--schedule` | `HH:MM-HH:MM` | `08:00-17:00` | Hours when keepalive is active |
| `--idle` | seconds | `180` | System-idle threshold |
| `--method` | `mouse` / `key` / `both` | `mouse` | How to reset the idle timer |
| `--key` | `f13` / `f14` / `f15` | `f13` | Key to press |

---

## Build (dev)

```bash
pdm install --dev
make build                         # PyInstaller → dist/keepalive-cli/
make test                          # 69 unit tests
make release VERSION=0.10.0        # Test, build, tag, GitHub Release, update tap
```

CI runs on **Ubuntu** (unit tests, ~30 s). Public repo — unlimited free
minutes. Integration and CLI tests run on macOS only.

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) — protocols, drivers, formatters,
trigger system, test strategy, and how to add a new platform.

---

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — free for personal, educational, and
non-commercial use. Commercial use requires a paid license. Contact skozar@
for terms.
