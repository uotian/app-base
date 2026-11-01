import io
import json
import logging

import pytest

from config.logging import console_handler


@pytest.mark.parametrize("terminal", [False, True])
def test_lifecycle_logs_use_stderr_without_secrets(monkeypatch, capsys, terminal):
    class Output(io.StringIO):
        def isatty(self):
            return terminal

    output = Output()
    monkeypatch.setattr("sys.stderr", output)
    handler = console_handler()
    record = logging.makeLogRecord(
        {
            "name": "app_base.server",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "server_started",
            "port": 12345,
            "desktop": True,
            "token": "test-secret",
        }
    )
    handler.handle(record)
    rendered = output.getvalue()
    assert "server_started" in rendered
    assert "12345" in rendered
    assert "test-secret" not in rendered
    assert capsys.readouterr().out == ""
    if not terminal:
        event = json.loads(rendered)
        assert event["port"] == 12345
        assert event["desktop"] is True
        assert event["level"] == "info"
        assert "timestamp" in event
