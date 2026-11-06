"""Pure-ASGI middleware: request id propagation + timing. Kept dependency-free so the same
middleware can be reused by any service (or a gateway) without BaseHTTPMiddleware overhead."""

import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

import structlog

type Scope = MutableMapping[str, Any]
type Message = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]
type ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

REQUEST_ID_HEADER = b"x-request-id"


def get_request_id() -> str | None:
    rid = structlog.contextvars.get_contextvars().get("request_id")
    return str(rid) if rid else None


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        request_id = headers.get(REQUEST_ID_HEADER, b"").decode() or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(
            request_id=request_id, path=scope.get("path"), method=scope.get("method")
        )
        start = time.perf_counter()
        log = structlog.get_logger("http")

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                hdrs = list(message.get("headers") or [])
                hdrs.append((REQUEST_ID_HEADER, request_id.encode()))
                hdrs.append((b"x-response-time-ms", str(elapsed_ms).encode()))
                message["headers"] = hdrs
                log.info("request", status=message["status"], duration_ms=elapsed_ms)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.unbind_contextvars("request_id", "path", "method")
