"""Local mirror of city coverage used ONLY to gate this package's outputs.
Agent 05 owns the authoritative /v1/cities registry; keep these in sync (documented in the handoff)."""
from __future__ import annotations

SUPPORTED_CITIES = {"dubai": {"name": "Dubai", "country_code": "AE", "timezone": "Asia/Dubai", "support_status": "supported"}}


def city_status(city_id: str) -> str:
    if not isinstance(city_id, str):
        return "unsupported"
    c = SUPPORTED_CITIES.get(city_id.strip().lower())
    return c["support_status"] if c else "unsupported"
