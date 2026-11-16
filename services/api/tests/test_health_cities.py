def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "ok" and b["database"]["state"] == "available"
    assert set(b["integrations"].values()) == {"not_integrated"}  # honest: nothing bound
    assert b["scheduler"]["jobs"] == []  # no fake recurring jobs
    assert b["auth_mode"] == "guest_session"
    assert r.headers["x-request-id"] and r.headers["x-content-type-options"] == "nosniff"


def test_cities_dubai_only_supported(client):
    cities = client.get("/v1/cities").json()["cities"]
    by_id = {c["id"]: c for c in cities}
    assert by_id["dubai"]["support_status"] == "supported"
    assert by_id["dubai"]["timezone"] == "Asia/Dubai"
    assert [c["id"] for c in cities if c["support_status"] == "supported"] == ["dubai"]
    assert cities[0]["id"] == "dubai"  # supported first
    assert all(c["support_status"] in {"preview", "unsupported"} for c in cities if c["id"] != "dubai")
    assert set(cities[0]) == {"id", "name", "country_code", "timezone", "support_status", "center_lat", "center_lon"}


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/v1/nope")
    assert r.status_code == 404
    e = r.json()["error"]
    assert e["code"] == "not_found" and e["request_id"] == r.headers["x-request-id"]
