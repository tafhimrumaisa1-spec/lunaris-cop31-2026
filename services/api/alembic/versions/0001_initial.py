"""initial schema + city registry

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Literal copy (migrations must not change when lunaris_api.cities_data changes).
_CITIES = [
    {"id": "dubai", "name": "Dubai", "country_code": "AE", "timezone": "Asia/Dubai", "support_status": "supported", "center_lat": 25.2048, "center_lon": 55.2708},
    {"id": "abu-dhabi", "name": "Abu Dhabi", "country_code": "AE", "timezone": "Asia/Dubai", "support_status": "unsupported", "center_lat": 24.4539, "center_lon": 54.3773},
    {"id": "london", "name": "London", "country_code": "GB", "timezone": "Europe/London", "support_status": "unsupported", "center_lat": 51.5074, "center_lon": -0.1278},
    {"id": "new-york", "name": "New York", "country_code": "US", "timezone": "America/New_York", "support_status": "unsupported", "center_lat": 40.7128, "center_lon": -74.0060},
    {"id": "singapore", "name": "Singapore", "country_code": "SG", "timezone": "Asia/Singapore", "support_status": "unsupported", "center_lat": 1.3521, "center_lon": 103.8198},
]


def _utc():
    from lunaris_api.db.types import UTCDateTime
    return UTCDateTime()


def upgrade() -> None:
    cities = op.create_table(
        "cities",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("support_status", sa.String(16), nullable=False),
        sa.Column("center_lat", sa.Float, nullable=False),
        sa.Column("center_lon", sa.Float, nullable=False),
        sa.CheckConstraint("support_status in ('supported','preview','unsupported')", name="ck_cities_support_status"),
    )
    op.bulk_insert(cities, _CITIES)

    op.create_table(
        "users",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("auth_mode", sa.String(32), nullable=False),
        sa.Column("created_at", _utc(), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", _utc(), nullable=False),
        sa.Column("expires_at", _utc(), nullable=False),
        sa.Column("revoked_at", _utc(), nullable=True),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_table(
        "preferences",
        sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("city_id", sa.String(64), sa.ForeignKey("cities.id"), nullable=False),
        sa.Column("weather_moods", sa.JSON, nullable=False),
        sa.Column("comfort_min_c", sa.Float, nullable=False),
        sa.Column("comfort_max_c", sa.Float, nullable=False),
        sa.Column("activities", sa.JSON, nullable=False),
        sa.Column("priorities", sa.JSON, nullable=False),
        sa.Column("notification_consent", sa.Boolean, nullable=False),
        sa.Column("updated_at", _utc(), nullable=False),
    )
    op.create_table(
        "missions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("city_id", sa.String(64), sa.ForeignKey("cities.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("permission_status", sa.String(16), nullable=False),
        sa.Column("verification_status", sa.String(16), nullable=False),
        sa.Column("organizer_id", sa.String(64), nullable=True),
        sa.CheckConstraint("status in ('demo','proposed','reviewing','approved','active','complete')", name="ck_missions_status"),
        sa.CheckConstraint("permission_status in ('unknown','pending','approved')", name="ck_missions_permission"),
        sa.CheckConstraint("verification_status in ('unverified','self_reported','reviewed','verified')", name="ck_missions_verification"),
    )
    op.create_table(
        "mission_interests",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("mission_id", sa.String(64), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_at", _utc(), nullable=False),
        sa.Column("created_at", _utc(), nullable=False),
        sa.UniqueConstraint("mission_id", "user_id", name="uq_interest_mission_user"),
    )
    op.create_index("ix_mission_interests_mission_id", "mission_interests", ["mission_id"])
    op.create_index("ix_mission_interests_user_id", "mission_interests", ["user_id"])
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("occurred_at", _utc(), nullable=False),
        sa.Column("actor_user_id", sa.String(40), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("subject_type", sa.String(32), nullable=False),
        sa.Column("subject_id", sa.String(64), nullable=False),
        sa.Column("detail", sa.JSON, nullable=False),
    )
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"])
    op.create_index("ix_audit_subject", "audit_log", ["subject_type", "subject_id"])
    op.create_table(
        "impact_records",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("user_id", sa.String(40), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("verification_status", sa.String(16), nullable=False),
        sa.Column("impact_estimate", sa.JSON, nullable=True),
        sa.Column("evidence", sa.JSON, nullable=False),
        sa.Column("created_at", _utc(), nullable=False),
        sa.CheckConstraint("verification_status in ('self_reported','reviewed','verified')", name="ck_impact_verification"),
    )
    op.create_index("ix_impact_records_user_id", "impact_records", ["user_id"])


def downgrade() -> None:
    for t in ("impact_records", "audit_log", "mission_interests", "missions", "preferences", "sessions", "users", "cities"):
        op.drop_table(t)
