"""Idempotent seeding. City registry always; demo mission only when explicitly enabled."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..cities_data import CITIES
from .models import CityRow, MissionRow

DEMO_MISSION_ID = "mission_demo_shade_survey"


def seed_cities(db: Session) -> None:
    for c in CITIES:
        db.merge(CityRow(**c))
    db.commit()


def seed_demo_missions(db: Session) -> None:
    """One explicitly-DEMO mission for exercising interest capture (PRODUCT_BRIEF.md journey 11).
    It names no real organizer, venue, address, permit, date or volunteer count because none exist."""
    if db.get(MissionRow, DEMO_MISSION_ID) is None:
        db.add(MissionRow(
            id=DEMO_MISSION_ID,
            title="DEMO: Community shade survey (not a real event)",
            summary=("Demonstration mission used to test interest capture. No event, organizer, permit, "
                     "location, date or volunteer count exists. Expressing interest does not register you for anything."),
            city_id="dubai",
            status="demo",
            permission_status="unknown",
            verification_status="unverified",
            organizer_id=None,
        ))
        db.commit()
