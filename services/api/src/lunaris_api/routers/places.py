from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import TypeAdapter, ValidationError

from ..core.errors import AppError
from ..deps import rate_limit
from ..enums import BUSINESS_DISCLOSURE_MVP
from ..integrations.ports import ProviderUnavailable
from ..schemas import BusinessEvidenceProfile, PlaceList, PlaceRecord, SourceStatus

router = APIRouter(prefix="/v1", tags=["places"], dependencies=[Depends(rate_limit("read"))])
log = logging.getLogger("lunaris.places")
_PLACES = TypeAdapter(list[PlaceRecord])


@router.get("/places", response_model=PlaceList, summary="Curated or sourced Dubai places, status per item")
def places(request: Request, category: Annotated[str | None, Query(pattern=r"^[a-z][a-z0-9_]{0,39}$")] = None,
           limit: Annotated[int, Query(ge=1, le=50)] = 20) -> PlaceList:
    st = request.app.state
    now = st.clock()
    if st.providers.places is None:
        # Empty list + explicit status. No invented venues.
        return PlaceList(places=[], source_status=SourceStatus(state="not_integrated", detail="No licensed or curated places source is integrated.", checked_at=now))
    try:
        raw = st.providers.places.list_places(city_id="dubai", category=category, limit=limit)
    except ProviderUnavailable as exc:
        raise AppError(503, "places_unavailable", "The places source is temporarily unavailable.") from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("places provider crashed")
        raise AppError(502, "provider_failure", "The places source failed.") from exc
    try:
        items = _PLACES.validate_python(list(raw))
    except (ValidationError, TypeError) as exc:
        raise AppError(502, "provider_contract_violation", "Places provider result violates the contract.") from exc
    state = "demo" if items and all(p.data_status == "demo" for p in items) else "available"
    return PlaceList(places=items[:limit], source_status=SourceStatus(state=state, checked_at=now))


@router.get("/business-evidence/{id}", response_model=BusinessEvidenceProfile, summary="Business environmental claims and review status",
            responses={404: {"description": "Unknown id"}, 503: {"description": "Source unavailable or not integrated"}})
def business_evidence(request: Request, id: Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]) -> BusinessEvidenceProfile:
    prov = request.app.state.providers.business
    if prov is None:
        raise AppError(503, "integration_pending", "No business-evidence source is integrated in this deployment.")
    try:
        raw = prov.get_profile(id)
    except ProviderUnavailable as exc:
        raise AppError(503, "business_evidence_unavailable", "The evidence source is temporarily unavailable.") from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("business evidence provider crashed")
        raise AppError(502, "provider_failure", "The evidence source failed.") from exc
    if raw is None:
        raise AppError(404, "not_found", "No evidence profile exists for this id.")
    try:
        profile = BusinessEvidenceProfile.model_validate(raw)
    except ValidationError as exc:
        raise AppError(502, "provider_contract_violation", "Evidence profile violates the contract.") from exc
    if profile.disclosure_status not in BUSINESS_DISCLOSURE_MVP:
        raise AppError(502, "provider_contract_violation", "The MVP supports only self_reported and documentation_reviewed; independent verification cannot be asserted yet.")
    return profile
