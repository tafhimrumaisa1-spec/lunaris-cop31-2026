"""Fixtures. Every test gets its own app + its own database (in-memory SQLite by default).

Set LUNARIS_TEST_DATABASE_URL=postgresql+psycopg://... to run the suite on PostgreSQL; the
schema is dropped and recreated per test, so use a dedicated throwaway database.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from lunaris_api.app import create_app
from lunaris_api.config import Settings
from lunaris_api.db.models import Base
from lunaris_api.integrations.ports import Providers

from .fakes import FakeChoices, FakeClimate, FakeWeather

PG_URL = os.environ.get("LUNARIS_TEST_DATABASE_URL")
GOOD_PREFS = {"city_id": "dubai", "weather_moods": ["rainy_cozy", "cloudy_moody"], "comfort_min_c": 19, "comfort_max_c": 29,
              "activities": ["walking", "cafes"], "priorities": ["transit"], "notification_consent": False}


@pytest.fixture
def make_client():
    created = []

    def factory(providers: Providers | None = None, clock=None, **settings_overrides):
        if PG_URL:
            settings_overrides.setdefault("database_url", PG_URL)
        settings = Settings.for_tests(**settings_overrides)
        app = create_app(settings, providers=providers if providers is not None else Providers(), clock=clock)
        if PG_URL:
            Base.metadata.drop_all(app.state.engine)
        client = TestClient(app, raise_server_exceptions=False)
        client.__enter__()  # runs lifespan: creates schema and seeds
        created.append(client)
        return client

    yield factory
    for c in created:
        if PG_URL:
            Base.metadata.drop_all(c.app.state.engine)
        c.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def full(make_client):
    """Client with all fake providers bound; returns (client, fakes)."""
    fakes = type("F", (), {"weather": FakeWeather(), "climate": FakeClimate(), "choices": FakeChoices()})()
    c = make_client(providers=Providers(weather=fakes.weather, climate=fakes.climate, choices=fakes.choices))
    return c, fakes


def new_session(client) -> dict:
    r = client.post("/v1/session")
    assert r.status_code == 201, r.text
    return r.json()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authed(client):
    s = new_session(client)
    return client, auth(s["session_token"]), s
