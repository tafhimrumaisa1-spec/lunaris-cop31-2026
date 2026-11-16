"""Non-medical activity rankings; calculations are explicit, not a trained preference model."""
from __future__ import annotations
from datetime import datetime
import math
from pydantic import BaseModel, Field, model_validator

class Preferences(BaseModel):
    min_comfort_c: float = Field(default=20, ge=-5, le=45)
    max_comfort_c: float = Field(default=30, ge=-5, le=55)
    prefers_clouds: bool = False
    prefers_rain: bool = False
    prefer_evenings: bool = False
    activity: str = Field(default="walking", pattern=r"^(walking|sightseeing|cafe|running|outdoor_rest)$")
    @model_validator(mode="after")
    def check_range(self):
        if self.min_comfort_c >= self.max_comfort_c:
            raise ValueError("min_comfort_c must be less than max_comfort_c")
        return self

def rank_hours(hours: list[dict], prefs: Preferences, limit: int = 6) -> list[dict]:
    """Rank optional windows without pronouncing conditions safe.
    Higher score (out of 100) means a closer stated-preference match, not physiological safety.
    """
    result=[]
    for h in hours:
        time = h.get("time")
        perceived = h.get("apparent_temperature_c")
        if time is None or perceived is None or not math.isfinite(float(perceived)):
            continue
        try:
            dt = datetime.fromisoformat(time)
        except ValueError:
            continue
        is_day = h.get("is_day")
        cloud = h.get("cloud_cover_pct")
        precip = h.get("precipitation_mm")
        humidity = h.get("relative_humidity_pct")
        temp = float(perceived)
        low, high = prefs.min_comfort_c, prefs.max_comfort_c
        distance = max(low-temp, 0, temp-high)
        # A transparent rule score: not learned from user preferences or validated comfort reports.
        score = max(0., 100. - 6. * distance)
        if prefs.prefers_clouds and cloud is not None and float(cloud) >= 60:
            score += 6
        if prefs.prefers_rain and precip is not None and float(precip) > 0:
            score += 4
        if prefs.prefer_evenings and dt.hour >= 17:
            score += 4
        score = min(100., round(score, 1))
        cautions=[]
        if temp >= 35:
            cautions.append("Elevated apparent temperature: exercise caution with outdoor exertion; this is not a safety assessment.")
        if precip is not None and float(precip) >= 5:
            cautions.append("Substantial hourly precipitation forecast; check official weather warnings.")
        if humidity is not None and float(humidity) >= 80:
            cautions.append("High humidity may increase heat discomfort.")
        if prefs.activity == "running" and temp >= 30:
            cautions.append("Running in hot conditions can increase heat strain; consider alternatives.")
        result.append({"time": dt.isoformat(), "preference_match_score":score,
            "apparent_temperature_c":round(temp,1), "is_day":is_day, "cautions":cautions,
            "reason":f"Predicted feels-like temperature {temp:.1f}°C; your preferred range is {low:g}–{high:g}°C.",
            "score_type":"transparent_preference_heuristic_not_medical_safety"})
    # rank by preference; caution entries are not suppressed, but never call 'safe'.
    return sorted(result,key=lambda v:(-v["preference_match_score"],len(v["cautions"]),v["time"]))[:limit]
