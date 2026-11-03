from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class SeedInventoryCreate(BaseModel):
    crop_type: str = Field(min_length=1, max_length=100)
    variety_name: str | None = Field(default=None, max_length=150)
    breeding_line: str | None = Field(default=None,max_length=150)
    seed_weight_g: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=4)
    seed_count: int | None = Field(default=None, ge=0)
    notes: str | None = None

class SeedInventoryUpdate(BaseModel):
    crop_type: str = Field(min_length=1, max_length=100)
    variety_name: str | None = Field(default=None, max_length=150)
    breeding_line: str | None = Field(default=None,max_length=150)
    seed_weight_g: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=4)
    seed_count: int | None = Field(default=None, ge=0)
    notes: str | None = None

class SeedInventoryRead(SeedInventoryCreate):
    id: int
    date_recorded: datetime
    model_config = ConfigDict(from_attributes=True)