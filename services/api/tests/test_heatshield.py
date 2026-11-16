from tests.conftest import GOOD_PREFS, auth, new_session

BODY = {"activity": "walking", "horizon_hours": 12, "comfort_min_c": 19, "comfort_max_c": 29}


def test_not_integrated(client):
    assert client.post("/v1/heatshield/windows", json=BODY).json()["error"]["code"] == "integration_pending"


def test_ranked_windows_and_notices(full):
    c, f = full
    r = c.post("/v1/heatshield/windows", json=BODY)
    assert r.status_code == 200
    b = r.json()
    assert [w["comfort_rank"] for w in b["windows"]] == sorted(w["comfort_rank"] for w in b["windows"])
    assert b["comfort_range_c"] == [19, 29]
    assert any("not medical advice" in n for n in b["notices"])
    assert b["source_status"]["state"] == "available"
    assert all(w["evidence"]["data_status"] == "modeled" for w in b["windows"])
    assert f.climate.last_params["location"] is None


def test_uses_saved_preferences_when_range_omitted(full):
    c, f = full
    s = new_session(c); h = auth(s["session_token"])
    body = {"activity": "walking"}
    assert c.post("/v1/heatshield/windows", json=body).json()["error"]["code"] == "comfort_range_required"
    c.put("/v1/preferences", json=GOOD_PREFS, headers=h)
    r = c.post("/v1/heatshield/windows", json=body, headers=h)
    assert r.status_code == 200 and r.json()["comfort_range_c"] == [19, 29]


def test_request_validation(full):
    c, _ = full
    bad = [{**BODY, "comfort_min_c": 30}, {**BODY, "comfort_max_c": None}, {**BODY, "horizon_hours": 0}, {**BODY, "horizon_hours": 999},
           {**BODY, "activity": "Not A Slug"}, {**BODY, "window_minutes": 5}, {**BODY, "extra": 1}, {}]
    for b in bad:
        assert c.post("/v1/heatshield/windows", json=b).status_code == 422, b


def test_unsupported_city(full):
    c, _ = full
    r = c.post("/v1/heatshield/windows", json={**BODY, "city_id": "london"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "city_not_supported"


def test_location_requires_consent_is_coarsened_and_bounded(full):
    c, f = full
    loc = {"latitude": 25.204849, "longitude": 55.270783, "consent": False}
    assert c.post("/v1/heatshield/windows", json={**BODY, "location": loc}).json()["error"]["code"] == "geolocation_consent_required"
    r = c.post("/v1/heatshield/windows", json={**BODY, "location": {**loc, "consent": True}})
    assert r.status_code == 200
    assert f.climate.last_params["location"] == {"latitude": 25.2, "longitude": 55.27}
    far = {"latitude": 51.5, "longitude": -0.12, "consent": True}
    assert c.post("/v1/heatshield/windows", json={**BODY, "location": far}).json()["error"]["code"] == "location_outside_city"


def test_engine_input_error_is_422(full):
    c, _ = full
    r = c.post("/v1/heatshield/windows", json={**BODY, "activity": "teleporting"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_heatshield_input"


def test_engine_contract_violations(full):
    from tests.fakes import evidence
    c, f = full
    ok = {"start": "2026-11-15T01:00:00Z", "end": "2026-11-15T02:00:00Z", "comfort_rank": 1, "heat_caution": "low", "reason_codes": [], "evidence": evidence()}
    cases = [
        [{**ok, "heat_caution": "safe"}],                     # 'safe' is not a contract value
        [{**ok, "evidence": evidence("verified")}],            # verified cannot come from a forecast engine
        [{**ok, "end": "2026-11-15T00:00:00Z"}],               # end before start
        [ok, {**ok, "start": "2026-11-15T03:00:00Z", "end": "2026-11-15T04:00:00Z"}],  # duplicate rank
    ]
    for raw in cases:
        f.climate.raw = raw
        r = c.post("/v1/heatshield/windows", json=BODY)
        assert r.status_code == 502 and r.json()["error"]["code"] == "provider_contract_violation", raw


def test_weather_outage_propagates_as_503(full):
    c, f = full
    f.weather.fail = True
    assert c.post("/v1/heatshield/windows", json=BODY).status_code == 503
