"""Application factory. `create_app()` is import-safe: nothing runs until it is called."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import Settings
from .core.cache import TTLCache
from .core.clock import utcnow
from .core.ratelimit import SlidingWindowLimiter
from .core.redaction import configure_logging
from .core.scheduler import NullScheduler
from .db.models import Base
from .db.seed import seed_cities, seed_demo_missions
from .db.session import make_engine, make_session_factory
from .errors import install_error_handlers
from .integrations.ports import Providers
from .integrations.registry import load_providers
from .middleware import RequestContextMiddleware
from .routers import action_atlas, choices, cities, health, heatshield, impact, missions, places, preferences, session, weather
from .services.weather import WeatherService
from lunaris_climate.api import router as climate_ai_router

log = logging.getLogger("lunaris.app")

DESCRIPTION = (
    "LUNARIS platform API (v0). Dubai is the only supported city. Responses carry source status and evidence; "
    "nothing is fabricated: an unavailable or unintegrated source yields a structured 503 (or an empty, "
    "clearly-labelled list), never invented data. Guest sessions are not production identity."
)


def create_app(
    settings: Settings | None = None,
    providers: Providers | None = None,
    clock: Callable | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env(os.environ)
    configure_logging(settings.log_level)
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    providers = providers if providers is not None else load_providers(settings)
    clock = clock or utcnow

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auto_create_schema:
            Base.metadata.create_all(engine)  # dev/test convenience only; production uses Alembic
        with session_factory() as db:
            if settings.auto_create_schema:
                seed_cities(db)
            if settings.seed_demo_data:
                seed_demo_missions(db)
        log.info("startup complete", extra={"env": settings.env, "integrations": providers.status()})
        yield
        engine.dispose()

    app = FastAPI(
        title="LUNARIS v1 API",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    st = app.state
    st.settings = settings
    st.engine = engine
    st.session_factory = session_factory
    st.providers = providers
    st.clock = clock
    st.limiter = SlidingWindowLimiter()
    st.scheduler = NullScheduler()
    st.weather_service = WeatherService(providers.weather, settings, clock, TTLCache())

    # Order: last added runs first (outermost). Context middleware must wrap everything so even CORS rejections carry a request id.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=False,  # bearer tokens travel in the Authorization header, not cookies
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_request_bytes)
    install_error_handlers(app)

    for r in (health, cities, session, preferences, weather, heatshield, choices, places, missions, impact):
        app.include_router(r.router)
    # Additive ML service; existing HeatShield contract stays unchanged.
    app.include_router(climate_ai_router)
    app.include_router(action_atlas.router)
    return app
