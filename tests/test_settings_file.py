"""Tests for settings.json load/save (config.py)."""

import json
import tempfile
from pathlib import Path

from keepalive.config import load_settings, save_settings, SETTINGS_PATH


class TestLoadSettings:
    def test_load_no_file(self, monkeypatch):
        """When settings.json doesn't exist, return defaults."""
        missing = Path("/nonexistent/settings.json")
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", missing)
        cfg = load_settings()
        assert cfg["schedule"] == "08:00-17:00"
        assert cfg["idle"] == 180
        assert cfg["method"] == "mouse"
        assert cfg["key"] == "f13"

    def test_load_valid(self, monkeypatch, tmp_path):
        """settings.json with all fields → correct dict, schedule merged."""
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({
            "schedule_from": "09:30",
            "schedule_to": "18:45",
            "idle": 120,
            "method": "key",
            "key": "f14",
        }))
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        cfg = load_settings()
        assert cfg["schedule"] == "09:30-18:45"
        assert cfg["idle"] == 120
        assert cfg["method"] == "key"
        assert cfg["key"] == "f14"

    def test_load_partial(self, monkeypatch, tmp_path):
        """Missing method → default, rest from file."""
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({
            "schedule_from": "22:00",
            "schedule_to": "06:00",
            "idle": 300,
        }))
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        cfg = load_settings()
        assert cfg["schedule"] == "22:00-06:00"
        assert cfg["idle"] == 300
        assert cfg["method"] == "mouse"  # default
        assert cfg["key"] == "f13"       # default

    def test_load_midnight(self, monkeypatch, tmp_path):
        """Schedule crossing midnight."""
        f = tmp_path / "settings.json"
        f.write_text(json.dumps({
            "schedule_from": "23:00",
            "schedule_to": "02:00",
            "idle": 180,
        }))
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        cfg = load_settings()
        assert cfg["schedule"] == "23:00-02:00"

    def test_load_corrupt(self, monkeypatch, tmp_path):
        """Corrupt JSON → fallback to defaults."""
        f = tmp_path / "settings.json"
        f.write_text("not json")
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        cfg = load_settings()
        assert cfg["schedule"] == "08:00-17:00"


class TestSaveSettings:
    def test_save_creates_file(self, monkeypatch, tmp_path):
        """save_settings creates the file."""
        f = tmp_path / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        save_settings("08:00-17:00", 300, "both", "f15")
        assert f.exists()
        data = json.loads(f.read_text())
        assert data["schedule_from"] == "08:00"
        assert data["schedule_to"] == "17:00"
        assert data["idle"] == 300
        assert data["method"] == "both"
        assert data["key"] == "f15"

    def test_roundtrip(self, monkeypatch, tmp_path):
        """save → load → same values."""
        f = tmp_path / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        save_settings("09:30-18:45", 90, "key", "f14")
        cfg = load_settings()
        assert cfg["schedule"] == "09:30-18:45"
        assert cfg["idle"] == 90
        assert cfg["method"] == "key"
        assert cfg["key"] == "f14"

    def test_save_splits_schedule(self, monkeypatch, tmp_path):
        """HH:MM-HH:MM → schedule_from, schedule_to."""
        f = tmp_path / "settings.json"
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", f)
        save_settings("09:30-18:45", 180, "mouse", "f13")
        data = json.loads(f.read_text())
        assert data["schedule_from"] == "09:30"
        assert data["schedule_to"] == "18:45"
