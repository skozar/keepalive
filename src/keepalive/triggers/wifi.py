"""WiFi trigger — current SSID and available network scan (macOS only)."""

from __future__ import annotations

import platform

_IS_DARWIN = platform.system() == "Darwin"

if _IS_DARWIN:
    import objc  # type: ignore[import-untyped]  # noqa: PLC0415
    from Foundation import NSBundle  # type: ignore[import-untyped]  # noqa: PLC0415

    _bundle = NSBundle.bundleWithIdentifier_("com.apple.CoreWLAN")
    if _bundle is not None:
        objc.loadBundle("CoreWLAN", _bundle, {"CoreWLAN": ["CWWiFiClient"]})


def get_current_ssid() -> str | None:
    """SSID of the currently connected WiFi network, or *None*."""
    if not _IS_DARWIN:
        return None
    try:
        client = objc.lookUpClass("CWWiFiClient").sharedWiFiClient()
        iface = client.interface()
        if iface is None:
            return None
        ssid = iface.ssid()
        return str(ssid) if ssid else None
    except Exception:
        return None


def list_available_ssids() -> list[str]:
    """Scan visible WiFi networks.  May require Location Services."""
    if not _IS_DARWIN:
        return []
    try:
        client = objc.lookUpClass("CWWiFiClient").sharedWiFiClient()
        iface = client.interface()
        if iface is None:
            return []
        nets, err = iface.scanForNetworksWithName_error_(None, None)
        if err or not nets:
            return []
        results: list[str] = []
        for net in nets:
            ssid = net.ssid()
            if ssid:
                results.append(str(ssid))
        return list(set(results))  # dedupe
    except Exception:
        return []
