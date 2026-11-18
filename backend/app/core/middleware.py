import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.responses import JSONResponse

from app.core.logging import request_id_context

logger = logging.getLogger(__name__)
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_REQUEST_ID_HEADER = b"x-request-id"


class RequestLoggingMiddleware:
    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[dict[str, Any]]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._request_id_from_scope(scope) or uuid.uuid4().hex
        token = request_id_context.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id
        method = scope.get("method", "")
        path = scope.get("path", "")
        started_at = time.perf_counter()
        response_status: int | None = None
        response_started = False

        fields = {
            "request_id": request_id,
            "http_method": method,
            "http_path": path,
        }
        logger.info("HTTP request started", extra=fields)

        async def send_with_request_id(message: dict[str, Any]) -> None:
            nonlocal response_status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != _REQUEST_ID_HEADER
                ]
                headers.append((_REQUEST_ID_HEADER, request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            logger.exception(
                "Unhandled request exception",
                extra={
                    **fields,
                    "http_status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            if response_started:
                raise

            response_status = 500
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error."},
            )
            await response(scope, receive, send_with_request_id)
        finally:
            logger.info(
                "HTTP request completed",
                extra={
                    **fields,
                    "http_status_code": response_status,
                    "duration_ms": round(
                        (time.perf_counter() - started_at) * 1000,
                        3,
                    ),
                },
            )
            request_id_context.reset(token)

    @staticmethod
    def _request_id_from_scope(scope: dict[str, Any]) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() != _REQUEST_ID_HEADER:
                continue
            try:
                candidate = value.decode("ascii")
            except UnicodeDecodeError:
                return None
            if _REQUEST_ID_PATTERN.fullmatch(candidate):
                return candidate
            return None
        return None
