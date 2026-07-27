"""Unit tests for config migrations."""

from keepalive.migrations import CURRENT_SCHEMA, _migrate_0_to_1, migrate


class TestMigrate01:
    def test_flat_to_nested(self) -> None:
        old = {
            "idle": 120,
            "method": "key",
            "key": "f14",
            "schedule_from": "09:00",
            "schedule_to": "18:00",
        }
        result = _migrate_0_to_1(old)
        assert result["activity"]["idle"] == 120
        assert result["activity"]["method"] == "key"
        assert result["activity"]["key"] == "f14"
        assert result["triggers"]["schedule"]["from"] == "09:00"
        assert result["triggers"]["schedule"]["to"] == "18:00"
        assert result["triggers"]["schedule"]["enabled"] is True
        assert "caffeinate" in result
        assert "wifi" in result["triggers"]
        assert "app" in result["triggers"]

    def test_flat_defaults(self) -> None:
        old: dict = {}
        result = _migrate_0_to_1(old)
        assert result["activity"]["idle"] == 180
        assert result["activity"]["method"] == "mouse"

    def test_already_nested_passes_through(self) -> None:
        nested = {
            "activity": {"idle": 99, "method": "both", "key": "f15"},
            "triggers": {
                "schedule": {"enabled": True, "from": "06:00", "to": "22:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        result = _migrate_0_to_1(nested)
        assert result == nested  # untouched


class TestMigrateLoop:
    def test_nested_config_passes_through(self) -> None:
        """Already-nested config without schema_version still works."""
        nested = {
            "activity": {"idle": 300, "method": "mouse", "key": "f13"},
            "caffeinate": {"enabled": False, "mode": "display", "lid_closed": False},
            "triggers": {
                "schedule": {"enabled": True, "from": "09:00", "to": "18:00"},
                "wifi": {"enabled": False, "ssids": [], "on_match": "start", "on_lost": "stop"},
                "app": {
                    "enabled": False,
                    "apps": [],
                    "on_active": "start",
                    "on_inactive": "schedule",
                },
            },
        }
        result = migrate(nested)
        assert result["activity"]["idle"] == 300
        assert result["schema_version"] == CURRENT_SCHEMA

    def test_no_version_field(self) -> None:
        old = {
            "idle": 120,
            "method": "mouse",
            "key": "f13",
            "schedule_from": "08:00",
            "schedule_to": "17:00",
        }
        result = migrate(old)
        assert result["schema_version"] == CURRENT_SCHEMA
        assert result["activity"]["idle"] == 120

    def test_idempotent(self) -> None:
        old = {
            "idle": 60,
            "method": "both",
            "key": "f15",
            "schedule_from": "06:00",
            "schedule_to": "22:00",
        }
        first = migrate(old)
        second = migrate(dict(first))
        assert second == first
