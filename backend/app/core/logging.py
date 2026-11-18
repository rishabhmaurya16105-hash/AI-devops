import json
import logging
import os
import re
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

_REDACTION_PATTERNS = (
    re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|"
        r"authorization|database[_-]?url|dsn)\b(\s*[:=]\s*)"
        r'(?:"[^"]*"|\'[^\']*\'|[^\s,;]+)'
    ),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"(?i)\b(?:postgres(?:ql)?(?:\+\w+)?|redis)://[^@\s]+@"),
    re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
        r"AKIA[A-Z0-9]{16})\b"
    ),
)
_STRUCTURED_FIELDS = (
    "http_method",
    "http_path",
    "http_status_code",
    "duration_ms",
)


def redact_sensitive_text(value: str) -> str:
    sanitized = value
    for pattern in _REDACTION_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "service": "devopsmart-api",
            "message": redact_sensitive_text(record.getMessage()),
            "request_id": getattr(
                record,
                "request_id",
                request_id_context.get(),
            ),
            "logger": record.name,
        }

        for field in _STRUCTURED_FIELDS:
            if hasattr(record, field):
                value = getattr(record, field)
                payload[field] = (
                    redact_sensitive_text(value)
                    if isinstance(value, str)
                    else value
                )

        if record.exc_info:
            exception_type, exception, tb = record.exc_info
            payload["exception"] = {
                "type": exception_type.__name__ if exception_type else None,
                "message": redact_sensitive_text(str(exception)),
                "frames": [
                    {
                        "file": os.path.basename(frame.filename),
                        "line": frame.lineno,
                        "function": frame.name,
                    }
                    for frame in traceback.extract_tb(tb)
                ],
            }

        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = next(
        (
            existing
            for existing in root_logger.handlers
            if getattr(existing, "_devopsmart_json_handler", False)
        ),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonLogFormatter())
        setattr(handler, "_devopsmart_json_handler", True)
        root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_logger.propagate = False

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
