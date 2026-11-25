import json
import logging
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import JsonLogFormatter, request_id_context
from app.core.middleware import RequestLoggingMiddleware
from app.main import app


def test_json_formatter_includes_standard_and_request_fields() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.http_method = "GET"
    record.http_path = "/health"
    record.http_status_code = 200
    record.duration_ms = 1.25

    token = request_id_context.set("request-123")
    try:
        payload = json.loads(JsonLogFormatter().format(record))
    finally:
        request_id_context.reset(token)

    assert payload["timestamp"].endswith("Z")
    assert payload["level"] == "INFO"
    assert payload["service"] == "devopsmart-api"
    assert payload["message"] == "HTTP request completed"
    assert payload["request_id"] == "request-123"
    assert payload["http_method"] == "GET"
    assert payload["http_path"] == "/health"
    assert payload["http_status_code"] == 200
    assert payload["duration_ms"] == 1.25


def test_request_id_is_generated_and_completion_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="app.core.middleware"):
        response = TestClient(app).get(
            "/health?access_token=should-not-be-logged"
        )

    request_id = response.headers["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)
    assert response.status_code == 200
    completion = next(
        record
        for record in caplog.records
        if record.getMessage() == "HTTP request completed"
    )
    assert completion.request_id == request_id
    assert completion.http_method == "GET"
    assert completion.http_path == "/health"
    assert completion.http_status_code == 200
    assert completion.duration_ms >= 0
    assert "should-not-be-logged" not in JsonLogFormatter().format(completion)


def test_valid_request_id_is_returned_and_invalid_id_is_replaced() -> None:
    client = TestClient(app)
    accepted = client.get(
        "/health",
        headers={"X-Request-ID": "trace-42.safe_id"},
    )
    rejected = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id"},
    )

    assert accepted.headers["X-Request-ID"] == "trace-42.safe_id"
    assert rejected.headers["X-Request-ID"] != "invalid request id"
    assert re.fullmatch(
        r"[0-9a-f]{32}",
        rejected.headers["X-Request-ID"],
    )


def test_unexpected_exception_is_logged_redacted_and_returns_request_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    test_app = FastAPI()

    @test_app.get("/test-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("api_key=never-log-this")

    test_app.add_middleware(RequestLoggingMiddleware)

    with caplog.at_level(logging.INFO, logger="app.core.middleware"):
        response = TestClient(
            test_app,
            raise_server_exceptions=False,
        ).get("/test-error")

    request_id = response.headers["X-Request-ID"]
    exception_record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Unhandled request exception"
    )
    formatted = JsonLogFormatter().format(exception_record)
    payload = json.loads(formatted)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert "never-log-this" not in response.text
    assert exception_record.request_id == request_id
    assert payload["exception"]["type"] == "RuntimeError"
    assert "never-log-this" not in formatted
    assert payload["http_status_code"] == 500
    assert payload["duration_ms"] >= 0
