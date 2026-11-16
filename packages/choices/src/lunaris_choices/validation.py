"""Strict scalar validators shared by all calculators. Reject bool/str/NaN/inf instead of coercing."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from .evidence import ValidationFailure


def number(value: Any, name: str, *, gt: Optional[float] = None, ge: Optional[float] = None,
           le: Optional[float] = None, lt: Optional[float] = None, required: bool = True) -> Optional[float]:
    if value is None:
        if required:
            raise ValidationFailure("MISSING_FIELD", f"{name} is required", name)
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationFailure("NOT_A_NUMBER", f"{name} must be a number", name)
    v = float(value)
    if not math.isfinite(v):
        raise ValidationFailure("NOT_FINITE", f"{name} must be finite", name)
    if v < 0 and (ge is not None and ge >= 0 or gt is not None and gt >= 0):
        raise ValidationFailure("NEGATIVE_VALUE", f"{name} must not be negative", name)
    if gt is not None and not v > gt:
        raise ValidationFailure("OUT_OF_RANGE", f"{name} must be > {gt}", name)
    if ge is not None and not v >= ge:
        raise ValidationFailure("OUT_OF_RANGE", f"{name} must be >= {ge}", name)
    if lt is not None and not v < lt:
        raise ValidationFailure("OUT_OF_RANGE", f"{name} must be < {lt}", name)
    if le is not None and not v <= le:
        raise ValidationFailure("OUT_OF_RANGE", f"{name} must be <= {le}", name)
    return v


def text(value: Any, name: str, *, max_len: int = 200, required: bool = True) -> Optional[str]:
    if value is None:
        if required:
            raise ValidationFailure("MISSING_FIELD", f"{name} is required", name)
        return None
    if not isinstance(value, str):
        raise ValidationFailure("NOT_A_STRING", f"{name} must be a string", name)
    v = value.strip()
    if required and not v:
        raise ValidationFailure("MISSING_FIELD", f"{name} must not be empty", name)
    if len(v) > max_len:
        raise ValidationFailure("TOO_LONG", f"{name} exceeds {max_len} characters", name)
    return v


def one_of(value: Any, name: str, allowed: Iterable[str]) -> str:
    allowed = tuple(allowed)
    if not isinstance(value, str) or value not in allowed:
        raise ValidationFailure("UNSUPPORTED_VALUE", f"{name} must be one of {list(allowed)}", name)
    return value


def country_code(value: Any, name: str = "country_code") -> str:
    if not isinstance(value, str) or len(value) != 2 or not value.isalpha():
        raise ValidationFailure("BAD_COUNTRY", f"{name} must be an ISO 3166-1 alpha-2 code", name)
    return value.upper()


def https_url(value: Any, name: str, *, required: bool = True) -> Optional[str]:
    v = text(value, name, max_len=500, required=required)
    if v is None:
        return None
    if not v.lower().startswith("https://") or " " in v:
        raise ValidationFailure("BAD_URL", f"{name} must be an https URL", name)
    return v


def aware_datetime(value: Any, name: str, *, required: bool = True) -> Optional[datetime]:
    if value is None:
        if required:
            raise ValidationFailure("MISSING_FIELD", f"{name} is required", name)
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationFailure("BAD_DATETIME", f"{name} must be ISO8601", name)
    else:
        raise ValidationFailure("BAD_DATETIME", f"{name} must be ISO8601", name)
    if dt.tzinfo is None:
        raise ValidationFailure("NAIVE_DATETIME", f"{name} must include a timezone offset", name)
    return dt.astimezone(timezone.utc)


def reject_unknown_keys(data: dict, allowed: Iterable[str], where: str) -> None:
    if not isinstance(data, dict):
        raise ValidationFailure("NOT_AN_OBJECT", f"{where} must be an object")
    extra = sorted(set(data) - set(allowed))
    if extra:
        raise ValidationFailure("UNKNOWN_FIELD", f"{where}: unsupported field(s) {extra}", extra[0])
