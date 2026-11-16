"""Exception handlers producing the structured error envelope. Never echoes request input."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.errors import AppError, error_body

log = logging.getLogger("lunaris.errors")


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return JSONResponse(error_body(exc.code, exc.message, _rid(request), exc.details), status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        # Only location, message and type: `input`/`ctx` are dropped so user data is never echoed.
        details = [{"loc": [str(p) for p in e.get("loc", ())], "msg": str(e.get("msg", "invalid")), "type": e.get("type")} for e in exc.errors()]
        return JSONResponse(error_body("validation_error", "Request validation failed.", _rid(request), details), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, f"http_{exc.status_code}")
        msg = "Resource not found." if exc.status_code == 404 else (exc.detail if isinstance(exc.detail, str) else "HTTP error.")
        return JSONResponse(error_body(code, msg, _rid(request)), status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.error("unhandled exception", exc_info=exc, extra={"request_id": _rid(request), "path": request.url.path})
        return JSONResponse(error_body("internal_error", "Unexpected server error.", _rid(request)), status_code=500)
