from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..core.ids import new_id
from ..db.models import AuditLogRow, MissionInterestRow, MissionRow
from ..deps import AuthContext, get_db, now, rate_limit, require_auth
from ..schemas import CommunityMission, MissionInterestRequest, MissionInterestStored, MissionList, SourceStatus

router = APIRouter(prefix="/v1", tags=["missions"])
MissionId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


@router.get("/missions", response_model=MissionList, summary="Dubai missions with explicit demo/approval status",
            dependencies=[Depends(rate_limit("read"))])
def list_missions(request: Request, db: Session = Depends(get_db)) -> MissionList:
    rows = db.scalars(select(MissionRow).order_by(MissionRow.id)).all()
    only_demo = bool(rows) and all(r.status == "demo" for r in rows)
    status = SourceStatus(
        state="demo" if only_demo else "available",
        detail="All listed missions are demonstrations; none is a real event." if only_demo else
        ("No missions exist yet." if not rows else None),
        checked_at=request.app.state.clock(),
    )
    return MissionList(missions=[CommunityMission.model_validate(r) for r in rows], source_status=status)


@router.post("/missions/{id}/interest", response_model=MissionInterestStored, status_code=201,
             summary="Express interest (consented, abuse-limited). This is NOT a registration.",
             dependencies=[Depends(rate_limit("write"))],
             responses={404: {"description": "Unknown mission"}, 409: {"description": "Duplicate or mission not accepting interest"}})
def express_interest(id: MissionId, body: MissionInterestRequest, request: Request,
                     auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)) -> MissionInterestStored:
    if not body.consent:
        raise AppError(422, "consent_required", "Interest is only recorded with explicit consent (consent: true).")
    mission = db.get(MissionRow, id)
    if mission is None:
        raise AppError(404, "not_found", "Unknown mission.")
    accepting = mission.status == "demo" or (mission.status in {"approved", "active"} and mission.permission_status == "approved")
    if not accepting:
        raise AppError(409, "mission_not_accepting_interest",
                       "This mission is not approved to accept interest yet (needs approved status and permission).")
    t = now(request)
    interest = MissionInterestRow(id=new_id("int"), mission_id=id, user_id=auth.user_id, consent_at=t, created_at=t)
    db.add(interest)
    db.add(AuditLogRow(id=new_id("aud"), occurred_at=t, actor_user_id=auth.user_id, action="mission_interest.created",
                       subject_type="mission", subject_id=id, detail={"mission_status": mission.status, "consent": True}))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "already_expressed_interest", "Interest has already been recorded for this mission.") from exc
    notice = ("DEMO mission: this is not a real event and no organizer has been notified." if mission.status == "demo"
              else "Interest recorded. This is not a registration; the organizer has not confirmed your place.")
    return MissionInterestStored(interest_id=interest.id, mission_id=id, mission_status=mission.status, created_at=t, notice=notice)
