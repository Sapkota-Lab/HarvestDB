from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead
from app.services.crop_service import CropService

router = APIRouter()
crop_service = CropService()


@router.post("/", response_model=HarvestRecordRead)
def create_harvest_record(payload: HarvestRecordCreate, harvest_event_id: int) -> HarvestRecordRead:
    return crop_service.create(payload, harvest_event_id)


@router.get("/", response_model=list[HarvestRecordRead])
def list_harvest_records(harvest_event_id: int | None = None) -> list[HarvestRecordRead]:
    return crop_service.list(harvest_event_id)


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
