"""Structured application errors. Envelope: {"error": {code, message, request_id, details}}."""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []
        self.headers = headers or {}


def error_body(code: str, message: str, request_id: str | None, details: list[dict[str, Any]] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id, "details": details or []}}
