"""Unit tests for config: parsing, validation, migration."""

from datetime import datetime

from keepalive.config import (
    DEFAULT_IDLE,
    DEFAULT_METHOD,
    load_settings,
    parse_schedule,
    validate_config,
    write_config,
)
from keepalive.triggers.schedule import in_active_window

# ── parse_schedule (legacy API) ────────────────────────────────────────────


class TestParseSchedule:
    def test_valid(self) -> None:
        assert parse_schedule("08:00-17:00") == (8, 17)

    def test_single_digit_hours(self) -> None:
        assert parse_schedule("3:00-5:30") == (3, 5)

    def test_over_midnight(self) -> None:
        assert parse_schedule("22:00-02:00") == (22, 2)


# ── in_active_window (triggers/schedule) ───────────────────────────────────


class TestInActiveWindow:
    @staticmethod
    def _dt(hour: int) -> datetime:
        return datetime(2026, 7, 1, hour, 0)

    def test_inside(self) -> None:
        assert in_active_window((4, 12), now=self._dt(10)) is True  # type: ignore[call-arg]

    def test_after_end(self) -> None:
        assert in_active_window((4, 12), now=self._dt(13)) is False  # type: ignore[call-arg]

    def test_before_start(self) -> None:
        assert in_active_window((4, 12), now=self._dt(3)) is False  # type: ignore[call-arg]

    def test_exact_start(self) -> None:
        assert in_active_window((4, 12), now=self._dt(4)) is True  # type: ignore[call-arg]

    def test_exact_end(self) -> None:
        assert in_active_window((4, 12), now=self._dt(12)) is False  # type: ignore[call-arg]


# ── validate_config ────────────────────────────────────────────────────────


class TestValidateConfig:
    def test_valid_full(self) -> None:
        cfg = {
            "activity": {"idle": 300, "method": "mouse", "key": "f13"},
            "caffeinate": {"enabled": False, "mode": "display", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "09:00", "to": "17:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        assert validate_config(cfg) == []

    def test_missing_section(self) -> None:
        assert len(validate_config({})) > 0

    def test_bad_idle_range(self) -> None:
        cfg = {
            "activity": {"idle": 5, "method": "mouse", "key": "f13"},
            "caffeinate": {"enabled": False, "mode": "display", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "09:00", "to": "17:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        errors = validate_config(cfg)
        assert any("idle" in e.lower() for e in errors)

    def test_bad_caffeinate_mode(self) -> None:
        cfg = {
            "activity": {"idle": 300, "method": "mouse", "key": "f13"},
            "caffeinate": {"enabled": False, "mode": "bad", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "09:00", "to": "17:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        errors = validate_config(cfg)
        assert any("caffeinate" in e.lower() for e in errors)

    def test_bad_schedule_format(self) -> None:
        cfg = {
            "activity": {"idle": 300, "method": "mouse", "key": "f13"},
            "caffeinate": {"enabled": False, "mode": "display", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "not-a-time", "to": "17:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        errors = validate_config(cfg)
        assert any("schedule" in e.lower() for e in errors)


# ── load_settings — migration from flat format ─────────────────────────────


class TestLoadSettings:
    def test_defaults_when_no_file(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        cfg = load_settings()
        assert cfg["activity"]["idle"] == DEFAULT_IDLE
        assert cfg["activity"]["method"] == DEFAULT_METHOD

    def test_loads_full_config(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        import json

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

    def test_migrates_flat_format(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        import json

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


# ── write_config + save_settings ───────────────────────────────────────────


class TestWriteConfig:
    def test_write_and_read_back(self, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        settings_file = tmp_path / ".config" / "keepalive" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        monkeypatch.setattr("keepalive.config.SETTINGS_PATH", settings_file)
        cfg_in = {
            "activity": {"idle": 200, "method": "both", "key": "f15"},
            "caffeinate": {"enabled": True, "mode": "display", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "06:00", "to": "14:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        errors = write_config(cfg_in)
        assert errors == []
        cfg_out = load_settings()
        assert cfg_out["activity"]["idle"] == 200
        assert cfg_out["caffeinate"]["enabled"] is True

    def test_write_invalid_returns_errors(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        errors = write_config({"activity": {"idle": 99999}})  # type: ignore[typeddict-item]
        assert len(errors) > 0
