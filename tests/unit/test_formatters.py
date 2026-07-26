"""Unit tests for formatters."""

import json

import pytest

from keepalive.formatters import (
    CaptureFormatter,
    JsonFormatter,
    TextFormatter,
)


class TestTextFormatter:
    def test_info_prints(self, capsys):
        f = TextFormatter()
        f.info("hello")
        captured = capsys.readouterr()
        assert captured.out.strip() == "hello"

    def test_success_prints_coloured(self, capsys):
        f = TextFormatter()
        f.success("done")
        out = capsys.readouterr().out
        assert "done" in out
        assert "\033[32m" in out  # green

    def test_warning_prints_coloured(self, capsys):
        f = TextFormatter()
        f.warning("careful")
        out = capsys.readouterr().out
        assert "careful" in out

    def test_error_goes_to_stderr(self, capsys):
        f = TextFormatter()
        f.error("fail")
        captured = capsys.readouterr()
        assert "fail" in captured.err

    def test_result_is_noop(self, capsys):
        f = TextFormatter()
        f.result({"a": 1})
        assert capsys.readouterr().out == ""

    def test_prompt_returns_input(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda p="": "yes")
        f = TextFormatter()
        assert f.prompt("? ") == "yes"


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
