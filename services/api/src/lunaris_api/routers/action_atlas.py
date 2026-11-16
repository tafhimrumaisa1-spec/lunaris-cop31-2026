from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..action_atlas.catalog import all_areas
from ..action_atlas.evidence import read_indicators
from ..action_atlas.scenario import estimate, ScenarioError, DEFAULTS

router = APIRouter(prefix='/v1/action/atlas', tags=['city-opportunities'])

class ScenarioIn(BaseModel):
    quantity: float = Field(ge=0, le=100000)
    unit_benefit: float | None = Field(default=None, ge=0, le=1e8)
    unit_cost: float | None = Field(default=None, ge=0, le=1e8)
    adoption: float | None = Field(default=None, ge=0, le=1)

@router.get('')
def list_atlas():
    return {'city':'Dubai, UAE', 'area_precision':'approximate neighborhood centroids only',
            'data_status':'curated conceptual pilot; no live satellite classification or site survey',
            'opportunities':all_areas(), 'scenario_defaults':DEFAULTS}

@router.get('/evidence', summary='Reviewed area-level satellite indicators, if supplied')
def atlas_evidence():
    """Never return made-up indicator values: an absent export is a labeled empty result."""
    return read_indicators()

@router.post('/{area_id}/scenario')
def calculate_scenario(area_id: str, request: ScenarioIn):
    area = next((a for a in all_areas() if a['id'] == area_id), None)
    if not area:
        raise HTTPException(404, 'Unknown opportunity area')
    try:
        result = estimate(area['category'], request.quantity, request.unit_benefit, request.unit_cost, request.adoption)
    except ScenarioError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {'area_id':area_id, 'area_name':area['name'], **result}

# Optional, consent-based interest ledger for concept proposals. No enrollment or organizer notification.
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..deps import get_db, require_auth, AuthContext, now
from ..db.models import MissionRow, MissionInterestRow, AuditLogRow
from ..core.ids import new_id

class InterestIn(BaseModel):
    consent: bool

@router.post('/{area_id}/interest', status_code=201)
def express_atlas_interest(area_id: str, body: InterestIn, request: Request,
                           auth: AuthContext = Depends(require_auth), db: Session = Depends(get_db)):
    area = next((a for a in all_areas() if a['id'] == area_id), None)
    if area is None:
        raise HTTPException(404, 'Unknown opportunity area')
    if not body.consent:
        raise HTTPException(422, 'Explicit consent is required')
    mission_id = 'atlas_' + area_id.replace('-', '_')
    mission = db.get(MissionRow, mission_id)
    if mission is None:
        mission = MissionRow(id=mission_id, title='CONCEPT: ' + area['title'],
                             summary='Area-level hypothetical opportunity. No real mission, organizer, permit or volunteer slot.',
                             city_id='dubai', status='demo', permission_status='unknown',
                             verification_status='unverified', organizer_id=None)
        db.add(mission)
        db.flush()
    t = now(request)
    record = MissionInterestRow(id=new_id('int'), mission_id=mission_id, user_id=auth.user_id, consent_at=t, created_at=t)
    db.add(record)
    db.add(AuditLogRow(id=new_id('aud'), occurred_at=t, actor_user_id=auth.user_id,
                       action='atlas.interest_created', subject_type='mission', subject_id=mission_id,
                       detail={'type':'concept_only','consent':True}))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, 'Interest already recorded for this concept') from exc
    return {'area_id':area_id, 'interest_id':record.id, 'status':'concept_interest_only',
            'notice':'Interest recorded in your guest account. No actual event exists; no organizer has been notified or place reserved.'}
