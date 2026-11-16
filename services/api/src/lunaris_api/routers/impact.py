from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ImpactRecordRow
from ..deps import AuthContext, get_db, rate_limit, require_auth
from ..schemas import ImpactList, ImpactRecord

router = APIRouter(prefix="/v1", tags=["impact"])

NOTICE = ("Verification status is reported separately from estimates. Impact units are never combined into a single score. "
          "Nothing here is verified unless a reviewer has recorded it.")


@router.get("/impact", response_model=ImpactList, summary="Personal log; verification separate from estimates",
            dependencies=[Depends(rate_limit("read"))])
def impact(auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)) -> ImpactList:
    rows = db.scalars(select(ImpactRecordRow).where(ImpactRecordRow.user_id == auth.user_id).order_by(ImpactRecordRow.created_at.desc())).all()
    counts = Counter(r.verification_status for r in rows)
    return ImpactList(
        records=[ImpactRecord.model_validate(r) for r in rows],
        verification_counts={k: counts.get(k, 0) for k in ("self_reported", "reviewed", "verified")},
        notice=NOTICE,
    )
