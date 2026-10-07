from datetime import date
from pydantic import BaseModel, Field, model_validator


class HarvestRecordFilter(BaseModel):
    """Query filters for harvest records."""

    harvest_event_id: int | None = Field(default=None, description="Filter by harvest event ID")
    field_id: int | None = Field(default=None, description="Filter by field ID")
    plot_number: str | None = Field(default=None, description="Filter by plot number (partial match)")
    harvest_date_from: date | None = Field(default=None, description="Filter records from this harvest date onwards")
    harvest_date_to: date | None = Field(default=None, description="Filter records up to this harvest date")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of records per page")

    @model_validator(mode="after")
    def _validate_date_range(self) -> "HarvestRecordFilter":
        if (
            self.harvest_date_from is not None
            and self.harvest_date_to is not None
            and self.harvest_date_from > self.harvest_date_to
        ):
            raise ValueError("harvest_date_from must not be later than harvest_date_to")
        return self
