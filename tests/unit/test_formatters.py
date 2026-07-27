"""Unit tests for formatters."""

import json

import click
import pytest
from click.testing import CliRunner

from keepalive.formatters import CaptureFormatter, JsonFormatter, TextFormatter


class TestTextFormatter:
    def test_info_prints(self, capsys):
        f = TextFormatter()
        f.info("hello")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_success_prints_coloured(self, capsys):
        f = TextFormatter()
        f.success("done")
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "done" in captured.out

    def test_warning_prints_coloured(self, capsys):
        f = TextFormatter()
        f.warning("careful")
        captured = capsys.readouterr()
        assert "[!!]" in captured.out

    def test_error_goes_to_stderr(self, capsys):
        f = TextFormatter()
        f.error("fail")
        captured = capsys.readouterr()
        assert "fail" in captured.err

    def test_result_is_noop(self, capsys):
        f = TextFormatter()
        f.result({"a": 1})
        assert capsys.readouterr().out == ""

    def test_prompt_returns_input(self):
        """click.prompt reads from stdin — use CliRunner input."""

        f = TextFormatter()

        # Simulate stdin via a subprocess-style invocation
        # We can't easily test click.prompt in isolation;
        # use a small Click command instead.
        @click.command()
        def ask():
            result = f.prompt("? ")
            click.echo(result)

        runner = CliRunner()
        result = runner.invoke(ask, input="yes\n")
        assert result.exit_code == 0
        assert "yes" in result.output


class TestJsonFormatter:
    def test_suppresses_info_success_warning_error(self, capsys):
        f = JsonFormatter()
        f.info("hi")
        f.success("ok")
        f.warning("warn")
        f.error("err")
        assert capsys.readouterr().out == ""

    def test_result_emits_json(self, capsys):
        f = JsonFormatter()
        f.result({"ready": True, "permissions": {"x": 1}})
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert data["ready"] is True
        assert data["permissions"] == {"x": 1}

    def test_second_result_is_silent(self, capsys):
        """Only the first result() call emits JSON."""
        f = JsonFormatter()
        f.result({"first": True})
        f.result({"second": True})
        lines = capsys.readouterr().out.strip().split("\n")
        assert len(lines) == 1

    def test_prompt_raises(self):
        f = JsonFormatter()
        with pytest.raises(RuntimeError, match="interactive"):
            f.prompt("?")


class TestCaptureFormatter:
    def test_records_info(self):
        f = CaptureFormatter()
        f.info("msg1")
        assert ("info", "msg1") in f.calls

    def test_records_success(self):
        f = CaptureFormatter()
        f.success("ok")
        assert ("success", "ok") in f.calls

    def test_records_error(self):
        f = CaptureFormatter()
        f.error("fail")
        assert ("error", "fail") in f.calls

    def test_stores_results(self):
        f = CaptureFormatter()
        f.result({"a": 1})
        assert len(f.results) == 1
        assert f.results[0] == {"a": 1}

    def test_prompt_returns_stored_response(self):
        f = CaptureFormatter()
        f._prompt_responses = ["y", "n"]
        assert f.prompt("?") == "y"
        assert f.prompt("?") == "n"
        assert f.prompt("?") == ""  # exhausted
