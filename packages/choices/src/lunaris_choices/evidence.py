"""Shared evidence / warning / result types and JSON helpers.

Field names of ``Evidence`` and ``ChoiceComparison`` follow contracts/data-models.json exactly.
``ChoiceComparison.warnings`` is an ADDITIVE field required by the Agent 03 brief ("warnings on each result").
Types are stdlib dataclasses (Pydantic v2 / FastAPI can consume them directly).
"""
from __future__ import annotations

import dataclasses
import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

DATA_STATUSES = ("live", "historical", "modeled", "demo", "self_reported", "verified")
COMPARISON_TYPES = ("travel", "food", "energy", "business")
WARNING_SEVERITIES = ("info", "caution", "limitation")

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("naive datetime not allowed; use UTC internally")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ValidationFailure(ValueError):
    """Raised for malformed or unsupported input. Maps to HTTP 422 in the API layer."""

    def __init__(self, code: str, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.code, self.message, self.field = code, message, field

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "field": self.field}


class NotFoundError(LookupError):
    """Raised when an id is unknown. Maps to HTTP 404."""


@dataclass(frozen=True)
class ResultWarning:
    code: str
    message: str
    severity: str = "caution"

    def __post_init__(self):
        if self.severity not in WARNING_SEVERITIES:
            raise ValueError(f"bad severity {self.severity}")


@dataclass(frozen=True)
class Evidence:
    source_name: str
    source_url: Optional[str]
    retrieved_at: str
    valid_at: Optional[str]
    data_status: str
    method: str
    limitations: list = field(default_factory=list)

    def __post_init__(self):
        if self.data_status not in DATA_STATUSES:
            raise ValueError(f"data_status must be one of {DATA_STATUSES}")


@dataclass(frozen=True)
class ChoiceComparison:
    choice_id: str
    comparison_type: str
    alternatives: list
    estimated_impacts: list
    assumptions: list
    evidence: list
    warnings: list = field(default_factory=list)

    def __post_init__(self):
        if self.comparison_type not in COMPARISON_TYPES:
            raise ValueError(f"comparison_type must be one of {COMPARISON_TYPES}")

    def to_dict(self) -> dict:
        return to_jsonable(self)


def to_jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, datetime):
        return iso_utc(obj)
    if isinstance(obj, enum.Enum):
        return obj.value
    return obj
