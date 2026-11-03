from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.field import FieldCreate, FieldRead
from app.services import field_service

router = APIRouter()


@router.post("/", response_model=FieldRead)
def create_field(payload: FieldCreate, db: Session = Depends(get_db)) -> FieldRead:
    try:
        return FieldRead.model_validate(field_service.create_field(db, payload))
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A field with this name already exists.") from error


@router.get("/", response_model=list[FieldRead])
def list_fields(db: Session = Depends(get_db)) -> list[FieldRead]:
    return [FieldRead.model_validate(field) for field in field_service.list_fields(db)]
