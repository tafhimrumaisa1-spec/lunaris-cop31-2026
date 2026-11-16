"""Weather caching boundary: fresh cache -> provider -> stale-if-error -> 503. Never fabricates."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from pydantic import TypeAdapter, ValidationError

from ..config import Settings
from ..core.cache import TTLCache
from ..core.errors import AppError
from ..db.models import CityRow
from ..enums import WEATHER_ALLOWED_DATA_STATUS
from ..integrations.ports import WeatherProvider
from ..schemas import HourConditions, SourceStatus

log = logging.getLogger("lunaris.weather")
_HOURS = TypeAdapter(list[HourConditions])


@dataclass(frozen=True)
class WeatherResult:
    hours: list[HourConditions]
    source_status: SourceStatus
    served_from_cache: bool
    age_seconds: float


class WeatherService:
    def __init__(self, provider: WeatherProvider | None, settings: Settings, clock: Callable[[], datetime], cache: TTLCache | None = None) -> None:
        self.provider = provider
        self.settings = settings
        self.clock = clock
        self.cache: TTLCache[list[HourConditions]] = cache or TTLCache()
        self._lock = threading.Lock()  # one upstream call at a time: avoids stampedes on cache expiry

    def get(self, city: CityRow, hours: int) -> WeatherResult:
        if self.provider is None:
            raise AppError(503, "integration_pending", "No weather provider is integrated in this deployment.",
                           details=[{"msg": "Set LUNARIS_WEATHER_PROVIDER to an implementation of WeatherProvider.", "loc": [], "type": None}])
        key = (city.id, hours)
        fresh = self.cache.get(key, self.settings.weather_cache_ttl_seconds)
        if fresh:
            return self._result(fresh.value, "available", None, True, fresh.age_seconds)

        with self._lock:
            fresh = self.cache.get(key, self.settings.weather_cache_ttl_seconds)  # filled while we waited
            if fresh:
                return self._result(fresh.value, "available", None, True, fresh.age_seconds)
            try:
                raw = self.provider.fetch_hourly(city_id=city.id, latitude=city.center_lat, longitude=city.center_lon, timezone=city.timezone, hours=hours)
            except Exception as exc:  # noqa: BLE001  (ProviderUnavailable or any provider crash -> same fallback)
                log.warning("weather provider failed: %s", type(exc).__name__)
                stale = self.cache.get(key, self.settings.weather_stale_max_seconds)
                if stale:
                    mins = int(stale.age_seconds // 60)
                    return self._result(stale.value, "stale",
                                        f"Upstream weather source unavailable; serving a cached forecast retrieved {mins} min ago.",
                                        True, stale.age_seconds)
                raise AppError(503, "weather_unavailable", "The weather source is unavailable and no recent cached forecast exists.") from exc

            parsed = self._validate(raw, hours)
            self.cache.put(key, parsed)
            return self._result(parsed, "available", None, False, 0.0)

    def _validate(self, raw, hours: int) -> list[HourConditions]:
        try:
            parsed = _HOURS.validate_python(list(raw))
        except (ValidationError, TypeError) as exc:
            log.error("weather provider contract violation")
            raise AppError(502, "provider_contract_violation", "Weather provider returned data that violates the HourConditions contract.") from exc
        if not parsed:
            raise AppError(503, "weather_unavailable", "The weather provider returned no hourly data.")
        stamps = [h.timestamp for h in parsed]
        if stamps != sorted(stamps):
            raise AppError(502, "provider_contract_violation", "Weather hours must be ascending by timestamp.")
        bad = {h.evidence.data_status for h in parsed} - WEATHER_ALLOWED_DATA_STATUS
        if bad:
            raise AppError(502, "provider_contract_violation", f"Weather evidence may not use data_status {sorted(bad)}.")
        return parsed[:hours]

    def _result(self, hours, state, detail, cached, age) -> WeatherResult:
        has_demo = any(h.evidence.data_status == "demo" for h in hours)
        if has_demo and state == "available":
            state, detail = "demo", "Fixture data: NOT a live forecast."
        return WeatherResult(hours, SourceStatus(state=state, detail=detail, checked_at=self.clock()), cached, age)
