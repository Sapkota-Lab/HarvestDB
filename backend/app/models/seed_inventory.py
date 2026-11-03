from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

#-- Seed Inventory table constraints and columns --#

class SeedInventory(Base):
    __tablename__ = "seed_inventory"

    __table_args__ = (CheckConstraint("seed_weight_g >= 0", name = "check_seed_weight",),
                      CheckConstraint("seed_count >= 0", name = "check_seed_count",),)

    id: Mapped[int] = mapped_column (primary_key=True, index=True)

    crop_type: Mapped[str] = mapped_column (String(100), nullable=False, index=True)

    variety_name: Mapped[str | None] = mapped_column (String(150), nullable=True)

    breeding_line: Mapped[str | None] = mapped_column (String(150), nullable=True)

    seed_weight_g: Mapped[Decimal | None] = mapped_column (Numeric(12,4),nullable=True)

    seed_count: Mapped[int | None] = mapped_column(nullable=True)

    date_recorded: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)