"""Mountable API router; no environmental numbers are fabricated on source outage."""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from functools import lru_cache
import math
import pandas as pd
import joblib
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import MODEL_FILE, REPORT_FILE, ALLOWED_ORIGINS
from .sources import get_live_forecast, ProviderError
from .ml import frame_for_live_forecast, FEATURES
from .recommendations import Preferences, rank_hours

router = APIRouter()

class WindowRequest(BaseModel):
    preferences: Preferences = Field(default_factory=Preferences)
    days: int = Field(default=3, ge=1, le=5)
    limit: int = Field(default=6, ge=1, le=24)

@lru_cache(maxsize=1)
def load_model(path_str: str, modified: float):
    return joblib.load(path_str)

def get_artifact():
    if not MODEL_FILE.exists():
        return None
    return load_model(str(MODEL_FILE), MODEL_FILE.stat().st_mtime)

@router.get("/v1/climate-ai/status")
def ai_status():
    artifact = get_artifact()
    if artifact is None:
        return {"status":"untrained", "model_available":False, "ml_deployed":False, "reason":"No trained artifact installed; using source forecast if available."}
    report=artifact["report"]
    return {"status":"evaluated", "model_available":True, "ml_deployed":bool(artifact["deploy_ml"]),
            "reference_kind":report.get("reference_caveat"),"test_results": {"baseline":report["test_baseline"], "ml":report["test_ml"]},
            "model_card":"/v1/climate-ai/evaluation"}

@router.get("/v1/climate-ai/evaluation")
def evaluation():
    if not REPORT_FILE.exists():
        raise HTTPException(status_code=404, detail="No evaluation generated yet: train on real provider data")
    return json.loads(REPORT_FILE.read_text())

def flatten_live(payload: dict, days: int) -> list[dict]:
    hourly = payload["hourly"]
    frame = frame_for_live_forecast(hourly)
    artifact = get_artifact()
    use_ml = bool(artifact and artifact["deploy_ml"])
    pred = None
    if use_ml:
        try:
            pred = artifact["model"].predict(frame[FEATURES])
        except (ValueError, TypeError):
            use_ml = False
    now_local = datetime.now(ZoneInfo("Asia/Dubai"))
    max_dt = now_local + timedelta(days=days)
    rows=[]
    for i, row in frame.iterrows():
        t = row["time"]
        if pd.isna(t):
            continue
        local_dt = t.to_pydatetime().replace(tzinfo=ZoneInfo("Asia/Dubai"))
        if not (now_local <= local_dt <= max_dt):
            continue
        raw = row.get("apparent_temperature")
        if pd.isna(raw):
            continue
        # Historical training uses exactly ~24-hour lead; do not correct other horizons.
        hours_ahead = (local_dt - now_local).total_seconds() / 3600
        apply_ml = bool(use_ml and pred is not None and 22 <= hours_ahead <= 26 and math.isfinite(pred[i]))
        corrected = float(pred[i]) if apply_ml else float(raw)
        def val(k):
            x=row.get(k)
            return None if x is None or pd.isna(x) else float(x)
        rows.append({"time":local_dt.isoformat(),"apparent_temperature_c":round(corrected,2),
                     "raw_provider_apparent_temperature_c": round(float(raw),2),
                     "cloud_cover_pct":val("cloud_cover"), "relative_humidity_pct":val("relative_humidity_2m"),
                     "precipitation_mm":val("precipitation"), "is_day":bool(row.get("is_day")) if not pd.isna(row.get("is_day")) else None,
                     "forecast_method":"experimental_ml_bias_correction_24h_lead" if apply_ml else "open_meteo_original_forecast"})
    return rows

@router.post("/v1/heatshield/ai-windows")
def heatshield_windows(request:WindowRequest):
    try:
        live = get_live_forecast(request.days)
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=f"Live weather unavailable; no fallback numbers invented. {exc}") from exc
    hours = flatten_live(live,request.days)
    if not hours:
        raise HTTPException(status_code=503, detail="No usable future forecast hours")
    ranked = rank_hours(hours, request.preferences, request.limit)
    artifact = get_artifact()
    is_ml = any(h["forecast_method"].startswith("experimental_ml") for h in hours)
    return {"city":"Dubai", "country":"United Arab Emirates", "timezone":"Asia/Dubai", "windows":ranked,
            "weather_source":"Open-Meteo Forecast API", "weather_url":"https://open-meteo.com/en/docs", 
            "prediction_method":"mixed_24h_experimental_ml_and_provider" if is_ml else "third_party_forecast_no_ml",
            "ml_evaluation_available":bool(artifact),
            "ml_status":"validation_gate_passed" if is_ml else ("validation_gate_failed" if artifact else "not_trained"),
            "data_kind":"model_forecast_not_station_measurements", "personalization_method":"transparent_rules_not_trained_model",
            "limitations":["Gridpoint forecasts do not represent precise street-level conditions.",
                           "Comfort scores reflect stated preferences, not an assessment of individual safety.",
                           "Check official hazardous weather and heat advisories before outdoor activity.",
                           "Model correction, if enabled, applies only around 24-hour live lead; all other horizons use the provider forecast."]}

@router.get("/v1/climate-ai/health")
def health():
    return {"ok":True, "service":"lunaris-climate-engine", "city":"Dubai", "ml_trained": MODEL_FILE.exists()}

def create_app() -> FastAPI:
    app = FastAPI(title="LUNARIS Climate Intelligence",version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type"])
    app.include_router(router)
    return app

app = create_app()
