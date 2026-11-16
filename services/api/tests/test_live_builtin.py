"""Opt-in smoke test for the real first-party integrations.

Run with LUNARIS_LIVE=1. It is skipped in the deterministic default suite.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from lunaris_api.app import create_app
from lunaris_api.config import Settings


@pytest.mark.skipif(os.environ.get("LUNARIS_LIVE") != "1", reason="live network test")
def test_live_weather_heatshield_and_dewa() -> None:
    settings = Settings.for_tests(
        weather_provider="lunaris_api.integrations.builtin:OpenMeteoWeatherProvider",
        climate_engine="lunaris_api.integrations.builtin:ComfortWindowEngine",
        choices_engine="lunaris_api.integrations.builtin:VerifiedChoicesEngine",
    )
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        weather = client.get("/v1/weather/dubai?hours=12")
        assert weather.status_code == 200, weather.text
        assert len(weather.json()["hours"]) == 12
        assert weather.json()["hours"][0]["evidence"]["source_name"] == "Open-Meteo Forecast API"

        windows = client.post(
            "/v1/heatshield/windows",
            json={"activity": "walking", "horizon_hours": 12, "comfort_min_c": 19, "comfort_max_c": 29},
        )
        assert windows.status_code == 200, windows.text
        assert windows.json()["windows"]

        energy = client.post("/v1/choices/energy", json={"monthly_kwh": 2500})
        assert energy.status_code == 200, energy.text
        assert energy.json()["alternatives"][0]["estimated_total_aed"] == 787.50
