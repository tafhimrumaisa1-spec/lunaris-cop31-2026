from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from ..core import geo
from ..core.errors import AppError
from ..db.models import CityRow, PreferencesRow
from ..deps import AuthContext, get_db, optional_auth, rate_limit
from ..enums import WINDOW_ALLOWED_DATA_STATUS
from ..integrations.ports import InvalidInput, ProviderUnavailable
from ..schemas import ActivityWindow, HeatShieldRequest, HeatShieldResponse

router = APIRouter(prefix="/v1", tags=["heatshield"])
log = logging.getLogger("lunaris.heatshield")
_WINDOWS = TypeAdapter(list[ActivityWindow])

NOTICES = [
    "Windows are ranked by YOUR comfort preference and the forecast. This is not medical advice and does not mean any window is safe.",
    "Heat caution is derived from forecast apparent temperature and humidity only; shade, sun exposure, exertion, health conditions and acclimatisation are not modelled.",
    "Forecast values are model output for the approximate city centre, not street-level measurements.",
]


@router.post("/heatshield/windows", response_model=HeatShieldResponse, summary="Personalised, non-medical activity window comparison",
             dependencies=[Depends(rate_limit("write"))],
             responses={503: {"description": "Weather or climate engine unavailable/not integrated"}})
def windows(body: HeatShieldRequest, request: Request, auth: AuthContext | None = Depends(optional_auth), db: Session = Depends(get_db)) -> HeatShieldResponse:
    st = request.app.state
    city = db.get(CityRow, body.city_id)
    if city is None:
        raise AppError(422, "unknown_city", "Unknown city_id. See GET /v1/cities.")
    if city.support_status != "supported":
        raise AppError(422, "city_not_supported", f"{city.name} is not supported; HeatShield needs a supported city.")

    # Comfort range: explicit request values, else saved preferences. Never a made-up default.
    lo, hi = body.comfort_min_c, body.comfort_max_c
    if lo is None:
        pref = db.get(PreferencesRow, auth.user_id) if auth else None
        if pref is None:
            raise AppError(422, "comfort_range_required", "Send comfort_min_c and comfort_max_c, or save preferences first.")
        lo, hi = pref.comfort_min_c, pref.comfort_max_c

    coarse = None
    if body.location is not None:
        if not body.location.consent:
            raise AppError(422, "geolocation_consent_required", "Location was sent without consent=true; remove it or ask for consent.")
        clat, clon = geo.coarsen(body.location.latitude, body.location.longitude)
        if not geo.within_radius(clat, clon, city.center_lat, city.center_lon):
            raise AppError(422, "location_outside_city", f"Location is not within the {city.name} area.")
        coarse = {"latitude": clat, "longitude": clon}  # coarsened, in-memory only, never persisted

    engine = st.providers.climate
    if engine is None:
        raise AppError(503, "integration_pending", "The HeatShield climate engine is not integrated in this deployment.")

    wx = st.weather_service.get(city, body.horizon_hours)
    params = {"activity": body.activity, "window_minutes": body.window_minutes, "max_windows": body.max_windows,
              "comfort_min_c": lo, "comfort_max_c": hi, "location": coarse}
    try:
        raw = engine.rank_windows(hours=[h.model_dump(mode="json") for h in wx.hours], params=params)
    except InvalidInput as exc:
        raise AppError(422, "invalid_heatshield_input", str(exc)) from exc
    except ProviderUnavailable as exc:
        raise AppError(503, "climate_unavailable", "The climate engine is temporarily unavailable.") from exc
    except Exception as exc:  # noqa: BLE001
        log.exception("climate engine crashed")
        raise AppError(502, "provider_failure", "The climate engine failed.") from exc

    try:
        parsed = _WINDOWS.validate_python(list(raw))
    except (ValidationError, TypeError) as exc:
        raise AppError(502, "provider_contract_violation", "Climate engine result violates the ActivityWindow contract.") from exc
    bad = {w.evidence.data_status for w in parsed} - WINDOW_ALLOWED_DATA_STATUS
    if bad:
        raise AppError(502, "provider_contract_violation", f"Window evidence may not use data_status {sorted(bad)}.")
    ranks = [w.comfort_rank for w in parsed]
    if len(set(ranks)) != len(ranks):
        raise AppError(502, "provider_contract_violation", "comfort_rank values must be unique.")
    parsed.sort(key=lambda w: w.comfort_rank)

    return HeatShieldResponse(city_id=city.id, activity=body.activity, windows=parsed[: body.max_windows],
                              comfort_range_c=(lo, hi), source_status=wx.source_status, notices=NOTICES)
