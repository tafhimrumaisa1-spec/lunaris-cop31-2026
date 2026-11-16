"""Explore: filtered place listing. Alphabetical order only (no rankings). Weather filters run only on sufficient-quality input."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

from lunaris_choices import validation as v
from lunaris_choices.cities import city_status
from lunaris_choices.evidence import Clock, ResultWarning, ValidationFailure, iso_utc, to_jsonable, utc_now

from .models import CATEGORIES, Place

ACTIVITY_TO_CATEGORY = {"cafes": "cafe", "walking": "walk", "exercise": "walk", "culture": "culture", "indoor": "indoor", "events": "event"}
WEATHER_MAX_AGE = timedelta(hours=3)
CURATED_PATH = Path(__file__).parent / "data" / "curated_places.json"


def load_curated(path: Path = CURATED_PATH) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Place.from_dict(e) for e in data["entries"]]  # raises on missing provenance


@dataclass(frozen=True)
class WeatherInput:
    apparent_temperature_c: Optional[float]
    precip_probability_percent: Optional[float]
    retrieved_at: datetime
    data_status: str

    @staticmethod
    def from_dict(d: dict) -> "WeatherInput":
        v.reject_unknown_keys(d, {"apparent_temperature_c", "precip_probability_percent", "retrieved_at", "data_status"}, "weather")
        return WeatherInput(v.number(d.get("apparent_temperature_c"), "apparent_temperature_c", ge=-90, le=70, required=False),
                            v.number(d.get("precip_probability_percent"), "precip_probability_percent", ge=0, le=100, required=False),
                            v.aware_datetime(d.get("retrieved_at"), "retrieved_at"),
                            v.one_of(d.get("data_status"), "data_status", ("live", "historical", "modeled", "demo")))

    def insufficiency(self, now: datetime) -> Optional[str]:
        if self.data_status != "live":
            return f"weather data_status is '{self.data_status}', not live"
        if self.apparent_temperature_c is None or self.precip_probability_percent is None:
            return "apparent temperature and precipitation probability are both required"
        if now - self.retrieved_at > WEATHER_MAX_AGE or self.retrieved_at - now > timedelta(minutes=5):
            return "weather snapshot is stale or from the future (>3h old)"
        return None


class PlaceService:
    def __init__(self, places: Optional[Iterable[Place]] = None, clock: Clock = utc_now):
        self._places = list(load_curated() if places is None else places)
        self._clock = clock

    def list_places(self, query: Optional[dict] = None) -> dict:
        q = query or {}
        v.reject_unknown_keys(q, {"city_id", "categories", "activities", "comfort_max_c", "comfort_min_c", "weather"}, "places query")
        now = self._clock()
        now_iso = iso_utc(now)
        city_id = v.text(q.get("city_id", "dubai"), "city_id", max_len=40).lower()
        status = city_status(city_id)
        warnings, applied, skipped = [], [], []
        if status != "supported":
            warnings.append(ResultWarning("UNSUPPORTED_CITY", f"City '{city_id}' has no supported place coverage; no places returned.", "limitation"))
            return self._resp(city_id, status, [], applied, skipped, warnings, 0, now_iso)

        wanted = set()
        for c in q.get("categories") or []:
            wanted.add(v.one_of(c, "categories[]", CATEGORIES))
        for a in q.get("activities") or []:
            cat = ACTIVITY_TO_CATEGORY.get(a) if isinstance(a, str) else None
            if cat:
                wanted.add(cat)
            else:
                warnings.append(ResultWarning("UNKNOWN_ACTIVITY", f"Activity '{a}' has no matching category and was ignored.", "info"))
        cmax = v.number(q.get("comfort_max_c"), "comfort_max_c", ge=-50, le=70, required=False)
        cmin = v.number(q.get("comfort_min_c"), "comfort_min_c", ge=-50, le=70, required=False)
        if cmax is not None and cmin is not None and cmin >= cmax:
            raise ValidationFailure("BAD_COMFORT_RANGE", "comfort_min_c must be below comfort_max_c", "comfort_min_c")

        pool = [p for p in self._places if p.city_id == city_id]
        if wanted:
            applied.append("categories:" + ",".join(sorted(wanted)))
            pool = [p for p in pool if wanted & set(p.categories)]

        wx = None
        if q.get("weather") is not None:
            w = WeatherInput.from_dict(q["weather"])
            why = w.insufficiency(now)
            if why:
                skipped.append({"filter": "weather", "reason": why})
                warnings.append(ResultWarning("WEATHER_FILTER_SKIPPED", f"Weather filtering skipped: {why}.", "caution"))
            else:
                wx = w
        results, excluded = [], 0
        for p in pool:
            reasons = []
            if wx and p.setting == "outdoor":
                if wx.precip_probability_percent >= 50:
                    excluded += 1
                    continue
                if cmax is not None and wx.apparent_temperature_c > cmax:
                    excluded += 1
                    continue
                if cmin is not None and wx.apparent_temperature_c < cmin:
                    excluded += 1
                    continue
            if wx:
                reasons.append("weather_filter_applied")
            if wanted:
                reasons.append("matches_requested_category")
            results.append({"place": p, "match_reasons": reasons, "open_now": p.open_now(now),
                            "open_now_note": None if p.open_now(now) is not None else "unknown: no hours or hours not verified within 30 days",
                            "evidence": p.evidence(now_iso)})
        if wx:
            applied.append("weather:outdoor places excluded when precip probability >= 50% or apparent temperature outside the user's comfort range (comfort preference, not a safety judgement)")
        results.sort(key=lambda r: r["place"].name.lower())
        if any(p.is_demo for p in self._places):
            warnings.append(ResultWarning("DEMO_ENTRIES", "Results include fictional demo entries; no real venue data is shipped.", "caution"))
        warnings.append(ResultWarning("NO_RANKING", "Results are alphabetical; no ranking, rating or sponsored placement.", "info"))
        return self._resp(city_id, status, results, applied, skipped, warnings, excluded, now_iso)

    @staticmethod
    def _resp(city_id, status, results, applied, skipped, warnings, excluded, now_iso) -> dict:
        items = []
        for r in results:
            p = r["place"]
            items.append({"id": p.id, "name": p.name, "categories": list(p.categories), "setting": p.setting, "description": p.description,
                          "map_link": p.map_link, "is_demo": p.is_demo, "open_now": r["open_now"], "open_now_note": r["open_now_note"],
                          "match_reasons": r["match_reasons"], "evidence": r["evidence"]})
        return to_jsonable({"city_id": city_id, "support_status": status, "generated_at": now_iso, "ordering": "alphabetical",
                            "places": items, "excluded_by_weather_count": excluded,
                            "applied_filters": applied, "skipped_filters": skipped, "warnings": warnings})
