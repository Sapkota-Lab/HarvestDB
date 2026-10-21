from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.harvest_event import HarvestEventCreate, HarvestEventRead
from app.services import field_service

router = APIRouter()


@router.post("/", response_model=HarvestEventRead)
def create_harvest(
    payload: HarvestEventCreate,
    field_id: int = Query(gt=0),
    db: Session = Depends(get_db),
) -> HarvestEventRead:
    harvest = field_service.create_harvest(db, payload, field_id)
    if harvest is None:
        raise HTTPException(status_code=404, detail="Field not found.")
    return HarvestEventRead.model_validate(harvest)


@router.get("/", response_model=list[HarvestEventRead])
def list_harvests(
    field_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> list[HarvestEventRead]:
    return [HarvestEventRead.model_validate(harvest) for harvest in field_service.list_harvests(db, field_id)]
