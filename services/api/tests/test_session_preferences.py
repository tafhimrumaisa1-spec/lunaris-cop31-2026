from sqlalchemy import select

from lunaris_api.db.models import SessionRow
from lunaris_api.core.tokens import hash_token

from .conftest import GOOD_PREFS, auth, new_session


def test_session_token_is_never_stored_in_plaintext(client):
    s = new_session(client)
    assert s["auth_mode"] == "guest_session" and "not a verified identity" in s["notice"]
    with client.app.state.session_factory() as db:
        rows = db.scalars(select(SessionRow)).all()
    assert len(rows) == 1
    assert rows[0].token_hash != s["session_token"]
    assert rows[0].token_hash == hash_token(client.app.state.settings.session_secret, s["session_token"])


def test_preferences_require_session(client):
    r = client.put("/v1/preferences", json=GOOD_PREFS)
    assert r.status_code == 401 and r.json()["error"]["code"] == "session_required"
    g = client.get("/v1/preferences").json()
    assert g["preferences"] is None and g["persisted"] is False  # no invented defaults


def test_preferences_roundtrip_and_isolation(client):
    a, b = new_session(client), new_session(client)
    r = client.put("/v1/preferences", json=GOOD_PREFS, headers=auth(a["session_token"]))
    assert r.status_code == 200 and r.json()["persisted"] is True
    got = client.get("/v1/preferences", headers=auth(a["session_token"])).json()["preferences"]
    assert got["comfort_min_c"] == 19 and got["user_id"] == a["user_id"]
    assert client.get("/v1/preferences", headers=auth(b["session_token"])).json()["preferences"] is None
    # update, not duplicate
    r = client.put("/v1/preferences", json={**GOOD_PREFS, "comfort_max_c": 31}, headers=auth(a["session_token"]))
    assert r.json()["preferences"]["comfort_max_c"] == 31


def test_preferences_validation(authed):
    c, h, _ = authed
    bad = [
        {**GOOD_PREFS, "comfort_min_c": 30, "comfort_max_c": 20},
        {**GOOD_PREFS, "comfort_min_c": 19, "comfort_max_c": 19},
        {**GOOD_PREFS, "comfort_max_c": 500},
        {**GOOD_PREFS, "weather_moods": ["apocalypse"]},
        {**GOOD_PREFS, "activities": ["base-jumping"]},
        {**GOOD_PREFS, "priorities": ["Bad Slug!"]},
        {**GOOD_PREFS, "notification_consent": "maybe"},
        {**GOOD_PREFS, "unexpected": 1},
        {k: v for k, v in GOOD_PREFS.items() if k != "city_id"},
    ]
    for body in bad:
        r = c.put("/v1/preferences", json=body, headers=h)
        assert r.status_code == 422, body
        assert r.json()["error"]["code"] == "validation_error"


def test_validation_errors_do_not_echo_input(authed):
    c, h, _ = authed
    r = c.put("/v1/preferences", json={**GOOD_PREFS, "priorities": ["secret@example.com"]}, headers=h)
    assert r.status_code == 422
    assert "secret@example.com" not in r.text


def test_preferences_city_rules(authed):
    c, h, s = authed
    r = c.put("/v1/preferences", json={**GOOD_PREFS, "city_id": "london"}, headers=h)
    assert r.status_code == 422 and r.json()["error"]["code"] == "city_not_supported"
    r = c.put("/v1/preferences", json={**GOOD_PREFS, "city_id": "atlantis"}, headers=h)
    assert r.json()["error"]["code"] == "unknown_city"
    r = c.put("/v1/preferences", json={**GOOD_PREFS, "user_id": "someone-else"}, headers=h)
    assert r.status_code == 403
    r = c.put("/v1/preferences", json={**GOOD_PREFS, "user_id": s["user_id"]}, headers=h)
    assert r.status_code == 200


def test_invalid_expired_and_revoked_tokens(make_client):
    from datetime import datetime, timedelta, timezone
    now = {"t": datetime(2026, 11, 15, tzinfo=timezone.utc)}
    c = make_client(clock=lambda: now["t"], session_ttl_days=1)
    s = new_session(c)
    h = auth(s["session_token"])
    assert c.get("/v1/session", headers=h).status_code == 200
    assert c.get("/v1/session", headers=auth("x" * 40)).status_code == 401
    assert c.get("/v1/session", headers=auth("short")).status_code == 401
    now["t"] += timedelta(days=2)
    assert c.get("/v1/session", headers=h).json()["error"]["code"] == "invalid_session"
    now["t"] -= timedelta(days=2)
    assert c.delete("/v1/session", headers=h).status_code == 204
    assert c.get("/v1/session", headers=h).status_code == 401
    # a presented-but-bad token is never silently treated as guest
    assert c.get("/v1/preferences", headers=auth("y" * 40)).status_code == 401


def test_erase_me_removes_everything(client):
    s = new_session(client)
    h = auth(s["session_token"])
    client.put("/v1/preferences", json=GOOD_PREFS, headers=h)
    client.post("/v1/missions/mission_demo_shade_survey/interest", json={"consent": True}, headers=h)
    assert client.delete("/v1/me", headers=h).status_code == 204
    assert client.get("/v1/session", headers=h).status_code == 401
    from lunaris_api.db.models import AuditLogRow, MissionInterestRow, PreferencesRow, UserRow
    with client.app.state.session_factory() as db:
        assert db.scalars(select(UserRow)).all() == []
        assert db.scalars(select(PreferencesRow)).all() == []
        assert db.scalars(select(MissionInterestRow)).all() == []
        assert all(a.actor_user_id is None for a in db.scalars(select(AuditLogRow)).all())
