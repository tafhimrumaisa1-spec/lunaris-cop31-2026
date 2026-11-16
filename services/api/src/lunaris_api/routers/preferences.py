from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..db.models import CityRow, PreferencesRow
from ..deps import AuthContext, get_db, now, optional_auth, rate_limit, require_auth
from ..schemas import PreferencesResponse, UserPreferences

router = APIRouter(prefix="/v1", tags=["preferences"])

NOTICE = "Comfort temperatures are personal preferences used to rank forecast windows. They are not medical safety thresholds."


def to_model(row: PreferencesRow) -> UserPreferences:
    return UserPreferences(user_id=row.user_id, city_id=row.city_id, weather_moods=row.weather_moods,
                           comfort_min_c=row.comfort_min_c, comfort_max_c=row.comfort_max_c,
                           activities=row.activities, priorities=row.priorities, notification_consent=row.notification_consent)


@router.get("/preferences", response_model=PreferencesResponse, summary="Current persisted preferences",
            dependencies=[Depends(rate_limit("read"))])
def get_preferences(auth: AuthContext | None = Depends(optional_auth), db: Session = Depends(get_db)) -> PreferencesResponse:
    """No session, or nothing saved yet => `preferences: null`. No defaults are invented."""
    row = db.get(PreferencesRow, auth.user_id) if auth else None
    return PreferencesResponse(preferences=to_model(row) if row else None, persisted=row is not None, notice=NOTICE)


@router.put("/preferences", response_model=PreferencesResponse, summary="Validate and save preferences",
            dependencies=[Depends(rate_limit("write"))])
def put_preferences(body: UserPreferences, request: Request, auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)) -> PreferencesResponse:
    if body.user_id is not None and body.user_id != auth.user_id:
        raise AppError(403, "user_mismatch", "user_id does not match the current session.")
    city = db.get(CityRow, body.city_id)
    if city is None:
        raise AppError(422, "unknown_city", "Unknown city_id. See GET /v1/cities.")
    if city.support_status == "unsupported":
        raise AppError(422, "city_not_supported", f"{city.name} is not supported yet; preferences can only be saved for supported or preview cities.")
    row = db.get(PreferencesRow, auth.user_id)
    values = dict(city_id=body.city_id, weather_moods=body.weather_moods, comfort_min_c=body.comfort_min_c,
                  comfort_max_c=body.comfort_max_c, activities=body.activities, priorities=body.priorities,
                  notification_consent=body.notification_consent, updated_at=now(request))
    if row is None:
        row = PreferencesRow(user_id=auth.user_id, **values)
        db.add(row)
    else:
        for k, v in values.items():
            setattr(row, k, v)
    db.commit()
    return PreferencesResponse(preferences=to_model(row), persisted=True, notice=NOTICE)
