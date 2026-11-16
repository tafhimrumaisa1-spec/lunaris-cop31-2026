"""Test doubles that implement the provider ports. Their output is labelled as test fixtures."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lunaris_api.integrations.ports import InvalidInput, ProviderUnavailable

T0 = datetime(2026, 11, 15, 0, 0, tzinfo=timezone.utc)


def evidence(status: str = "modeled", **kw) -> dict:
    e = {"source_name": "TEST FIXTURE (not real data)", "source_url": None, "retrieved_at": T0.isoformat(),
         "valid_at": None, "data_status": status, "method": "unit-test fixture", "limitations": ["test only"]}
    e.update(kw)
    return e


class FakeWeather:
    def __init__(self, status: str = "modeled"):
        self.calls = 0
        self.fail = False
        self.status = status
        self.override = None

    def fetch_hourly(self, *, city_id, latitude, longitude, timezone, hours):
        self.calls += 1
        if self.fail:
            raise ProviderUnavailable("down")
        if self.override is not None:
            return self.override
        return [{"timestamp": (T0 + timedelta(hours=i)).isoformat(), "temperature_c": 30.0 + i % 5,
                 "apparent_temperature_c": 33.0 + i % 5, "humidity_percent": 60.0, "precip_probability_percent": 0.0,
                 "weather_code": 0, "is_day": 6 <= i % 24 <= 18, "evidence": evidence(self.status)} for i in range(hours + 6)]


class FakeClimate:
    def __init__(self):
        self.last_params = None
        self.raw = None

    def rank_windows(self, *, hours, params):
        self.last_params = dict(params)
        if params["activity"] == "teleporting":
            raise InvalidInput("Unknown activity 'teleporting'.")
        if self.raw is not None:
            return self.raw
        out = []
        for i in range(min(params["max_windows"], 3)):
            start = datetime.fromisoformat(hours[i * 2]["timestamp"].replace("Z", "+00:00"))
            out.append({"start": start.isoformat(), "end": (start + timedelta(minutes=params["window_minutes"])).isoformat(),
                        "comfort_rank": 3 - i, "heat_caution": "elevated", "reason_codes": ["test"], "evidence": evidence("modeled")})
        return out


class FakeChoices:
    def __init__(self):
        self.raw = None

    def compare(self, *, kind, payload):
        if payload.get("bad"):
            raise InvalidInput("distance_km must be positive")
        if self.raw is not None:
            return self.raw
        return {"choice_id": f"{kind}-1", "comparison_type": kind, "alternatives": [{"mode": "walk"}],
                "estimated_impacts": [{"kg_co2e": 0.0, "unit": "kg CO2e"}], "assumptions": ["test"], "evidence": [evidence("modeled")]}
