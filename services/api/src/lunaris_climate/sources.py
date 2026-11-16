"""Weather API fetching, caching and integrity checks. Not station observations."""
from __future__ import annotations
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
from .config import DUBAI_LAT, DUBAI_LON, DUBAI_TZ, ROOT

FORECAST_HOST = "https://api.open-meteo.com/v1/forecast"
PREVIOUS_HOST = "https://previous-runs-api.open-meteo.com/v1/forecast"
ARCHIVE_HOST = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_COLS = ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "cloud_cover", "wind_speed_10m", "precipitation", "weather_code", "is_day"]
HIST_PRED_COLS = ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "cloud_cover", "wind_speed_10m"]

class ProviderError(RuntimeError):
    pass

def fetch_json(url: str, params: dict, cache_dir: Path | None = None, ttl_seconds: int | None = None) -> dict:
    """Retries limited to 3; cache raw source responses with retrieval timestamp."""
    cache_dir = Path(cache_dir or ROOT / "data" / "cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest()[:24]
    path = cache_dir / f"{key}.json"
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if ttl_seconds is None or age < ttl_seconds:
            return json.loads(path.read_text())["payload"]
    error = "unknown"
    for i in range(3):
        try:
            res = requests.get(url, params=params, timeout=30, headers={"User-Agent": "LUNARIS-ResearchPrototype/0.1"})
            res.raise_for_status()
            payload = res.json()
            if payload.get("error"):
                raise ProviderError(str(payload.get("reason", "Provider error")))
            if "hourly" not in payload or "time" not in payload["hourly"]:
                raise ProviderError("Missing hourly data")
            path.write_text(json.dumps({"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "url": res.url, "payload": payload}))
            return payload
        except (requests.RequestException, ValueError, ProviderError) as exc:
            error = str(exc)
            if i < 2:
                time.sleep(0.6 * (i + 1))
    raise ProviderError(f"Weather source unavailable: {error}")

def get_live_forecast(days: int = 5, cache_dir: Path | None = None) -> dict:
    if not 1 <= days <= 7:
        raise ValueError("days must be from 1 to 7")
    params = {"latitude": DUBAI_LAT, "longitude": DUBAI_LON, "hourly": ",".join(FORECAST_COLS), "timezone": DUBAI_TZ, "forecast_days": days}
    return fetch_json(FORECAST_HOST, params, cache_dir, ttl_seconds=1800)

def fetch_training_data(start_date: str, end_date: str, cache_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Joined 24-hour lead forecast vs archive reanalysis proxy at the same valid hour.
    Neither source is direct station ground truth. The two may not be independent.
    """
    for date in (start_date, end_date):
        datetime.strptime(date, "%Y-%m-%d")
    if start_date >= end_date:
        raise ValueError("start_date must precede end_date")
    base = {"latitude": DUBAI_LAT, "longitude": DUBAI_LON, "start_date": start_date, "end_date": end_date, "timezone": DUBAI_TZ}
    prev = fetch_json(PREVIOUS_HOST, {**base, "hourly": ",".join(f"{c}_previous_day1" for c in HIST_PRED_COLS)}, cache_dir)
    archived = fetch_json(ARCHIVE_HOST, {**base, "hourly": "apparent_temperature"}, cache_dir)
    p = pd.DataFrame(prev["hourly"])
    a = pd.DataFrame(archived["hourly"])
    rename = {f"{c}_previous_day1": f"f_{c}" for c in HIST_PRED_COLS}
    p = p.rename(columns=rename)
    a = a.rename(columns={"apparent_temperature": "target_apparent_temperature"})
    merged = p.merge(a[["time", "target_apparent_temperature"]], on="time", how="inner", validate="one_to_one")
    merged["time"] = pd.to_datetime(merged["time"], errors="coerce")
    merged = merged.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    metadata = {"location": "Dubai, UAE", "latitude": DUBAI_LAT, "longitude": DUBAI_LON, "timezone": DUBAI_TZ,
                "forecast_source": "Open-Meteo Previous Runs API: previous_day1 (24-hour lead)",
                "reference_source": "Open-Meteo Historical Weather Archive: reanalysis, NOT independent observed ground truth",
                "forecast_documentation": "https://open-meteo.com/en/docs/previous-runs-api",
                "reference_documentation": "https://open-meteo.com/en/docs/historical-weather-api",
                "requested_start": start_date, "requested_end": end_date,
                "meaning": "Experimental correction to model-vs-reanalysis differences; not verified medical risk or station accuracy."}
    return merged, metadata
