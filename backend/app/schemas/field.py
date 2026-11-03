from pydantic import BaseModel, ConfigDict, Field, field_validator


class FieldCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2048)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class FieldRead(FieldCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
