"""Verify new AI routes coexist with the original API without live network access."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from lunaris_climate import api as ai


def fake_provider_forecast(_days):
    start = datetime.now(ZoneInfo('Asia/Dubai')).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    times = [(start + timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(36)]
    hourly = {
        'time': times,
        'temperature_2m': [28.0] * len(times),
        'relative_humidity_2m': [60.0] * len(times),
        'apparent_temperature': [30.0] * len(times),
        'cloud_cover': [30.0] * len(times),
        'wind_speed_10m': [10.0] * len(times),
        'precipitation': [0.0] * len(times),
        'weather_code': [0] * len(times),
        'is_day': [1] * len(times),
    }
    return {'hourly': hourly}


def test_ai_status_untrained_is_truthful(client, monkeypatch):
    monkeypatch.setattr(ai, 'get_artifact', lambda: None)
    status = client.get('/v1/climate-ai/status')
    assert status.status_code == 200
    assert status.json()['model_available'] is False
    assert status.json()['ml_deployed'] is False


def test_ai_windows_uses_provider_when_model_untrained(client, monkeypatch):
    monkeypatch.setattr(ai, 'get_live_forecast', fake_provider_forecast)
    monkeypatch.setattr(ai, 'get_artifact', lambda: None)
    result = client.post('/v1/heatshield/ai-windows', json={
        'preferences': {'min_comfort_c': 20, 'max_comfort_c': 31, 'activity': 'walking'},
        'days': 2, 'limit': 3
    })
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['ml_status'] == 'not_trained'
    assert data['prediction_method'] == 'third_party_forecast_no_ml'
    assert len(data['windows']) == 3
    assert data['windows'][0]['score_type'] == 'transparent_preference_heuristic_not_medical_safety'


def test_original_heatshield_contract_still_exists(client):
    paths = client.get('/openapi.json').json()['paths']
    assert '/v1/heatshield/windows' in paths
    assert '/v1/heatshield/ai-windows' in paths
