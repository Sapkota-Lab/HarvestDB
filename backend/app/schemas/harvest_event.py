from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class HarvestEventCreate(BaseModel):
    harvest_date: date
    harvest_number: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=2048)


class HarvestEventRead(HarvestEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_id: int
