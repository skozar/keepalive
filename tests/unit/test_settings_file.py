"""Unit tests for settings file I/O using new nested config format."""

import json

from keepalive.config import (
    DEFAULT_IDLE,
    DEFAULT_KEY,
    DEFAULT_METHOD,
    DEFAULT_SCHEDULE_FROM,
    DEFAULT_SCHEDULE_TO,
    load_settings,
    save_settings,
)


class TestLoadSettings:
    def test_defaults_when_no_file(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        cfg = load_settings()
        assert cfg["activity"]["idle"] == DEFAULT_IDLE
        assert cfg["activity"]["method"] == DEFAULT_METHOD
        assert cfg["activity"]["key"] == DEFAULT_KEY
        assert cfg["triggers"]["schedule"]["from"] == DEFAULT_SCHEDULE_FROM
        assert cfg["triggers"]["schedule"]["to"] == DEFAULT_SCHEDULE_TO

    def test_loads_full_config(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        cfg = {
            "activity": {"idle": 400, "method": "key", "key": "f14"},
            "caffeinate": {"enabled": True, "mode": "system", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "07:00", "to": "15:00"},
                "wifi": {
                    "enabled": True,
                    "ssids": ["Home"],
                    "on_match": "start",
                    "on_lost": "stop",
                },
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        settings_file.write_text(json.dumps(cfg))
        result = load_settings()
        assert result["activity"]["idle"] == 400
        assert result["caffeinate"]["enabled"] is True
        assert result["triggers"]["schedule"]["from"] == "07:00"

    def test_migrates_flat_format(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        old = {
            "schedule_from": "09:30",
            "schedule_to": "18:45",
            "idle": 60,
            "method": "both",
            "key": "f15",
        }
        settings_file.write_text(json.dumps(old))
        result = load_settings()
        assert result["triggers"]["schedule"]["from"] == "09:30"
        assert result["triggers"]["schedule"]["to"] == "18:45"
        assert result["activity"]["idle"] == 60
        assert result["activity"]["method"] == "both"

    def test_loads_partial_merged_with_defaults(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        partial = {"activity": {"idle": 999}}
        settings_file.write_text(json.dumps(partial))
        result = load_settings()
        assert result["activity"]["idle"] == 999
        assert result["activity"]["method"] == DEFAULT_METHOD

    def test_loads_corrupt_file_returns_defaults(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        settings_file.write_text("not json")
        result = load_settings()
        assert result["activity"]["idle"] == DEFAULT_IDLE


class TestSaveSettings:
    def test_save_creates_file(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("09:30-18:45", 60, "both", "f15")
        data = json.loads(settings_file.read_text())
        assert data["triggers"]["schedule"]["from"] == "09:30"
        assert data["triggers"]["schedule"]["to"] == "18:45"
        assert data["activity"]["idle"] == 60
        assert data["activity"]["method"] == "both"
        assert data["activity"]["key"] == "f15"

    def test_roundtrip(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("09:30-18:45", 60, "both", "f15")
        cfg = load_settings()
        assert cfg["triggers"]["schedule"]["from"] == "09:30"
        assert cfg["activity"]["idle"] == 60

    def test_save_splits_schedule(self, tmp_path, monkeypatch) -> None:
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        save_settings("09:30-18:45", 60, "mouse", "f13")
        data = json.loads(settings_file.read_text())
        assert data["triggers"]["schedule"]["from"] == "09:30"
        assert data["triggers"]["schedule"]["to"] == "18:45"
