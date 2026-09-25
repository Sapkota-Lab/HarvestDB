from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HarvestRecordCreate(BaseModel):
    plot_number: str = Field(min_length=1, max_length=64)
    dynamic_data: dict[str, Any] = Field(default_factory=dict)


class HarvestRecordRead(HarvestRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    harvest_event_id: int
    created_at: datetime | None = None


class HarvestRecordQueryRead(HarvestRecordRead):
    field_name: str
    harvest_date: date
