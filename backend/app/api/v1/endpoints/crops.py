from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead, HarvestRecordUpdate
from app.services.crop_service import CropService

router = APIRouter()
crop_service = CropService()


@router.post("/", response_model=HarvestRecordRead)
def create_harvest_record(
    payload: HarvestRecordCreate,
    harvest_event_id: int,
    db: Session = Depends(get_db),
) -> HarvestRecordRead:
    record = crop_service.create(db, payload, harvest_event_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Harvest event not found")
    return record


@router.get("/", response_model=list[HarvestRecordRead])
def list_harvest_records(
    harvest_event_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[HarvestRecordRead]:
    return crop_service.list(db, harvest_event_id)


@router.patch("/{record_id}", response_model=HarvestRecordRead)
def update_harvest_record(
    record_id: int,
    payload: HarvestRecordUpdate,
    db: Session = Depends(get_db),
) -> HarvestRecordRead:
    if not payload.model_dump(exclude_unset=True):
        raise HTTPException(status_code=400, detail="No fields to update")

    record = crop_service.update(db, record_id, payload)
    if record is None:
        raise HTTPException(status_code=404, detail="Harvest record not found")
    return record


@router.delete("/{record_id}", status_code=204)
def delete_harvest_record(record_id: int, db: Session = Depends(get_db)) -> None:
    deleted = crop_service.delete(db, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Harvest record not found")


@router.post("/upload", response_model=list[HarvestRecordRead])
async def upload_harvest_records(harvest_event_id: int, file: UploadFile = File(...)) -> list[HarvestRecordRead]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file")

    raw = await file.read()
    try:
        csv_text = raw.decode("utf-8-sig")  # strips the BOM Excel adds when it saves a CSV
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Uploaded file must be UTF-8 encoded") from exc

    try:
        return crop_service.import_csv(csv_text, harvest_event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
