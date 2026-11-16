import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from lunaris_api.config import DEFAULT_DEV_DB, normalize_database_url
from lunaris_api.db.models import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # Tests may pre-set sqlalchemy.url on the Config; otherwise use the environment.
    return config.get_main_option("sqlalchemy.url") or normalize_database_url(os.environ.get("LUNARIS_DATABASE_URL") or DEFAULT_DEV_DB)


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=_url().startswith("sqlite"))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = _url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=connection.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
