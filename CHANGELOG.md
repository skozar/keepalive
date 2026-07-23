# Changelog

## v0.6.0 (2026-07-23)
- rename: keepalive→keepalive-cli (CLI), KeepaliveUI→Keepalive (GUI), smoother icons, README rewrite
- v0.5.3: update formulas

## v0.5.3 (2026-07-23)
- fix: _menu_item→_menuitem, date picker style→TextFieldAndStepper
- docs: update README for v0.5.2 (schedule, speed, GUI, tests, CI)
- v0.5.2: update formulas

## v0.5.2 (2026-07-23)
- fix: correct backslash escaping in release target
- fix: remove broken sed line in release target
- fix: speed up CLI (--onedir), fix Settings NSPopUpButton, dual CI
- chore: add market-analysis.md (gitignored)
- docs: add donate badges (GitHub Sponsors + Buy Me a Coffee)
- ci: skip launchctl test on Linux, handle FileNotFoundError
- ci: make pyobjc/rumps darwin-only, unblock Ubuntu CI
- chore: remove .coverage from tracking
- ci: add GitHub Actions test workflow with coverage
- v0.5.1: update formulas

## v0.5.2 (2026-07-23)
- fix: remove broken sed line in release target
- fix: speed up CLI (--onedir), fix Settings NSPopUpButton, dual CI
- chore: add market-analysis.md (gitignored)
- docs: add donate badges (GitHub Sponsors + Buy Me a Coffee)
- ci: skip launchctl test on Linux, handle FileNotFoundError
- ci: make pyobjc/rumps darwin-only, unblock Ubuntu CI
- chore: remove .coverage from tracking
- ci: add GitHub Actions test workflow with coverage
- v0.5.1: update formulas

## v0.5.2 (2026-07-23)
- fix: speed up CLI (--onedir), fix Settings NSPopUpButton, dual CI
- chore: add market-analysis.md (gitignored)
- docs: add donate badges (GitHub Sponsors + Buy Me a Coffee)
- ci: skip launchctl test on Linux, handle FileNotFoundError
- ci: make pyobjc/rumps darwin-only, unblock Ubuntu CI
- chore: remove .coverage from tracking
- ci: add GitHub Actions test workflow with coverage
- v0.5.1: update formulas

## v0.5.1 (2026-07-23)
- chore: move gui/ back to src/gui/, add --paths src
- feat: auto-start/stop, toggle menu, status --json, 08-17 default
- fix: restore v0.5.0 changelog entries
- v0.5.0: update formulas

## v0.5.0 (2026-07-23)
- feat: add app icon (light blue circle outline)
- chore: unify CLI+UI release, auto-changelog from git log
- chore: rename GUI bundle to KeepaliveUI (case-insensitive fix)


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
