from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import __version__
from ..deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health")
def health(request: Request, db: Session = Depends(get_db)):
    st = request.app.state
    try:
        db.execute(text("SELECT 1"))
        db_state = "available"
    except Exception:  # noqa: BLE001
        db_state = "unavailable"
    body = {
        "status": "ok" if db_state == "available" else "degraded",
        "service": "lunaris-api",
        "version": __version__,
        "environment": st.settings.env,
        "time_utc": st.clock().isoformat(),
        "database": {"state": db_state, "dialect": "sqlite" if st.settings.is_sqlite else "postgresql"},
        # Provider status is informational: an unbound provider does not make the API unhealthy.
        "integrations": st.providers.status(),
        "auth_mode": st.settings.auth_mode,
        "scheduler": {"backend": "none", "jobs": st.scheduler.jobs()},
    }
    return JSONResponse(body, status_code=200 if db_state == "available" else 503)
