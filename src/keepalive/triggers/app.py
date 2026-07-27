"""App trigger — detect running apps by bundle ID (macOS only)."""

from __future__ import annotations

import platform

_IS_DARWIN = platform.system() == "Darwin"


def get_running_apps() -> list[str]:
    """Return bundle IDs of currently running GUI applications."""
    if not _IS_DARWIN:
        return []
    try:
        from Cocoa import NSWorkspace  # type: ignore[import-untyped]  # noqa: E501, PLC0415

        ws = NSWorkspace.sharedWorkspace()
        running = ws.runningApplications()
        result: list[str] = []
        for app in running:
            if app.activationPolicy() == 0:
                bid = app.bundleIdentifier()
                if bid:
                    result.append(str(bid))
        return result
    except Exception:
        return []


def list_installed_apps() -> list[dict[str, str]]:
    """Return all installed .app bundles as [{name, bundle_id}, ...]."""
    if not _IS_DARWIN:
        return []
    try:
        import os

        results: list[dict[str, str]] = []
        search_paths = [
            "/Applications",
            "/System/Applications",
            os.path.expanduser("~/Applications"),
        ]
        for base in search_paths:
            if not os.path.isdir(base):
                continue
            for entry in os.listdir(base):
                if not entry.endswith(".app"):
                    continue
                path = os.path.join(base, entry)
                plist = os.path.join(path, "Contents", "Info.plist")
                name = entry[:-4]
                bid = ""
                if os.path.isfile(plist):
                    try:
                        import plistlib

                        with open(plist, "rb") as f:
                            info = plistlib.load(f)
                        bid = info.get("CFBundleIdentifier", "")
                    except Exception:
                        pass
                if name:
                    results.append({"name": name, "bundle_id": str(bid)})
        return results
    except Exception:
        return []


def search_apps(query: str) -> list[dict[str, str]]:
    """Filter installed apps by name or bundle ID substring."""
    q = query.lower()
    return [
        a for a in list_installed_apps() if q in a["name"].lower() or q in a["bundle_id"].lower()
    ]
