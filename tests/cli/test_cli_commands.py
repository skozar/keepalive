"""CLI integration tests — subprocess, slow, platform-dependent."""

import json
import subprocess
import sys

import pytest

from keepalive.config import load_settings, save_settings

BINARY = [sys.executable, "-m", "keepalive"]


class TestCLI:
    def test_help_smoke(self):
        result = subprocess.run(
            [*BINARY, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "keepalive" in result.stdout.lower()
        assert "Commands:" in result.stdout

    def test_start_help(self):
        result = subprocess.run(
            [*BINARY, "start", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--method" in result.stdout
        assert "--key" in result.stdout

    @pytest.mark.skipif(sys.platform != "darwin", reason="needs launchctl")
    def test_status_smoke(self):
        result = subprocess.run(
            [*BINARY, "status"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "keepalive-cli" in result.stdout.lower()

    @pytest.mark.skipif(sys.platform != "darwin", reason="needs launchctl")
    def test_status_json(self):
        result = subprocess.run(
            [*BINARY, "--json", "status"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "running" in data

    def test_start_respects_settings(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".config" / "keepalive"
        config_dir.mkdir(parents=True)
        settings_file = config_dir / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("10:00-14:00", 60, "both", "f15")
        cfg = load_settings()
        assert cfg["triggers"]["schedule"]["from"] == "10:00"
        assert cfg["triggers"]["schedule"]["to"] == "14:00"
        assert cfg["activity"]["idle"] == 60
        assert cfg["activity"]["method"] == "both"
        assert cfg["activity"]["key"] == "f15"

    def test_start_flag_overrides_default(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".config" / "keepalive"
        config_dir.mkdir(parents=True)
        settings_file = config_dir / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("08:00-17:00", 180, "mouse", "f13")
        cfg = load_settings()
        assert cfg["activity"]["method"] == "mouse"

    def test_help_with_global_json(self):
        result = subprocess.run(
            [*BINARY, "--json", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "keepalive" in result.stdout.lower()
