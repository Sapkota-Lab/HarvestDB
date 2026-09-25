import csv
import io

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.harvest_event import HarvestEvent
from app.models.harvest_record import HarvestRecord
from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead, HarvestRecordUpdate


class CropService:
    def create(
        self, db: Session, payload: HarvestRecordCreate, harvest_event_id: int
    ) -> HarvestRecordRead | None:
        if db.get(HarvestEvent, harvest_event_id) is None:
            return None

        record = HarvestRecord(
            harvest_event_id=harvest_event_id,
            plot_number=payload.plot_number,
            dynamic_data=payload.dynamic_data,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _to_read(record)

    def update(
        self, db: Session, record_id: int, payload: HarvestRecordUpdate
    ) -> HarvestRecordRead | None:
        record = db.get(HarvestRecord, record_id)
        if record is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        if "plot_number" in updates:
            record.plot_number = updates["plot_number"]
        if "dynamic_data" in updates:
            record.dynamic_data = updates["dynamic_data"]

        db.commit()
        db.refresh(record)
        return _to_read(record)

    def delete(self, db: Session, record_id: int) -> bool:
        record = db.get(HarvestRecord, record_id)
        if record is None:
            return False

        db.delete(record)
        db.commit()
        return True

    def import_csv(self, csv_text: str, harvest_event_id: int) -> list[HarvestRecordRead]:
        reader = csv.DictReader(io.StringIO(csv_text))
        records: list[HarvestRecordRead] = []

        for line_number, row in enumerate(reader, start=2):
            try:
                payload = HarvestRecordCreate(**_clean_row(row))
            except ValidationError as exc:
                raise ValueError(f"Row {line_number}: {exc}") from exc

            print(f"[CSV import] harvest_event_id={harvest_event_id} row={line_number} {payload.model_dump()}")
            records.append(
                HarvestRecordRead(id=len(records) + 1, harvest_event_id=harvest_event_id, **payload.model_dump())
            )

        return records

    def list(self, db: Session, harvest_event_id: int | None = None) -> list[HarvestRecordRead]:
        stmt = select(HarvestRecord)
        if harvest_event_id is not None:
            stmt = stmt.where(HarvestRecord.harvest_event_id == harvest_event_id)
        return [_to_read(record) for record in db.scalars(stmt).all()]


def _to_read(record: HarvestRecord) -> HarvestRecordRead:
    return HarvestRecordRead(
        id=record.id,
        harvest_event_id=record.harvest_event_id,
        plot_number=record.plot_number,
        dynamic_data=record.dynamic_data or {},
        created_at=record.created_at,
    )


def _clean_row(row: dict) -> dict:
    cleaned = {}
    for key, value in row.items():
        if key is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        cleaned[key] = value or None
    return cleaned
