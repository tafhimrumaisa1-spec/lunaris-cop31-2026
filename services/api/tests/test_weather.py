from tests.fakes import FakeWeather
from lunaris_api.integrations.ports import Providers


def test_weather_not_integrated_is_503_not_fabricated(client):
    r = client.get("/v1/weather/dubai")
    assert r.status_code == 503 and r.json()["error"]["code"] == "integration_pending"


def test_weather_ok_with_provenance(full):
    c, f = full
    r = c.get("/v1/weather/dubai?hours=12")
    assert r.status_code == 200
    b = r.json()
    assert b["timezone"] == "Asia/Dubai" and b["location_precision"] == "approximate_city_center"
    assert len(b["hours"]) == 12 and b["source_status"]["state"] == "available"
    assert b["cache"] == {"served_from_cache": False, "age_seconds": 0.0}
    assert all(h["evidence"]["data_status"] == "modeled" and h["evidence"]["limitations"] for h in b["hours"])
    assert "not a street-level" in b["notice"]


def test_weather_is_cached(full):
    c, f = full
    c.get("/v1/weather/dubai?hours=6")
    r = c.get("/v1/weather/dubai?hours=6")
    assert f.weather.calls == 1 and r.json()["cache"]["served_from_cache"] is True


def test_outage_serves_stale_then_503(make_client):
    w = FakeWeather()
    c = make_client(providers=Providers(weather=w), weather_cache_ttl_seconds=0, weather_stale_max_seconds=3600)
    assert c.get("/v1/weather/dubai?hours=6").status_code == 200
    w.fail = True
    r = c.get("/v1/weather/dubai?hours=6")
    assert r.status_code == 200
    b = r.json()
    assert b["source_status"]["state"] == "stale" and "unavailable" in b["source_status"]["detail"]
    # a different horizon has no cache entry: honest 503, nothing invented
    r = c.get("/v1/weather/dubai?hours=7")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_unavailable"


def test_outage_without_cache_is_503(make_client):
    w = FakeWeather(); w.fail = True
    c = make_client(providers=Providers(weather=w))
    assert c.get("/v1/weather/dubai").status_code == 503


def test_demo_data_is_labelled_demo(make_client):
    c = make_client(providers=Providers(weather=FakeWeather(status="demo")))
    b = c.get("/v1/weather/dubai?hours=3").json()
    assert b["source_status"]["state"] == "demo" and "NOT a live forecast" in b["source_status"]["detail"]


def test_provider_contract_violations_are_502(make_client):
    for status in ("verified", "self_reported"):
        c = make_client(providers=Providers(weather=FakeWeather(status=status)))
        r = c.get("/v1/weather/dubai?hours=3")
        assert r.status_code == 502 and r.json()["error"]["code"] == "provider_contract_violation"
    w = FakeWeather(); w.override = [{"timestamp": "2026-11-15T00:00:00Z", "humidity_percent": 400}]
    assert make_client(providers=Providers(weather=w)).get("/v1/weather/dubai").status_code == 502
    w2 = FakeWeather(); w2.override = []
    assert make_client(providers=Providers(weather=w2)).get("/v1/weather/dubai").status_code == 503


def test_weather_query_validation(full):
    c, _ = full
    for q in ("hours=0", "hours=500", "hours=abc"):
        assert c.get("/v1/weather/dubai?" + q).status_code == 422
