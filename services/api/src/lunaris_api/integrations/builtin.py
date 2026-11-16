"""First-party integrations assembled from the verified agent handoffs.

These providers are deliberately small and synchronous because the platform ports are
synchronous. They do not invent fallback values: network or shape failures raise
ProviderUnavailable and the API's stale-cache policy decides what may be served.
"""
from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from .ports import InvalidInput, ProviderUnavailable

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_DOCS = "https://open-meteo.com/en/docs"
DEWA_TARIFF_URL = "https://www.dewa.gov.ae/en/consumer/billing/slab-tariff"


def _utc_iso(value: datetime) -> str:
    return value.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")


class OpenMeteoWeatherProvider:
    """Dubai forecast provider, verified against a live response on 2026-11-15."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_hourly(
        self, *, city_id: str, latitude: float, longitude: float, timezone: str, hours: int
    ) -> Sequence[Mapping[str, Any]]:
        if city_id != "dubai":
            raise InvalidInput("Only Dubai is supported by this provider.")
        requested = max(1, min(int(hours), 120))
        forecast_days = max(1, min(6, math.ceil(requested / 24) + 1))
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,weather_code,is_day",
                "timezone": timezone,
                "forecast_days": forecast_days,
            }
        )
        request = urllib.request.Request(
            f"{OPEN_METEO_URL}?{query}",
            headers={"User-Agent": "LUNARIS/0.1 source-aware weather client"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise ProviderUnavailable("Open-Meteo forecast could not be retrieved.") from exc

        hourly = payload.get("hourly")
        if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
            raise ProviderUnavailable("Open-Meteo returned an incomplete hourly response.")
        keys = (
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation_probability",
            "weather_code",
            "is_day",
        )
        if any(not isinstance(hourly.get(key), list) for key in keys):
            raise ProviderUnavailable("Open-Meteo response omitted a required hourly series.")

        try:
            local_zone = ZoneInfo(timezone)
        except Exception as exc:  # noqa: BLE001
            raise InvalidInput("Unsupported city timezone.") from exc
        retrieved = datetime.now(dt_timezone.utc)
        rows: list[dict[str, Any]] = []
        for index, raw_time in enumerate(hourly["time"]):
            try:
                local_time = datetime.fromisoformat(raw_time).replace(tzinfo=local_zone)
                values = {key: hourly[key][index] for key in keys}
            except (ValueError, IndexError, TypeError) as exc:
                raise ProviderUnavailable("Open-Meteo hourly arrays were inconsistent.") from exc
            valid_at = local_time.astimezone(dt_timezone.utc)
            rows.append(
                {
                    "timestamp": _utc_iso(valid_at),
                    "temperature_c": values["temperature_2m"],
                    "apparent_temperature_c": values["apparent_temperature"],
                    "humidity_percent": values["relative_humidity_2m"],
                    "precip_probability_percent": values["precipitation_probability"],
                    "weather_code": values["weather_code"],
                    "is_day": bool(values["is_day"]) if values["is_day"] is not None else None,
                    "evidence": {
                        "source_name": "Open-Meteo Forecast API",
                        "source_url": OPEN_METEO_DOCS,
                        "retrieved_at": _utc_iso(retrieved),
                        "valid_at": _utc_iso(valid_at),
                        "data_status": "live",
                        "method": "Best Match numerical weather model forecast for the Dubai city-centre grid point.",
                        "limitations": [
                            "Model forecast, not a street-level measurement or guarantee.",
                            "Approximate city-centre grid point; local shade and surfaces are not represented.",
                        ],
                        "license_note": "Open-Meteo data CC BY 4.0; free API restricted to non-commercial use.",
                        "location_precision": "approximate_city_center",
                        "model_id": "best_match",
                        "uncertainty": "No calibrated interval supplied by this endpoint.",
                    },
                }
            )
        now = datetime.now(dt_timezone.utc) - timedelta(minutes=30)
        future = [row for row in rows if datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")) >= now]
        return future[:requested]


class ComfortWindowEngine:
    """Transparent comfort-preference ranking; not a safety or medical model."""

    _ACTIVITIES = {"walk", "walking", "run", "exercise", "cycle", "outdoor"}

    def rank_windows(
        self, *, hours: Sequence[Mapping[str, Any]], params: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        activity = str(params.get("activity", "")).lower()
        if activity not in self._ACTIVITIES:
            raise InvalidInput(f"Unsupported activity {activity!r}.")
        lo = float(params["comfort_min_c"])
        hi = float(params["comfort_max_c"])
        if lo >= hi:
            raise InvalidInput("comfort_min_c must be below comfort_max_c")
        duration = int(params.get("window_minutes", 60))
        maximum = int(params.get("max_windows", 5))
        now = datetime.now(dt_timezone.utc)
        candidates: list[tuple[float, Mapping[str, Any], datetime]] = []
        for hour in hours:
            stamp = datetime.fromisoformat(str(hour["timestamp"]).replace("Z", "+00:00"))
            if stamp < now:
                continue
            temp = hour.get("temperature_c")
            apparent = hour.get("apparent_temperature_c")
            humidity = hour.get("humidity_percent")
            rain = hour.get("precip_probability_percent")
            if temp is None or apparent is None:
                continue
            centre = (lo + hi) / 2
            distance = lo - temp if temp < lo else temp - hi if temp > hi else abs(temp - centre) * 0.18
            heat = 12 if apparent >= 40 else 5 if apparent >= 35 else 0
            exertion = 3 if activity in {"run", "exercise", "cycle"} and apparent >= 32 else 0
            rain_penalty = (float(rain) if rain is not None else 0) * 0.03
            humidity_penalty = max(0, (float(humidity) if humidity is not None else 0) - 75) * 0.03
            candidates.append((distance + heat + exertion + rain_penalty + humidity_penalty, hour, stamp))
        candidates.sort(key=lambda item: (item[0], item[2]))
        output = []
        for rank, (_, hour, stamp) in enumerate(candidates[:maximum], start=1):
            apparent = float(hour["apparent_temperature_c"])
            caution = "elevated" if apparent >= 40 else "moderate" if apparent >= 35 else "low"
            reasons = ["closest_to_personal_comfort_range"]
            if caution != "low":
                reasons.append("apparent_temperature_caution")
            if (hour.get("precip_probability_percent") or 0) >= 50:
                reasons.append("precipitation_probability_high")
            source_evidence = dict(hour["evidence"])
            evidence = {
                **source_evidence,
                "valid_at": _utc_iso(stamp),
                "data_status": "modeled",
                "method": "Transparent ranking of live model-forecast hours against the user's chosen comfort range.",
                "assumptions": [f"Personal comfort range {lo:g}–{hi:g} °C", f"Activity: {activity}"],
                "limitations": list(source_evidence.get("limitations", []))
                + ["Preference fit is not physiological safety or medical advice."],
            }
            output.append(
                {
                    "start": _utc_iso(stamp),
                    "end": _utc_iso(stamp + timedelta(minutes=duration)),
                    "comfort_rank": rank,
                    "heat_caution": caution,
                    "reason_codes": reasons,
                    "evidence": evidence,
                }
            )
        return output


class VerifiedChoicesEngine:
    """Adapter around Agent 03 services plus the verified DEWA tariff calculation."""

    def compare(self, *, kind: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            if kind == "energy" and "monthly_kwh" in payload:
                return self._dewa_energy(payload)
            from lunaris_choices import calculate_energy, compare_food, compare_travel
            from lunaris_choices import ValidationFailure

            fn = {"travel": compare_travel, "food": compare_food, "energy": calculate_energy}.get(kind)
            if fn is None:
                raise InvalidInput(f"Unsupported comparison kind {kind!r}.")
            try:
                result = fn(dict(payload)).to_dict()
            except ValidationFailure as exc:
                raise InvalidInput(str(exc)) from exc
            warnings = result.pop("warnings", [])
            result["assumptions"].extend(
                f"{w['code']}: {w['message']}" for w in warnings if w.get("severity") != "info"
            )
            return result
        except ImportError as exc:
            raise ProviderUnavailable("The choices package is not installed.") from exc

    @staticmethod
    def _dewa_energy(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        allowed = {"monthly_kwh"}
        if set(payload) - allowed:
            raise InvalidInput("Official DEWA tariff mode accepts only monthly_kwh.")
        try:
            kwh = float(payload["monthly_kwh"])
        except (TypeError, ValueError, KeyError) as exc:
            raise InvalidInput("monthly_kwh must be a number.") from exc
        if not math.isfinite(kwh) or kwh < 0 or kwh > 100000:
            raise InvalidInput("monthly_kwh must be between 0 and 100000.")
        remaining = kwh
        base = 0.0
        breakdown = []
        lower = 0.0
        for upper, rate in ((2000.0, 0.23), (4000.0, 0.28), (6000.0, 0.32), (float("inf"), 0.38)):
            amount = min(remaining, upper - lower)
            if amount > 0:
                cost = amount * rate
                base += cost
                breakdown.append({"from_kwh": lower, "to_kwh": None if math.isinf(upper) else upper, "usage_kwh": round(amount, 3), "rate_aed_per_kwh": rate, "cost_aed": round(cost, 2)})
                remaining -= amount
            lower = upper
            if remaining <= 0:
                break
        fuel = kwh * 0.06
        subtotal = base + fuel
        vat = subtotal * 0.05
        total = subtotal + vat
        now = _utc_iso(datetime.now(dt_timezone.utc))
        return {
            "choice_id": f"energy:dewa:{round(kwh, 3)}",
            "comparison_type": "energy",
            "alternatives": [{"monthly_kwh": round(kwh, 3), "slab_breakdown": breakdown, "base_tariff_aed": round(base, 2), "fuel_surcharge_aed": round(fuel, 2), "vat_aed": round(vat, 2), "estimated_total_aed": round(total, 2)}],
            "estimated_impacts": [{"type": "cost_estimate", "unit": "AED", "value": round(total, 2)}],
            "assumptions": ["Residential/commercial slab tariff.", "November 2026 electricity fuel surcharge: AED 0.060/kWh.", "5% VAT applied to tariff plus fuel surcharge.", "Meter service charge and other account adjustments excluded."],
            "evidence": [{"source_name": "Dubai Electricity and Water Authority", "source_url": DEWA_TARIFF_URL, "retrieved_at": now, "valid_at": None, "data_status": "live", "method": "Progressive published slab tariff plus published monthly fuel surcharge and VAT.", "limitations": ["Estimate is not a bill.", "Meter service charge and account-specific adjustments are excluded."], "license_note": "Official DEWA public tariff page; all rights reserved.", "location_precision": "Dubai"}],
        }
