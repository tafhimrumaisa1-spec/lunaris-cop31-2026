from sqlalchemy import select

from lunaris_api.db.models import AuditLogRow, ImpactRecordRow, MissionRow
from lunaris_api.db.seed import DEMO_MISSION_ID
from tests.conftest import auth, new_session

URL = f"/v1/missions/{DEMO_MISSION_ID}/interest"


def test_missions_lists_explicit_demo(client):
    b = client.get("/v1/missions").json()
    assert [m["id"] for m in b["missions"]] == [DEMO_MISSION_ID]
    m = b["missions"][0]
    assert m["status"] == "demo" and m["verification_status"] == "unverified" and m["organizer_id"] is None
    assert b["source_status"]["state"] == "demo" and "demonstration" in b["source_status"]["detail"]
    assert m["title"].startswith("DEMO")


def test_no_demo_seed_by_default_flag(make_client):
    c = make_client(seed_demo_data=False)
    b = c.get("/v1/missions").json()
    assert b["missions"] == [] and b["source_status"]["state"] == "available"


def test_interest_requires_session_and_consent(authed):
    c, h, _ = authed
    assert c.post(URL, json={"consent": True}).status_code == 401
    r = c.post(URL, json={"consent": False}, headers=h)
    assert r.status_code == 422 and r.json()["error"]["code"] == "consent_required"
    assert c.post(URL, json={}, headers=h).status_code == 422
    assert c.post(URL, json={"consent": True, "extra": "x"}, headers=h).status_code == 422


def test_interest_never_claims_registration_and_is_audited(authed):
    c, h, s = authed
    r = c.post(URL, json={"consent": True}, headers=h)
    assert r.status_code == 201
    b = r.json()
    assert b["registration_confirmed"] is False and b["status"] == "interest_recorded" and b["mission_status"] == "demo"
    assert "not a real event" in b["notice"]
    with c.app.state.session_factory() as db:
        logs = db.scalars(select(AuditLogRow).where(AuditLogRow.action == "mission_interest.created")).all()
    assert len(logs) == 1 and logs[0].actor_user_id == s["user_id"] and logs[0].subject_id == DEMO_MISSION_ID


def test_duplicate_interest_is_409(authed):
    c, h, _ = authed
    assert c.post(URL, json={"consent": True}, headers=h).status_code == 201
    r = c.post(URL, json={"consent": True}, headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_expressed_interest"


def test_unknown_and_unapproved_missions(authed):
    c, h, _ = authed
    assert c.post("/v1/missions/nope/interest", json={"consent": True}, headers=h).status_code == 404
    assert c.post("/v1/missions/bad id!/interest", json={"consent": True}, headers=h).status_code == 422
    with c.app.state.session_factory() as db:
        for mid, st, perm in [("m_prop", "proposed", "unknown"), ("m_appr_noperm", "approved", "pending"), ("m_ok", "approved", "approved")]:
            db.add(MissionRow(id=mid, title=mid, city_id="dubai", status=st, permission_status=perm, verification_status="unverified"))
        db.commit()
    for mid in ("m_prop", "m_appr_noperm"):
        r = c.post(f"/v1/missions/{mid}/interest", json={"consent": True}, headers=h)
        assert r.status_code == 409 and r.json()["error"]["code"] == "mission_not_accepting_interest"
    r = c.post("/v1/missions/m_ok/interest", json={"consent": True}, headers=h)
    assert r.status_code == 201 and "not a registration" in r.json()["notice"]


def test_impact_requires_session_and_starts_empty_with_no_verified(authed):
    c, h, _ = authed
    assert c.get("/v1/impact").status_code == 401
    b = c.get("/v1/impact", headers=h).json()
    assert b["records"] == [] and b["verification_counts"] == {"self_reported": 0, "reviewed": 0, "verified": 0}
    assert "never combined" in b["notice"]


def test_impact_is_per_user_and_counts_statuses_separately(client):
    from datetime import datetime, timezone
    from tests.fakes import evidence
    a, b = new_session(client), new_session(client)
    with client.app.state.session_factory() as db:
        db.add(ImpactRecordRow(id="imp1", user_id=a["user_id"], action_type="walk", verification_status="self_reported",
                               impact_estimate={"kg_co2e": 0.4, "unit": "kg CO2e"}, evidence=[evidence("self_reported")],
                               created_at=datetime.now(timezone.utc)))
        db.commit()
    ra = client.get("/v1/impact", headers=auth(a["session_token"])).json()
    assert len(ra["records"]) == 1 and ra["verification_counts"] == {"self_reported": 1, "reviewed": 0, "verified": 0}
    assert client.get("/v1/impact", headers=auth(b["session_token"])).json()["records"] == []


def test_db_rejects_invalid_verification_status(client):
    import pytest
    from datetime import datetime, timezone
    from sqlalchemy.exc import IntegrityError
    s = new_session(client)
    with client.app.state.session_factory() as db:
        db.add(ImpactRecordRow(id="bad", user_id=s["user_id"], action_type="x", verification_status="certified",
                               impact_estimate=None, evidence=[], created_at=datetime.now(timezone.utc)))
        with pytest.raises(IntegrityError):
            db.commit()
