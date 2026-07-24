# Roadmap

Features competitors have that keepalive doesn't — prioritized by user interest,
not by release version.

---

## 1. Boost Mode

### What it is

A more aggressive movement pattern for apps that detect "too simple" jiggle
(Figma, browser IDEs, Google Docs). Instead of 1 px nudge, the cursor moves in
a circle or zigzag — harder to filter out.

### How it works

- New method: `boost` (alongside `mouse`, `key`, `both`)
- Cursor draws a small circle (diameter ~5–10 px) over 200 ms
- Fires at the same `--idle` interval as regular mode
- No key press — mouse-only for canvas-based apps

### Technical requirements

- `Quartz.CGEventPost` with computed arc coordinates
- Arc approximated by 8–12 discrete moves, 15–20 ms apart
- Same `--idle` threshold, same `in_active_window()` check
- Guard: boost should NOT trigger during user interaction (check idle first)

### Example

```bash
keepalive-cli start --schedule 08:00-17:00 --method boost --idle 180
```

---

## 2. Caffeinate Mode

### What it is

Prevent display sleep or system sleep — a deliberate departure from keepalive's
"only simulate activity" philosophy. Useful for presentations, coding marathons,
or watching videos where you don't want screen dimming.

### How it works

- New `--mode` flag: `activity` (default, current behavior) / `caffeinate`
- `caffeinate` mode wraps `IOPMAssertion` or subprocess `caffeinate`
- Two sub-modes:
  - `display` — prevent display sleep (screen stays on)
  - `system` — prevent system sleep (mac keeps running)
- Can coexist with schedule/idle: only caffeinate during active hours

### Technical requirements

- `IOPMAssertionCreateWithName(kIOPMAssertionTypePreventUserIdleDisplaySleep, ...)`
- Or `subprocess.Popen(["caffeinate", "-d"])` — simpler, same result
- Assertion released when agent stops or outside schedule
- Optional warning in CLI: "caffeinate overrides macOS energy saver — may drain battery"

### Example

```bash
keepalive-cli start --schedule 09:00-18:00 --mode caffeinate --caffeinate display
```

---

## 3. WiFi Triggers

### What it is

Auto-start/stop based on connected WiFi network. No schedule needed — tied to
physical presence (office, co-working, home).

### How it works

- New CLI flag: `--wifi OfficeWiFi,HomeWiFi`
- Every 30 seconds: read current SSID via `CoreWLAN`
- If SSID matches any in the list → agent starts (or stays running)
- If SSID doesn't match → agent stops (if started by WiFi)
- Falls back to `--schedule` if WiFi changes mid-day?

### Technical requirements

- PyObjC `CoreWLAN.CWWiFiClient.sharedWiFiClient().interface().ssid()`
- Polling at 30-second intervals (read-only, no battery impact)
- State machine: WiFi match → start, WiFi lost → graceful stop
- Config stored in plist/settings.json
- Guard: respect `--idle` threshold even on WiFi start
- Edge case: no WiFi (Ethernet) → fall back to schedule

### Example

```bash
keepalive-cli wifi add --ssid OfficeWiFi
keepalive-cli wifi remove --ssid CoffeeShopWiFi
keepalive-cli start --wifi "OfficeWiFi,HomeWiFi" --schedule 08:00-20:00
```

### UX considerations

- CLI: `keepalive-cli wifi list` shows current network + configured list
- GUI: checkbox to enable WiFi triggers + list of configured networks
- Default: WiFi triggers disabled — user must opt in

---

## 4. App Triggers

### What it is

Agent activates when a specific app is running (e.g., Zoom, Teams, Slack huddle).

### How it works

- New CLI flag: `--apps Zoom.us,Microsoft Teams`
- Every 5–10 seconds: poll `NSWorkspace.runningApplications`
- If any target app is in the foreground or running → agent active
- All apps closed → agent returns to schedule-based behavior

### Technical requirements

- PyObjC `NSWorkspace.sharedWorkspace().runningApplications()`
- Check by bundle ID (e.g., `us.zoom.xos`) or display name
- Polling at 5–10 second intervals — negligible CPU
- Respect `--idle`: app is running BUT user is typing → don't jiggle
- Conflict resolution: app trigger + schedule → app trigger wins

### Example

```bash
keepalive-cli start --apps "us.zoom.xos,com.microsoft.teams2" --schedule 08:00-18:00
```

### UX considerations

- `keepalive-cli apps list` — show configured apps
- `keepalive-cli apps suggest` — list currently running `.app` names for easy setup
- GUI: text field or picker to add/remove apps by name
- Caveat: app name might change across versions (Teams Classic vs Teams 2.0)

---

## 5. Lid-Closed Support

### What it is

Agent keeps working when MacBook lid is closed. Without this, all activity
simulation stops the moment you close the lid — the laptop sleeps.

### How it works

- New CLI flag: `--lid-closed`
- Creates `IOPMAssertion` of type `kIOPMAssertionTypePreventUserIdleSystemSleep`
- Same as `caffeinate -s` but scoped to "only when lid is closed"
- Safety: requires `--battery-guard` (stop at X% battery)
- Safety: active only during `--schedule` window

### Technical requirements

- `IOPMAssertionCreateWithName` for system sleep prevention
- Detect lid state via `IOKit` (`kIOPMModelLidState`) or `ioreg`
- Only apply assertion when lid IS closed + schedule is active
- `--battery-guard <percent>`: stop agent and release assertion below threshold
- Log warning: "lid-closed active — battery at 35%"

### Safety considerations

- **Risk:** battery drain in backpack if user forgets to stop
- **Mitigation 1:** `--battery-guard 20` — auto-stop below 20%
- **Mitigation 2:** `--require-power` — only lid-closed when on AC power
- **Mitigation 3:** notification on lid-close: "keepalive active, battery at 72%"
- **Mitigation 4:** integration with `pmset` to check current power source

### Example

```bash
keepalive-cli start --lid-closed --battery-guard 20 --schedule 08:00-17:00
```

---

## 6. Cross-Platform (Linux + Windows)

### What it is

CLI agent running on Linux and Windows — same `start`/`stop`/`status` commands,
same config format. No GUI (platform-specific GUI is out of scope).

### Platform breakdown

| Feature | macOS | Linux | Windows |
|---|---|---|---|
| Idle detection | Quartz | XScreenSaver (X11) | `GetLastInputInfo` (user32) |
| Mouse move | Quartz/CGEvent | python-xlib / pyautogui | pyautogui |
| Key press | Quartz/CGEvent | python-xlib / pyautogui | pyautogui |
| Daemon | launchd | systemd (user) | Task Scheduler / WinSW |
| Config | plist | JSON | JSON |
| Log | Unified Logging | file | file |
| GUI | rumps (Cocoa) | ❌ | ❌ |

### Technical requirements

- Abstract input layer: `InputBackend` protocol with per-platform impl
- Abstract daemon layer: `DaemonManager` protocol
- Config: migrate from plist to JSON (already used by settings.json)
- Tests: CI expands to Ubuntu (already ✅) + Windows (new)
- CLI: identical commands on all platforms
- `brew install keepalive-cli` on macOS, `pip install` or `apt` on others

### Non-goals

- GUI on Linux/Windows (CLI-only)
- System tray on non-macOS
- launchd/systemd parity — just "install daemon" abstract command

### Migration notes

- plist → JSON: backward-compatible read for one release
- Config path: `~/.config/keepalive/config.json` (XDG-compliant)
- Existing macOS users unaffected — config auto-converted on first run

---

## Priority Notes

Not ranked yet — all items are "interesting but unscheduled."

Items 1–5 are **macOS-only, Python + PyObjC — low risk, high feasibility.**

Item 6 is **multi-platform, requires infrastructure — v2.0-level effort.**

| # | Feature | Effort | User Value | Risk |
|---|---|---|---|---|
| 1 | Boost | 30 min | Medium | None |
| 2 | Caffeinate | 1 hr | High | Battery drain |
| 3 | WiFi Triggers | 2–3 hrs | High | SSID polling edge cases |
| 4 | App Triggers | 2–3 hrs | High | App name fragility |
| 5 | Lid-closed | 2 hrs + tests | High | Battery drain in backpack |
| 6 | Cross-Platform | 2–4 weeks | Medium | Test matrix explosion |
