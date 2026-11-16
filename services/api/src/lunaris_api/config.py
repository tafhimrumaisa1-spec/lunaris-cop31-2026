"""Environment-driven settings. Stdlib only. All variables are prefixed LUNARIS_."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field, replace
from typing import Mapping

DEFAULT_DEV_DB = "sqlite:///./.data/lunaris_dev.db"


class ConfigError(ValueError):
    pass


def normalize_database_url(url: str) -> str:
    """Use the psycopg (v3) driver for bare postgres URLs."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    v = raw.strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"invalid boolean: {raw!r}")


def _int(raw: str | None, default: int, name: str, minimum: int = 1) -> int:
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if v < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    return v


@dataclass(frozen=True)
class Settings:
    env: str = "development"  # development | test | production
    database_url: str = DEFAULT_DEV_DB
    session_secret: str = ""
    session_ttl_days: int = 30
    cors_allow_origins: tuple[str, ...] = ("http://localhost:3000",)
    max_request_bytes: int = 65_536
    rate_limit_read_per_min: int = 120
    rate_limit_write_per_min: int = 30
    rate_limit_session_per_hour: int = 10
    trust_proxy_headers: bool = False
    weather_cache_ttl_seconds: int = 900
    weather_stale_max_seconds: int = 21_600
    auto_create_schema: bool = False
    seed_demo_data: bool = False
    docs_enabled: bool = True
    log_level: str = "INFO"
    # "module:attr" entrypoints supplied by the other agents' packages. Unset => not integrated.
    weather_provider: str | None = None
    climate_engine: str | None = None
    choices_engine: str | None = None
    places_provider: str | None = None
    business_evidence_provider: str | None = None
    # Email auth is NOT implemented: guest sessions only (see README "Authentication").
    auth_mode: str = field(default="guest_session")

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @classmethod
    def for_tests(cls, **overrides) -> "Settings":
        base = cls(
            env="test",
            database_url="sqlite://",
            session_secret="test-secret-" + "x" * 32,
            auto_create_schema=True,
            seed_demo_data=True,
            docs_enabled=True,
        )
        return replace(base, **overrides)

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> "Settings":
        g = lambda k: environ.get("LUNARIS_" + k)  # noqa: E731
        env = (g("ENV") or "development").lower()
        if env not in {"development", "test", "production"}:
            raise ConfigError("LUNARIS_ENV must be development, test or production")
        prod = env == "production"

        db = normalize_database_url(g("DATABASE_URL") or DEFAULT_DEV_DB)
        if prod and db.startswith("sqlite"):
            raise ConfigError("SQLite is a development fallback only; set LUNARIS_DATABASE_URL to PostgreSQL")

        secret = g("SESSION_SECRET") or ""
        if not secret:
            if prod:
                raise ConfigError("LUNARIS_SESSION_SECRET is required in production (>= 32 chars)")
            secret = secrets.token_urlsafe(32)  # ephemeral: dev sessions die on restart
        if prod and len(secret) < 32:
            raise ConfigError("LUNARIS_SESSION_SECRET must be at least 32 characters")

        origins = tuple(o.strip().rstrip("/") for o in (g("CORS_ALLOW_ORIGINS") or "http://localhost:3000").split(",") if o.strip())
        for o in origins:
            if o == "*" or not o.startswith(("http://", "https://")):
                raise ConfigError("LUNARIS_CORS_ALLOW_ORIGINS must be explicit http(s) origins; '*' is not allowed")
            if prod and o.startswith("http://") and "localhost" not in o:
                raise ConfigError("non-HTTPS CORS origin in production")

        auth = (g("AUTH_MODE") or "guest_session").lower()
        if auth != "guest_session":
            raise ConfigError("Only LUNARIS_AUTH_MODE=guest_session is implemented (no email-auth provider credentials/integration)")

        return cls(
            env=env,
            database_url=db,
            session_secret=secret,
            session_ttl_days=_int(g("SESSION_TTL_DAYS"), 30, "LUNARIS_SESSION_TTL_DAYS"),
            cors_allow_origins=origins,
            max_request_bytes=_int(g("MAX_REQUEST_BYTES"), 65_536, "LUNARIS_MAX_REQUEST_BYTES", 1024),
            rate_limit_read_per_min=_int(g("RATE_LIMIT_READ_PER_MIN"), 120, "LUNARIS_RATE_LIMIT_READ_PER_MIN"),
            rate_limit_write_per_min=_int(g("RATE_LIMIT_WRITE_PER_MIN"), 30, "LUNARIS_RATE_LIMIT_WRITE_PER_MIN"),
            rate_limit_session_per_hour=_int(g("RATE_LIMIT_SESSION_PER_HOUR"), 10, "LUNARIS_RATE_LIMIT_SESSION_PER_HOUR"),
            trust_proxy_headers=_bool(g("TRUST_PROXY_HEADERS"), False),
            weather_cache_ttl_seconds=_int(g("WEATHER_CACHE_TTL_SECONDS"), 900, "LUNARIS_WEATHER_CACHE_TTL_SECONDS", 0),
            weather_stale_max_seconds=_int(g("WEATHER_STALE_MAX_SECONDS"), 21_600, "LUNARIS_WEATHER_STALE_MAX_SECONDS", 0),
            auto_create_schema=_bool(g("AUTO_CREATE_SCHEMA"), not prod and env != "test"),
            seed_demo_data=_bool(g("SEED_DEMO_DATA"), False),
            docs_enabled=_bool(g("DOCS_ENABLED"), not prod),
            log_level=(g("LOG_LEVEL") or "INFO").upper(),
            weather_provider=g("WEATHER_PROVIDER") or None,
            climate_engine=g("CLIMATE_ENGINE") or None,
            choices_engine=g("CHOICES_ENGINE") or None,
            places_provider=g("PLACES_PROVIDER") or None,
            business_evidence_provider=g("BUSINESS_EVIDENCE_PROVIDER") or None,
            auth_mode=auth,
        )
