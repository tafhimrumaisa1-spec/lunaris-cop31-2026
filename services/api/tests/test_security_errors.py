def test_cors_allowlist(make_client):
    c = make_client(cors_allow_origins=("https://app.example.org",))
    ok = c.options("/v1/cities", headers={"Origin": "https://app.example.org", "Access-Control-Request-Method": "GET"})
    assert ok.status_code == 200 and ok.headers["access-control-allow-origin"] == "https://app.example.org"
    assert "access-control-allow-credentials" not in ok.headers
    bad = c.options("/v1/cities", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert bad.status_code == 400 and "access-control-allow-origin" not in bad.headers
    r = c.get("/v1/cities", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_body_size_limit(make_client):
    c = make_client(max_request_bytes=200)
    r = c.post("/v1/choices/travel", json={"a": "x" * 500})
    assert r.status_code == 413 and r.json()["error"]["code"] == "request_too_large"
    assert r.headers["x-request-id"]


def test_chunked_bodies_rejected(client):
    r = client.post("/v1/choices/travel", content=iter([b'{"a":1}']), headers={"Content-Type": "application/json"})
    assert r.status_code == 411


def test_request_id_echoed_when_valid_and_replaced_when_not(client):
    assert client.get("/health", headers={"X-Request-ID": "abc-12345678"}).headers["x-request-id"] == "abc-12345678"
    assert client.get("/health", headers={"X-Request-ID": "bad id\twith junk"}).headers["x-request-id"] != "bad id\twith junk"


def test_rate_limiting(make_client):
    c = make_client(rate_limit_read_per_min=3)
    codes = [c.get("/v1/cities").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    r = c.get("/v1/cities")
    assert r.json()["error"]["code"] == "rate_limited" and int(r.headers["retry-after"]) >= 1
    assert c.get("/health").status_code == 200  # health is exempt


def test_session_creation_is_strictly_limited(make_client):
    c = make_client(rate_limit_session_per_hour=2)
    assert [c.post("/v1/session").status_code for _ in range(3)] == [201, 201, 429]


def test_x_forwarded_for_ignored_unless_trusted(make_client):
    c = make_client(rate_limit_read_per_min=1)
    assert c.get("/v1/cities", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert c.get("/v1/cities", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429  # spoofing does not dodge the limit
    t = make_client(rate_limit_read_per_min=1, trust_proxy_headers=True)
    assert t.get("/v1/cities", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert t.get("/v1/cities", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200


def test_unhandled_errors_do_not_leak(make_client):
    from lunaris_api.integrations.ports import Providers

    class Boom:
        def fetch_hourly(self, **kw):
            raise RuntimeError("secret internal detail user@example.com")
    c = make_client(providers=Providers(weather=Boom()))
    r = c.get("/v1/weather/dubai")
    assert r.status_code == 503 and "secret" not in r.text and "example.com" not in r.text


def test_docs_toggle(make_client):
    assert make_client(docs_enabled=True).get("/docs").status_code == 200
    assert make_client(docs_enabled=False).get("/docs").status_code == 404
    assert make_client(docs_enabled=False).get("/openapi.json").status_code == 404


def test_method_not_allowed_envelope(client):
    r = client.delete("/v1/cities")
    assert r.status_code == 405 and r.json()["error"]["code"] == "method_not_allowed"
