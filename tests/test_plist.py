import plistlib

from keepalive.plist import read_plist_config

PLIST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/keepalive-cli</string>
        <string>--schedule</string>
        <string>10:00-11:00</string>
        <string>--idle</string>
        <string>120</string>
        <string>--method</string>
        <string>both</string>
        <string>--key</string>
        <string>f14</string>
    </array>
</dict>
</plist>
"""


class TestReadPlistConfig:
    def test_full_config(self, tmp_path):
        plist_file = tmp_path / "com.keepalive.jiggle.plist"
        plist_file.write_text(PLIST_XML)

        cfg = read_plist_config(plist_file)
        assert cfg == {
            "schedule": "10:00-11:00",
            "idle": "120",
            "method": "both",
            "key": "f14",
        }

    def test_no_file(self, tmp_path):
        cfg = read_plist_config(tmp_path / "nonexistent.plist")
        assert cfg is None

    def test_empty_arguments(self, tmp_path):
        plist_file = tmp_path / "empty.plist"
        plist = plistlib.dumps({"ProgramArguments": []}, fmt=plistlib.FMT_XML)
        plist_file.write_bytes(plist)

        cfg = read_plist_config(plist_file)
        assert cfg == {}
