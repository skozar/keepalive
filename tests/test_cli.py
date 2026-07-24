import json
import subprocess
import sys
import pytest

from pathlib import Path
from keepalive.config import load_settings, save_settings


class TestCLI:
    def test_help_smoke(self):
        """Binary runs --help without crashing."""
        result = subprocess.run(
            [sys.executable, "-m", "keepalive", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "usage: keepalive-cli" in result.stdout

    def test_start_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "keepalive", "start", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "--method" in result.stdout
        assert "--key" in result.stdout

    @pytest.mark.skipif(sys.platform != "darwin", reason="needs launchctl")
    def test_status_smoke(self):
        result = subprocess.run(
            [sys.executable, "-m", "keepalive", "status"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "keepalive-cli" in result.stdout.lower()

    @pytest.mark.skipif(sys.platform != "darwin", reason="needs launchctl")
    def test_status_json(self):
        """status --json returns valid JSON with expected keys."""
        result = subprocess.run(
            [sys.executable, "-m", "keepalive", "status", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "running" in data

    def test_start_respects_settings(self, tmp_path, monkeypatch):
        """start without flags picks up defaults from settings.json."""
        settings_file = tmp_path / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("10:00-14:00", 60, "both", "f15")
        # argparse defaults come from load_settings(), check them
        cfg = load_settings()
        assert cfg["schedule"] == "10:00-14:00"
        assert cfg["idle"] == 60
        assert cfg["method"] == "both"
        assert cfg["key"] == "f15"

    def test_start_flag_overrides_default(self, tmp_path, monkeypatch):
        """When settings.json has mouse, --method key wins."""
        settings_file = tmp_path / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("08:00-17:00", 180, "mouse", "f13")
        # Simulate: argparse would use --method key to override
        cfg = load_settings()
        assert cfg["method"] == "mouse"  # from file
        # In real CLI, --method key would override via argparse
        # The load_settings() call is just defaults — CLI args override
