from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecordImage(Base):
    __tablename__ = "record_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    harvest_record_id: Mapped[int] = mapped_column(
        ForeignKey("harvest_records.id", ondelete="CASCADE"), index=True
    )
    # Deferred so listing images never loads the file bytes.
    data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    category: Mapped[str] = mapped_column(String(32), default="Other")
    caption: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
