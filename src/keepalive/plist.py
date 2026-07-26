"""Launchd plist template and helpers."""

import os
import plistlib
import sys
from pathlib import Path
from typing import Any

from keepalive.config import PLIST_PATH

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{binary}</string>
        <string>--schedule</string>
        <string>{schedule}</string>
        <string>--idle</string>
        <string>{idle}</string>
        <string>--method</string>
        <string>{method}</string>
        <string>--key</string>
        <string>{key}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_file}</string>
    <key>StandardErrorPath</key>
    <string>{log_file}</string>
</dict>
</plist>
"""


def binary_path() -> str:
    """Absolute path to this binary. Works for both python and PyInstaller."""
    return os.path.abspath(sys.argv[0])


def read_plist_config(plist_path: Path | None = None) -> dict[str, str] | None:
    """Parse plist ProgramArguments into a {key: value} dict. None if no plist."""
    target = plist_path if plist_path is not None else PLIST_PATH
    if not target.exists():
        return None
    with open(target, "rb") as f:
        plist: dict[str, Any] = plistlib.load(f)
    args: list[str] = plist.get("ProgramArguments", [])
    cfg: dict[str, str] = {}
    for i, arg in enumerate(args):
        if arg.startswith("--") and i + 1 < len(args):
            cfg[arg.lstrip("-")] = args[i + 1]
    return cfg
