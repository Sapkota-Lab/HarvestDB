from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.harvest_record import HarvestRecord
from app.models.record_image import RecordImage
from app.schemas.record_image import ImageCategory, RecordImageRead
from app.services.storage_service import detect_image_type, storage

router = APIRouter()


@router.post("/{record_id}/images", response_model=list[RecordImageRead], status_code=201)
async def upload_record_images(
    record_id: int,
    files: list[UploadFile] = File(...),
    category: ImageCategory = Form(ImageCategory.Other),
    caption: str | None = Form(None, max_length=512),
    db: Session = Depends(get_db),
) -> list[RecordImage]:
    if db.get(HarvestRecord, record_id) is None:
        raise HTTPException(status_code=404, detail="Harvest record not found")

    # Validate everything before writing so a bad file doesn't leave a partial upload.
    validated: list[tuple[UploadFile, bytes, str]] = []
    for upload in files:
        data = await upload.read(settings.max_image_bytes + 1)
        if len(data) > settings.max_image_bytes:
            raise HTTPException(status_code=413, detail=f"{upload.filename} exceeds the size limit")
        content_type = detect_image_type(data)
        if content_type is None:
            raise HTTPException(
                status_code=400, detail=f"{upload.filename} must be a JPEG, PNG or WebP image"
            )
        validated.append((upload, data, content_type))

    saved_keys: list[str] = []
    images: list[RecordImage] = []
    try:
        for upload, data, content_type in validated:
            key = storage.save(data, content_type)
            saved_keys.append(key)
            image = RecordImage(
                harvest_record_id=record_id,
                storage_key=key,
                original_filename=(upload.filename or "")[:255] or None,
                content_type=content_type,
                size_bytes=len(data),
                category=category.value,
                caption=caption,
            )
            db.add(image)
            images.append(image)
        db.commit()
    except Exception:
        db.rollback()
        for key in saved_keys:
            storage.delete(key)
        raise

    for image in images:
        db.refresh(image)
    return images


@router.get("/{record_id}/images", response_model=list[RecordImageRead])
def list_record_images(record_id: int, db: Session = Depends(get_db)) -> list[RecordImage]:
    if db.get(HarvestRecord, record_id) is None:
        raise HTTPException(status_code=404, detail="Harvest record not found")
    return list(
        db.scalars(
            select(RecordImage)
            .where(RecordImage.harvest_record_id == record_id)
            .order_by(RecordImage.id)
        )
    )


@router.get("/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)) -> FileResponse:
    image = db.get(RecordImage, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    path = storage.path(image.storage_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(path, media_type=image.content_type)


@router.delete("/images/{image_id}", status_code=204)
def delete_image(image_id: int, db: Session = Depends(get_db)) -> None:
    image = db.get(RecordImage, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    key = image.storage_key
    db.delete(image)
    db.commit()
    storage.delete(key)
