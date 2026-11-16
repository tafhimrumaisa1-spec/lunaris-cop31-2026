from datetime import datetime, timedelta, timezone

from lunaris_api.integrations.builtin import ComfortWindowEngine, VerifiedChoicesEngine


def evidence(valid):
    return {
        "source_name": "Open-Meteo Forecast API",
        "source_url": "https://open-meteo.com/en/docs",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "valid_at": valid.isoformat(),
        "data_status": "live",
        "method": "model forecast",
        "limitations": ["not street-level"],
    }


def test_comfort_window_engine_ranks_real_hours():
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    hours = [
        {"timestamp": (now + timedelta(hours=i)).isoformat(), "temperature_c": t, "apparent_temperature_c": a,
         "humidity_percent": 55, "precip_probability_percent": 5, "weather_code": 0, "is_day": True,
         "evidence": evidence(now + timedelta(hours=i))}
        for i, (t, a) in enumerate(((34, 38), (27, 29), (24, 25)))
    ]
    result = ComfortWindowEngine().rank_windows(hours=hours, params={"activity": "walk", "comfort_min_c": 20,
        "comfort_max_c": 29, "window_minutes": 60, "max_windows": 3})
    assert result[0]["start"] == hours[2]["timestamp"].replace("+00:00", "Z")
    assert result[0]["heat_caution"] == "low"
    assert result[0]["evidence"]["data_status"] == "modeled"


def test_dewa_progressive_tariff():
    result = VerifiedChoicesEngine().compare(kind="energy", payload={"monthly_kwh": 3500})
    row = result["alternatives"][0]
    assert row["base_tariff_aed"] == 880.0
    assert row["fuel_surcharge_aed"] == 210.0
    assert row["estimated_total_aed"] == 1144.5
    assert result["evidence"][0]["source_name"] == "Dubai Electricity and Water Authority"
