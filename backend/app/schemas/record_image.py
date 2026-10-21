from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, computed_field


class ImageCategory(str, Enum):
    Tomato = "Tomato"
    Plant = "Plant"
    Leaf = "Leaf"
    Other = "Other"


class RecordImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    harvest_record_id: int
    original_filename: str | None = None
    content_type: str
    size_bytes: int
    category: ImageCategory
    caption: str | None = None
    created_at: datetime | None = None

    @computed_field
    @property
    def url(self) -> str:
        return f"/api/v1/harvest-records/images/{self.id}"
