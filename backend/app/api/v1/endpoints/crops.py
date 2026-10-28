import json
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.harvest_event import HarvestEvent
from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead, HarvestRecordUpdate, HarvestUploadRead
from app.schemas.harvest_record_filter import HarvestRecordFilter
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


@router.get("/", response_model=dict)
def list_harvest_records(
    harvest_event_id: int | None = None,
    field_id: int | None = None,
    plot_number: str | None = None,
    harvest_date_from: date | None = None,
    harvest_date_to: date | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    filters = HarvestRecordFilter(
        harvest_event_id=harvest_event_id,
        field_id=field_id,
        plot_number=plot_number,
        harvest_date_from=harvest_date_from,
        harvest_date_to=harvest_date_to,
        page=page,
        page_size=page_size,
    )

    records, total = crop_service.list_records(db, filters)
    total_pages = (total + page_size - 1) // page_size

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.patch("/{record_id}", response_model=HarvestRecordRead, status_code=200)
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


@router.post("/upload", response_model=HarvestUploadRead)
async def upload_harvest_records(
    harvest_event_id: int | None = None,
    file: UploadFile = File(...),
    sheet_event_ids: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> HarvestUploadRead:
    filename = (file.filename or "").lower()
    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv or .xlsx file")

    raw = await file.read()
    try:
        if filename.endswith(".xlsx"):
            if sheet_event_ids is None:
                raise ValueError("Choose an event or skip each worksheet")
            try:
                parsed_event_ids = json.loads(sheet_event_ids)
            except json.JSONDecodeError as exc:
                raise ValueError("Worksheet event mappings must be valid JSON") from exc
            if not isinstance(parsed_event_ids, dict) or any(
                not isinstance(name, str)
                or (
                    event_id is not None
                    and (
                        isinstance(event_id, bool)
                        or not isinstance(event_id, int)
                        or event_id < 1
                    )
                )
                for name, event_id in parsed_event_ids.items()
            ):
                raise ValueError("Worksheet event mappings must contain valid event IDs or null")
            for event_id in parsed_event_ids.values():
                if event_id is not None and db.get(HarvestEvent, event_id) is None:
                    raise HTTPException(status_code=404, detail="Harvest event not found")
            return crop_service.import_xlsx(db, raw, parsed_event_ids)
        if harvest_event_id is None:
            raise HTTPException(status_code=400, detail="Harvest event ID is required for CSV uploads")
        if db.get(HarvestEvent, harvest_event_id) is None:
            raise HTTPException(status_code=404, detail="Harvest event not found")
        csv_text = raw.decode("utf-8-sig")
        return HarvestUploadRead(records=crop_service.import_csv(db, csv_text, harvest_event_id))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upload/worksheets", response_model=list[str])
async def list_upload_worksheets(
    file: UploadFile = File(...),
) -> list[str]:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .xlsx file")

    try:
        return crop_service.list_xlsx_worksheets(await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
