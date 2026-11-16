"""`alembic upgrade head` must produce exactly the schema the models describe."""
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from lunaris_api.db.models import Base

ROOT = Path(__file__).resolve().parents[1]


def _cfg(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_upgrade_matches_models_and_seeds_cities(tmp_path):
    url = f"sqlite:///{tmp_path/'m.db'}"
    command.upgrade(_cfg(url), "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert diff == [], diff
        rows = conn.execute(text("select id, support_status from cities order by id")).all()
    assert [r for r in rows if r[1] == "supported"] == [("dubai", "supported")]
    assert set(inspect(engine).get_table_names()) >= {"cities", "users", "sessions", "preferences", "missions", "mission_interests", "audit_log", "impact_records"}


def test_downgrade_is_clean(tmp_path):
    url = f"sqlite:///{tmp_path/'d.db'}"
    command.upgrade(_cfg(url), "head")
    command.downgrade(_cfg(url), "base")
    assert set(inspect(create_engine(url)).get_table_names()) <= {"alembic_version"}
