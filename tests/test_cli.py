import subprocess
import sys
import pytest


class TestCLI:
    def test_help_smoke(self):
        """Binary runs --help without crashing."""
        result = subprocess.run(
            [sys.executable, "-m", "keepalive", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "usage: keepalive" in result.stdout

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
        assert "keepalive" in result.stdout.lower()
