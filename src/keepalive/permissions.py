"""Platform-specific permission help texts.

Keep this separate from drivers — the driver only reports factuality
(dict of bool), while *how* to explain to the user belongs here in the
CLI layer.
"""

import sys

_PERMISSION_HELP: dict[str, dict[str, str]] = {
    "darwin": {
        "accessibility": (
            "System Settings → Privacy & Security → Accessibility\n"
            "→ Add your terminal app (Terminal.app / iTerm2 / VS Code / warp)\n"
            "→ Or run: open "
            '"x-apple.systempreferences:com.apple.preference.security'
            '?Privacy_Accessibility"'
        ),
    },
    "linux": {
        "input": ("Run:  sudo usermod -aG input $USER\nThen log out and back in."),
    },
    "win32": {},
}


def help_for_platform(permission_name: str, platform: str | None = None) -> str:
    """Return the human-readable help text for *permission_name*.

    *platform* defaults to ``sys.platform``.
    """
    platform = platform or sys.platform
    key = platform
    if platform.startswith("linux"):
        key = "linux"
    return _PERMISSION_HELP.get(key, {}).get(permission_name, "")
