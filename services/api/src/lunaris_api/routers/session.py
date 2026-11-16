"""Guest sessions. NOT production identity: no email, name, password or provider is involved."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from ..core.ids import new_id
from ..core.tokens import hash_token, new_token
from ..db.models import AuditLogRow, ImpactRecordRow, MissionInterestRow, PreferencesRow, SessionRow, UserRow
from ..deps import AuthContext, get_db, get_settings, now, rate_limit, require_auth
from ..schemas import SessionCreated, SessionInfo
from ..config import Settings

router = APIRouter(prefix="/v1", tags=["session"])

NOTICE = ("Guest session: a pseudonymous, device-bound token. It is not a verified identity and "
          "must not be used as production authentication. Email sign-in is not implemented.")


@router.post("/session", response_model=SessionCreated, status_code=201, summary="Create a guest session",
             dependencies=[Depends(rate_limit("session"))])
def create_session(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> SessionCreated:
    t = now(request)
    user = UserRow(id=new_id("usr"), auth_mode=settings.auth_mode, created_at=t)
    token = new_token()
    expires = t + timedelta(days=settings.session_ttl_days)
    db.add(user)
    db.flush()
    db.add(SessionRow(id=new_id("ses"), user_id=user.id, token_hash=hash_token(settings.session_secret, token), created_at=t, expires_at=expires))
    db.commit()
    return SessionCreated(session_token=token, expires_at=expires, user_id=user.id, auth_mode=settings.auth_mode, notice=NOTICE)


@router.get("/session", response_model=SessionInfo, summary="Inspect the current session",
            dependencies=[Depends(rate_limit("read"))])
def get_session(auth: AuthContext = Depends(require_auth), settings: Settings = Depends(get_settings)) -> SessionInfo:
    return SessionInfo(user_id=auth.user_id, auth_mode=settings.auth_mode, expires_at=auth.expires_at, notice=NOTICE)


@router.delete("/session", status_code=204, summary="Revoke the current session (sign out)",
               dependencies=[Depends(rate_limit("write"))])
def revoke_session(request: Request, auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)) -> Response:
    db.execute(update(SessionRow).where(SessionRow.id == auth.session_id).values(revoked_at=now(request)))
    db.commit()
    return Response(status_code=204)


@router.delete("/me", status_code=204, summary="Erase this user and all their data",
               dependencies=[Depends(rate_limit("write"))])
def erase_me(request: Request, auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)) -> Response:
    """Deletes user, sessions, preferences, interests and impact records. Audit rows are kept but de-linked."""
    uid = auth.user_id
    db.execute(update(AuditLogRow).where(AuditLogRow.actor_user_id == uid).values(actor_user_id=None))
    # Explicit deletes (do not rely on FK cascade being enabled on every backend).
    for model in (ImpactRecordRow, MissionInterestRow, PreferencesRow, SessionRow):
        db.execute(delete(model).where(model.user_id == uid))
    db.execute(delete(UserRow).where(UserRow.id == uid))
    db.add(AuditLogRow(id=new_id("aud"), occurred_at=now(request), actor_user_id=None, action="user.erased", subject_type="user", subject_id="redacted", detail={}))
    db.commit()
    return Response(status_code=204)
