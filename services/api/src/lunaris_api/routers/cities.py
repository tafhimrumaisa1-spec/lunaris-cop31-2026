from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from ..db.models import CityRow
from ..deps import get_db, rate_limit
from ..schemas import City, CityList

router = APIRouter(prefix="/v1", tags=["cities"], dependencies=[Depends(rate_limit("read"))])


@router.get("/cities", response_model=CityList, summary="Supported city registry")
def list_cities(db: Session = Depends(get_db)) -> CityList:
    """Only `supported` cities have weather, model, venue and licensing coverage. Dubai is the only one at v0."""
    order = case((CityRow.support_status == "supported", 0), (CityRow.support_status == "preview", 1), else_=2)
    rows = db.scalars(select(CityRow).order_by(order, CityRow.name)).all()
    return CityList(cities=[City.model_validate(r) for r in rows])
