from datetime import date
from pydantic import BaseModel, Field


class HarvestRecordFilter(BaseModel):
    """Query filters for harvest records."""
    
    harvest_event_id: int | None = Field(default=None, description="Filter by harvest event ID")
    field_id: int | None = Field(default=None, description="Filter by field ID")
    plot_number: str | None = Field(default=None, description="Filter by plot number (partial match)")
    harvest_date_from: date | None = Field(default=None, description="Filter records from this harvest date onwards")
    harvest_date_to: date | None = Field(default=None, description="Filter records up to this harvest date")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Number of records per page")
