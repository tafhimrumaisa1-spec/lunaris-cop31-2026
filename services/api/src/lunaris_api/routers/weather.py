from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..db.models import CityRow
from ..deps import get_db, rate_limit
from ..schemas import CacheInfo, WeatherResponse

router = APIRouter(prefix="/v1", tags=["weather"], dependencies=[Depends(rate_limit("read"))])

NOTICE = "Model forecast for the approximate city centre; not a street-level or station measurement."


@router.get("/weather/dubai", response_model=WeatherResponse, summary="Source-aware Dubai forecast",
            responses={503: {"description": "Weather source unavailable or not integrated"}, 502: {"description": "Provider contract violation"}})
def dubai_weather(request: Request, hours: int = Query(48, ge=1, le=120), db: Session = Depends(get_db)) -> WeatherResponse:
    city = db.get(CityRow, "dubai")
    if city is None:
        raise AppError(503, "registry_not_seeded", "City registry is empty; run `alembic upgrade head`.")
    res = request.app.state.weather_service.get(city, hours)
    return WeatherResponse(
        city_id=city.id, timezone=city.timezone, location_precision="approximate_city_center", horizon_hours=hours,
        hours=res.hours, source_status=res.source_status, cache=CacheInfo(served_from_cache=res.served_from_cache, age_seconds=round(res.age_seconds, 1)),
        notice=NOTICE,
    )
