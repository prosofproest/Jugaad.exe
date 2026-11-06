"""Structured logs are JSON, carry a request id and never carry payloads."""

import json
import logging

from app.core.logging import JsonFormatter, request_id_var


def _record(message: str, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_log_event_is_one_json_line() -> None:
    formatted = JsonFormatter().format(_record("forecast.issued", forecast_id="fc_1"))

    assert "\n" not in formatted
    event = json.loads(formatted)
    assert event["level"] == "info"
    assert event["event"] == "forecast.issued"
    assert event["forecast_id"] == "fc_1"
    assert event["ts"].endswith("+00:00")


def test_request_id_from_context_is_attached() -> None:
    token = request_id_var.set("req_ctx_1")
    try:
        event = json.loads(JsonFormatter().format(_record("review.claimed")))
    finally:
        request_id_var.reset(token)

    assert event["request_id"] == "req_ctx_1"


def test_exception_logging_keeps_only_the_error_type() -> None:
    try:
        raise ValueError("secret payload value")
    except ValueError:
        record = _record("request.failed")
        record.exc_info = __import__("sys").exc_info()

    event = json.loads(JsonFormatter().format(record))
    assert event["error_type"] == "ValueError"
    assert "secret payload value" not in json.dumps(event)
