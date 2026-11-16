"""Pure-ASGI middleware: request id, body-size guard, security headers, access log."""
from __future__ import annotations

import json
import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders

from .core.errors import error_body

log = logging.getLogger("lunaris.access")
_RID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_BODY_METHODS = {"POST", "PUT", "PATCH"}


class RequestContextMiddleware:
    def __init__(self, app, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        incoming = headers.get("x-request-id", "")
        rid = incoming if _RID.match(incoming) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = rid
        status = {"code": 0}
        start = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                h = MutableHeaders(scope=message)
                h["X-Request-ID"] = rid
                h["X-Content-Type-Options"] = "nosniff"
                h["Referrer-Policy"] = "no-referrer"
                if "cache-control" not in h:
                    h["Cache-Control"] = "no-store"
            await send(message)

        async def reject(code: int, err: str, msg: str):
            body = json.dumps(error_body(err, msg, rid)).encode()
            await send_wrapper({"type": "http.response.start", "status": code,
                                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
            await send_wrapper({"type": "http.response.body", "body": body})

        try:
            if scope["method"] in _BODY_METHODS:
                if "chunked" in headers.get("transfer-encoding", "").lower():
                    await reject(411, "length_required", "Content-Length is required for request bodies.")
                    return
                try:
                    declared = int(headers.get("content-length", "0") or 0)
                except ValueError:
                    await reject(400, "invalid_content_length", "Invalid Content-Length header.")
                    return
                if declared < 0 or declared > self.max_body_bytes:
                    await reject(413, "request_too_large", f"Request body exceeds {self.max_body_bytes} bytes.")
                    return
            await self.app(scope, receive, send_wrapper)
        finally:
            # Path only: query strings can carry PII and are never logged.
            log.info("request", extra={
                "request_id": rid, "method": scope["method"], "path": scope["path"],
                "status": status["code"], "duration_ms": int((time.perf_counter() - start) * 1000),
            })
