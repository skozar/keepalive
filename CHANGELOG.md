# Changelog

## v0.5.0 (2026-07-23)


## v0.4.0 (2026-07-22)

### GUI
- Native macOS settings: NSDatePicker for schedule (From/To), NSPopUpButton for method and key
- Fixed duplicate Quit in menu bar (`quit_button=None`)
- Template icons: filled circle (running) / empty circle (stopped)
- Save settings → auto-restart keepalive with new flags
- GUI source moved to `src/gui/` (PyInstaller-compatible)

### Build
- Unified `make release VERSION=x.y.z` — builds CLI + GUI, tags, creates GitHub releases, updates both brew formulas in homebrew-tap
- Tap update at the very end (only after all builds and tags succeed)
- Icons bundled via `--add-data`

## v0.3.0 (2026-07-21)

- Migrated to PDM + `src/keepalive/` package
- Tests: 14 tests passing (config, plist, CLI smoke)
- Makefile: `test` → `build` → `release` pipeline
- README: honest "When to use" section (messaging apps only)

## v0.2.1 (2026-07-20)

- `keepalive status` shows active settings (schedule, idle, method, key) by parsing plist

## v0.2.0 (2026-07-20)

- `--method` flag: `mouse`, `key`, `both`
- `--key` flag: `f13`, `f14`, `f15` (via osascript)
- Automated release: `make release VERSION=x.y.z`

## v0.1.0 (2026-07-20)

- Initial CLI: `start`, `stop`, `status`, `run`
- Launchd management
- Rotating logs
- PyInstaller build + Homebrew formula
