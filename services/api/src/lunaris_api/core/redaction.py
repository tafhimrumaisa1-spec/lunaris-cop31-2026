"""PII / secret redaction for logs."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

REDACTED = "[REDACTED]"

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{8,}"), r"\1 " + REDACTED),
    (re.compile(r"(?i)\b(authorization|token|secret|password|api[_-]?key|session[_-]?token|cookie)(\s*[=:]\s*)[^\s,;&\"']+"), r"\1\2" + REDACTED),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"\+\d[\d\s().-]{7,}\d"), "[REDACTED_PHONE]"),
    # coordinates with >=3 decimals (precise location)
    (re.compile(r"(?<![\w.])-?\d{1,3}\.\d{3,}(?![\w.])"), "[REDACTED_COORD]"),
    # long opaque tokens (urlsafe-base64 / hex >= 32 chars)
    (re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{32,}(?![A-Za-z0-9_-])"), "[REDACTED_TOKEN]"),
]

_SENSITIVE_KEYS = {
    "authorization", "token", "session_token", "password", "secret", "cookie", "email",
    "latitude", "longitude", "lat", "lon", "lng", "phone", "api_key", "apikey",
}


def redact_text(text: str) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text


def redact_value(value: Any, key: str | None = None) -> Any:
    if key is not None and key.lower() in _SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(v) for v in value]
    return value


class RedactingFilter(logging.Filter):
    """Redacts the formatted message and any structured `extra` fields."""

    _STD = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        for k in list(vars(record)):
            if k not in self._STD:
                setattr(record, k, redact_value(getattr(record, k), k))
        if record.exc_text:
            record.exc_text = redact_text(record.exc_text)
        return True


class JsonFormatter(logging.Formatter):
    _STD = RedactingFilter._STD

    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k, v in vars(record).items():
            if k not in self._STD:
                out[k] = v
        if record.exc_info:
            out["exc"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(out, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactingFilter())
    root = logging.getLogger("lunaris")
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    root.propagate = False
