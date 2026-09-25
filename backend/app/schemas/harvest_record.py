from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class HarvestRecordCreate(BaseModel):
    plot_number: str = Field(min_length=1, max_length=64)
    dynamic_data: dict[str, Any] = Field(default_factory=dict)


class HarvestRecordUpdate(BaseModel):
    plot_number: str | None = Field(default=None, min_length=1, max_length=64)
    dynamic_data: dict[str, Any] | None = None

    @field_validator("dynamic_data", mode="before")
    @classmethod
    def dynamic_data_not_null(cls, value):
        if value is None:
            raise ValueError("dynamic_data cannot be null")
        return value


class HarvestRecordRead(HarvestRecordCreate):
    id: int
    harvest_event_id: int
    created_at: datetime | None = None
