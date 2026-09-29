from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from petland.shared.database import Base


class ServiceRecord(Base):
    __tablename__ = "services"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1500))
    active: Mapped[bool] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int]


class ServiceSpeciesRecord(Base):
    __tablename__ = "service_species"
    service_id: Mapped[UUID] = mapped_column(ForeignKey("services.id"), primary_key=True)
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"), primary_key=True)


class OptionRecord(Base):
    __tablename__ = "service_options"
    __table_args__ = (
        CheckConstraint("size IN ('SMALL','MEDIUM','LARGE')", name="size"),
        CheckConstraint("price >= 0 AND price <= 9999999.99", name="price"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 1440", name="duration"),
    )
    service_id: Mapped[UUID] = mapped_column(ForeignKey("services.id"), primary_key=True)
    size: Mapped[str] = mapped_column(String(16), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_minutes: Mapped[int]
