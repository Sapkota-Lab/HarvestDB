from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.field import Field
from app.models.harvest_event import HarvestEvent
from app.schemas.field import FieldCreate
from app.schemas.harvest_event import HarvestEventCreate


def create_field(db: Session, payload: FieldCreate) -> Field:
    field = Field(**payload.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def list_fields(db: Session) -> list[Field]:
    return list(db.scalars(select(Field).order_by(Field.name, Field.id)))


def create_harvest(
    db: Session, payload: HarvestEventCreate, field_id: int
) -> HarvestEvent | None:
    if db.get(Field, field_id) is None:
        return None
    harvest = HarvestEvent(field_id=field_id, **payload.model_dump())
    db.add(harvest)
    db.commit()
    db.refresh(harvest)
    return harvest


def list_harvests(db: Session, field_id: int | None) -> list[HarvestEvent]:
    query = select(HarvestEvent)
    if field_id is not None:
        query = query.where(HarvestEvent.field_id == field_id)
    return list(db.scalars(query.order_by(HarvestEvent.harvest_date.desc(), HarvestEvent.id.desc())))
