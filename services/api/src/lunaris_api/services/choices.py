"""Gateway to the choices package: envelope checks in, contract + provenance checks out."""
from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from ..core.errors import AppError
from ..core.payload import PayloadError, check_json_payload
from ..enums import CHOICES_ALLOWED_DATA_STATUS
from ..integrations.ports import ChoicesEngine, InvalidInput, ProviderUnavailable
from ..schemas import ChoiceComparison

log = logging.getLogger("lunaris.choices")


def compare(engine: ChoicesEngine | None, kind: str, payload: dict[str, Any]) -> ChoiceComparison:
    if engine is None:
        raise AppError(503, "integration_pending", f"The {kind} comparison engine is not integrated in this deployment.")
    try:
        check_json_payload(payload)
    except PayloadError as exc:
        raise AppError(422, "invalid_payload", str(exc)) from exc
    try:
        raw = engine.compare(kind=kind, payload=payload)
    except InvalidInput as exc:
        raise AppError(422, "invalid_choice_input", str(exc)) from exc
    except ProviderUnavailable as exc:
        raise AppError(503, "choices_unavailable", "The comparison engine is temporarily unavailable.") from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("choices engine crashed")
        raise AppError(502, "provider_failure", "The comparison engine failed.") from exc
    try:
        result = ChoiceComparison.model_validate(raw)
    except ValidationError as exc:
        raise AppError(502, "provider_contract_violation", "Comparison result violates the ChoiceComparison contract.") from exc
    if result.comparison_type != kind:
        raise AppError(502, "provider_contract_violation", f"Expected comparison_type {kind!r}, got {result.comparison_type!r}.")
    bad = {e.data_status for e in result.evidence} - CHOICES_ALLOWED_DATA_STATUS
    if bad:
        raise AppError(502, "provider_contract_violation", f"Choice evidence may not use data_status {sorted(bad)}.")
    return result
