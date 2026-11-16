"""Shared FastAPI dependencies: db session, guest-session auth, rate limiting."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .core.errors import AppError
from .core.tokens import hash_token
from .db.models import SessionRow

bearer_scheme = HTTPBearer(auto_error=False, description="Opaque guest-session token from POST /v1/session")


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    session_id: str
    expires_at: datetime


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def now(request: Request) -> datetime:
    return request.app.state.clock()


def client_ip(request: Request) -> str:
    s: Settings = request.app.state.settings
    if s.trust_proxy_headers:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[-1].strip()  # entry appended by our own trusted proxy
    return request.client.host if request.client else "unknown"


def optional_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthContext | None:
    """None when no credentials are sent. A presented-but-invalid token is a 401, never silent guest."""
    if creds is None:
        return None
    token = creds.credentials
    invalid = AppError(401, "invalid_session", "Session is missing, expired or revoked.", headers={"WWW-Authenticate": "Bearer"})
    if not (16 <= len(token) <= 256):
        raise invalid
    row = db.scalar(select(SessionRow).where(SessionRow.token_hash == hash_token(request.app.state.settings.session_secret, token)))
    if row is None or row.revoked_at is not None or row.expires_at <= now(request):
        raise invalid
    return AuthContext(user_id=row.user_id, session_id=row.id, expires_at=row.expires_at)


def require_auth(auth: AuthContext | None = Depends(optional_auth)) -> AuthContext:
    if auth is None:
        raise AppError(401, "session_required", "This action needs a session. Create a guest session with POST /v1/session.",
                       headers={"WWW-Authenticate": "Bearer"})
    return auth


def rate_limit(group: str):
    """group in {read, write, session}"""

    def dep(request: Request) -> None:
        st = request.app.state
        s: Settings = st.settings
        limit, window = {
            "read": (s.rate_limit_read_per_min, 60),
            "write": (s.rate_limit_write_per_min, 60),
            "session": (s.rate_limit_session_per_hour, 3600),
        }[group]
        ok, retry = st.limiter.check(f"{group}:{client_ip(request)}", limit, window)
        if not ok:
            raise AppError(429, "rate_limited", "Too many requests. Please slow down.", headers={"Retry-After": str(retry)})

    return dep
