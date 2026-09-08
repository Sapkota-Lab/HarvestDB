import csv
import io

from pydantic import ValidationError

from app.schemas.harvest_record import HarvestRecordCreate, HarvestRecordRead


class CropService:
    def create(self, payload: HarvestRecordCreate, harvest_event_id: int) -> HarvestRecordRead:
        return HarvestRecordRead(id=1, harvest_event_id=harvest_event_id, **payload.model_dump())

    def import_csv(self, csv_text: str, harvest_event_id: int) -> list[HarvestRecordRead]:
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
            records.append(
                HarvestRecordRead(id=len(records) + 1, harvest_event_id=harvest_event_id, **payload.model_dump())
            )

        return records

    # has to stay below import_csv — a method named `list` shadows the builtin `list`,
    # which breaks the `list[...]` type hints on anything defined after it in this class
    def list(self, harvest_event_id: int | None = None) -> list[HarvestRecordRead]:
        return []


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
