import csv
import io

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.harvest_record import HarvestRecord
from app.models.harvest_event import HarvestEvent
from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead
from app.schemas.harvest_record_filter import HarvestRecordFilter


class CropService:
    def create(self, db: Session, payload: HarvestRecordCreate, harvest_event_id: int) -> HarvestRecordRead:
        harvest_record = HarvestRecord(
            harvest_event_id=harvest_event_id,
            plot_number=payload.plot_number,
            dynamic_data=payload.dynamic_data,
        )
        db.add(harvest_record)
        db.commit()
        db.refresh(harvest_record)
        return HarvestRecordRead.model_validate(harvest_record)

    def import_csv(self, db: Session, csv_text: str, harvest_event_id: int) -> list[HarvestRecordRead]:
        # printing instead of inserting until issue #4 (testing DB) is ready — swap this
        # for a real insert once there's a DB to insert into
        reader = csv.DictReader(io.StringIO(csv_text))
        records: list[HarvestRecordRead] = []

        for line_number, row in enumerate(reader, start=2):  # header occupies line 1
            try:
                payload = HarvestRecordCreate(**_clean_row(row))
            except ValidationError as exc:
                raise ValueError(f"Row {line_number}: {exc}") from exc

            print(f"[CSV import] harvest_event_id={harvest_event_id} row={line_number} {payload.model_dump()}")
            harvest_record = HarvestRecord(
                harvest_event_id=harvest_event_id,
                plot_number=payload.plot_number,
                dynamic_data=payload.dynamic_data,
            )
            db.add(harvest_record)
            records.append(HarvestRecordRead.model_validate(harvest_record))

        db.commit()
        return records

    # has to stay below import_csv — a method named `list` shadows the builtin `list`,
    # which breaks the `list[...]` type hints on anything defined after it in this class
    def list(self, db: Session, filters: HarvestRecordFilter) -> tuple[list[HarvestRecordRead], int]:
        """
        Query harvest records with filters and pagination.
        
        Returns:
            Tuple of (records, total_count)
        """
        query = db.query(HarvestRecord)

        # Filter by harvest event
        if filters.harvest_event_id is not None:
            query = query.filter(HarvestRecord.harvest_event_id == filters.harvest_event_id)

        if filters.field_id is not None or filters.harvest_date_from is not None or filters.harvest_date_to is not None:
            query = query.join(HarvestEvent)

        # Filter by field
        if filters.field_id is not None:
            query = query.filter(HarvestEvent.field_id == filters.field_id)

        # Filter by plot number (case-insensitive partial match)
        if filters.plot_number is not None:
            query = query.filter(HarvestRecord.plot_number.ilike(f"%{filters.plot_number}%"))

        # Filter by harvest date range
        if filters.harvest_date_from is not None or filters.harvest_date_to is not None:
            if filters.harvest_date_from is not None:
                query = query.filter(HarvestEvent.harvest_date >= filters.harvest_date_from)
            if filters.harvest_date_to is not None:
                query = query.filter(HarvestEvent.harvest_date <= filters.harvest_date_to)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        records = query.offset(offset).limit(filters.page_size).all()

        return [HarvestRecordRead.model_validate(r) for r in records], total_count


def _clean_row(row: dict) -> dict:
    # DictReader turns blank cells into "" and dumps any extra unnamed columns under a None key
    cleaned = {}
    for key, value in row.items():
        if key is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        cleaned[key] = value or None
    return cleaned
