from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ..deps import rate_limit
from ..schemas import ChoiceComparison
from ..services import choices as svc

router = APIRouter(prefix="/v1/choices", tags=["choices"], dependencies=[Depends(rate_limit("write"))])

_R = {503: {"description": "Engine unavailable or not integrated"}, 422: {"description": "Invalid input"}}


@router.post("/travel", response_model=ChoiceComparison, responses=_R, summary="Compare user-defined modes and distance (no routing)")
def travel(payload: dict[str, Any], request: Request) -> ChoiceComparison:
    return svc.compare(request.app.state.providers.choices, "travel", payload)


@router.post("/food", response_model=ChoiceComparison, responses=_R, summary="Compare documented food-category factors")
def food(payload: dict[str, Any], request: Request) -> ChoiceComparison:
    return svc.compare(request.app.state.providers.choices, "food", payload)


@router.post("/energy", response_model=ChoiceComparison, responses=_R, summary="Appliance scenario with user-assumed tariff")
def energy(payload: dict[str, Any], request: Request) -> ChoiceComparison:
    return svc.compare(request.app.state.providers.choices, "energy", payload)
