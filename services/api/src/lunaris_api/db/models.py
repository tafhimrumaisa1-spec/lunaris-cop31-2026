"""SQLAlchemy 2.0 models. Keep in sync with alembic/versions/*; tests/test_migrations.py enforces it."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .types import UTCDateTime


class Base(DeclarativeBase):
    pass


class CityRow(Base):
    __tablename__ = "cities"
    __table_args__ = (CheckConstraint("support_status in ('supported','preview','unsupported')", name="ck_cities_support_status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    country_code: Mapped[str] = mapped_column(String(2))
    timezone: Mapped[str] = mapped_column(String(64))
    support_status: Mapped[str] = mapped_column(String(16))
    center_lat: Mapped[float] = mapped_column(Float)
    center_lon: Mapped[float] = mapped_column(Float)


class UserRow(Base):
    """Pseudonymous user. Guest sessions only: no email, name or profile data is stored."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    auth_mode: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)  # HMAC-SHA256 hex; never the token
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class PreferencesRow(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"))
    weather_moods: Mapped[list[str]] = mapped_column(JSON)
    comfort_min_c: Mapped[float] = mapped_column(Float)
    comfort_max_c: Mapped[float] = mapped_column(Float)
    activities: Mapped[list[str]] = mapped_column(JSON)
    priorities: Mapped[list[str]] = mapped_column(JSON)
    notification_consent: Mapped[bool] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)


class MissionRow(Base):
    __tablename__ = "missions"
    __table_args__ = (
        CheckConstraint("status in ('demo','proposed','reviewing','approved','active','complete')", name="ck_missions_status"),
        CheckConstraint("permission_status in ('unknown','pending','approved')", name="ck_missions_permission"),
        CheckConstraint("verification_status in ('unverified','self_reported','reviewed','verified')", name="ck_missions_verification"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"))
    status: Mapped[str] = mapped_column(String(16))
    permission_status: Mapped[str] = mapped_column(String(16))
    verification_status: Mapped[str] = mapped_column(String(16))
    organizer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MissionInterestRow(Base):
    __tablename__ = "mission_interests"
    __table_args__ = (UniqueConstraint("mission_id", "user_id", name="uq_interest_mission_user"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    consent_at: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class AuditLogRow(Base):
    """Append-only audit trail. actor_user_id has no FK so rows survive erasure (then nulled)."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_subject", "subject_type", "subject_id"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    actor_user_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    subject_type: Mapped[str] = mapped_column(String(32))
    subject_id: Mapped[str] = mapped_column(String(64))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON)


class ImpactRecordRow(Base):
    __tablename__ = "impact_records"
    __table_args__ = (CheckConstraint("verification_status in ('self_reported','reviewed','verified')", name="ck_impact_verification"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(String(16))
    impact_estimate: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
