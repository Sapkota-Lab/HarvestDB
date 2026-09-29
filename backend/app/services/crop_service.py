import csv
import io
import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.field import Field
from app.models.harvest_event import HarvestEvent
from app.models.harvest_record import HarvestRecord
from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordQueryRead, HarvestRecordRead, HarvestRecordUpdate
from app.schemas.harvest_record_filter import HarvestRecordFilter


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

    def import_csv(self, db: Session, csv_text: str, harvest_event_id: int) -> list[HarvestRecordRead]:
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            raise ValueError("CSV file must include a header row")

        required_columns = {"plot_number"}
        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            missing_column_names = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required column: {missing_column_names}")

        records: list[HarvestRecord] = []

        for line_number, row in enumerate(reader, start=2):
            try:
                data = _clean_row(row)
                dynamic_data = data.get("dynamic_data")
                if dynamic_data is None:
                    data.pop("dynamic_data", None)
                else:
                    data["dynamic_data"] = json.loads(dynamic_data)
                payload = HarvestRecordCreate(**data)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Row {line_number}: dynamic_data must be valid JSON") from exc
            except ValidationError as exc:
                raise ValueError(f"Row {line_number}: {exc}") from exc

            records.append(
                HarvestRecord(
                    harvest_event_id=harvest_event_id,
                    plot_number=payload.plot_number,
                    dynamic_data=payload.dynamic_data,
                )
            )

        db.add_all(records)
        db.commit()
        return [_to_read(record) for record in records]

    def list_records(
        self, db: Session, filters: HarvestRecordFilter
    ) -> tuple[list[HarvestRecordQueryRead], int]:
        query = (
            db.query(HarvestRecord, HarvestEvent.harvest_date, Field.name.label("field_name"))
            .select_from(HarvestRecord)
            .join(HarvestEvent, HarvestRecord.harvest_event_id == HarvestEvent.id)
            .join(Field, HarvestEvent.field_id == Field.id)
        )

        if filters.harvest_event_id is not None:
            query = query.filter(HarvestRecord.harvest_event_id == filters.harvest_event_id)
        if filters.field_id is not None:
            query = query.filter(HarvestEvent.field_id == filters.field_id)
        if filters.plot_number is not None:
            query = query.filter(HarvestRecord.plot_number.ilike(f"%{filters.plot_number}%"))
        if filters.harvest_date_from is not None:
            query = query.filter(HarvestEvent.harvest_date >= filters.harvest_date_from)
        if filters.harvest_date_to is not None:
            query = query.filter(HarvestEvent.harvest_date <= filters.harvest_date_to)

        total_count = query.count()
        query = query.order_by(HarvestRecord.id)
        offset = (filters.page - 1) * filters.page_size
        records = query.offset(offset).limit(filters.page_size).all()

        return [
            HarvestRecordQueryRead(
                **HarvestRecordRead.model_validate(record).model_dump(),
                harvest_date=harvest_date,
                field_name=field_name,
            )
            for record, harvest_date, field_name in records
        ], total_count


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
