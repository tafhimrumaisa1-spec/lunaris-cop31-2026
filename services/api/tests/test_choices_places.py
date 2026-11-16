import pytest

from lunaris_api.integrations.ports import Providers
from tests.fakes import evidence


@pytest.mark.parametrize("kind", ["travel", "food", "energy"])
def test_not_integrated(client, kind):
    r = client.post(f"/v1/choices/{kind}", json={"x": 1})
    assert r.status_code == 503 and r.json()["error"]["code"] == "integration_pending"


@pytest.mark.parametrize("kind", ["travel", "food", "energy"])
def test_ok_returns_contract_shape(full, kind):
    c, _ = full
    r = c.post(f"/v1/choices/{kind}", json={"distance_km": 5})
    assert r.status_code == 200
    b = r.json()
    assert set(b) == {"choice_id", "comparison_type", "alternatives", "estimated_impacts", "assumptions", "evidence"}
    assert b["comparison_type"] == kind and b["evidence"]


def test_domain_validation_is_delegated(full):
    c, _ = full
    r = c.post("/v1/choices/travel", json={"bad": True})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_choice_input"


def test_envelope_validation(full):
    c, _ = full
    assert c.post("/v1/choices/travel", content=b'{"a": NaN}', headers={"Content-Type": "application/json"}).status_code in (400, 422)
    assert c.post("/v1/choices/travel", json=[1, 2]).status_code == 422
    deep = cur = {}
    for _ in range(12):
        cur["n"] = {}; cur = cur["n"]
    assert c.post("/v1/choices/travel", json=deep).json()["error"]["code"] == "invalid_payload"


def test_engine_contract_violations(full):
    c, f = full
    base = {"choice_id": "x", "comparison_type": "travel", "alternatives": [], "estimated_impacts": [], "assumptions": [], "evidence": [evidence()]}
    cases = [
        {**base, "evidence": []},                       # unsourced estimate
        {**base, "comparison_type": "food"},            # wrong type for route
        {**base, "evidence": [evidence("verified")]},   # estimates cannot be 'verified'
        {**base, "evidence": [evidence("self_reported")]},
        {**base, "comparison_type": "emissions"},
    ]
    for raw in cases:
        f.choices.raw = raw
        r = c.post("/v1/choices/travel", json={"d": 1})
        assert r.status_code == 502, raw


def test_places_not_integrated_is_empty_and_labelled(client):
    b = client.get("/v1/places").json()
    assert b["places"] == [] and b["source_status"]["state"] == "not_integrated"


class FakePlaces:
    def __init__(self, items): self.items = items
    def list_places(self, *, city_id, category, limit): return self.items


def test_places_pass_through_and_validation(make_client):
    good = {"id": "p1", "name": "Fixture Cafe", "data_status": "demo", "evidence": [evidence("demo")], "category": "cafes"}
    c = make_client(providers=Providers(places=FakePlaces([good])))
    b = c.get("/v1/places?category=cafes").json()
    assert b["places"][0]["category"] == "cafes" and b["source_status"]["state"] == "demo"
    c2 = make_client(providers=Providers(places=FakePlaces([{"id": "p1", "name": "x", "data_status": "demo", "evidence": []}])))
    assert c2.get("/v1/places").status_code == 502  # a place without evidence is rejected, not shown
    assert c.get("/v1/places?limit=0").status_code == 422
    assert c.get("/v1/places?category=Bad Value").status_code == 422


class FakeBiz:
    def __init__(self, status="self_reported"): self.status = status
    def get_profile(self, business_id):
        if business_id == "missing":
            return None
        return {"id": business_id, "disclosure_status": self.status, "evidence": [evidence("self_reported")]}


def test_business_evidence(make_client):
    c = make_client(providers=Providers(business=FakeBiz()))
    b = c.get("/v1/business-evidence/abc-1").json()
    assert b["disclosure_status"] == "self_reported" and "not a certification" in b["notice"]
    assert c.get("/v1/business-evidence/missing").status_code == 404
    assert c.get("/v1/business-evidence/bad id!").status_code == 422
    c2 = make_client(providers=Providers(business=FakeBiz("independently_verified")))
    assert c2.get("/v1/business-evidence/abc").status_code == 502  # MVP cannot assert independent verification
    c3 = make_client(providers=Providers(business=FakeBiz("certified")))
    assert c3.get("/v1/business-evidence/abc").status_code == 502


def test_business_not_integrated(client):
    assert client.get("/v1/business-evidence/abc").status_code == 503
