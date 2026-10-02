from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from petland.shared.database import Base


class SpeciesRecord(Base):
    __tablename__ = "species"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)


class BreedRecord(Base):
    __tablename__ = "breeds"
    __table_args__ = (UniqueConstraint("id", "species_id"), UniqueConstraint("species_id", "name"))
    id: Mapped[UUID] = mapped_column(primary_key=True)
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"))
    name: Mapped[str] = mapped_column(String(80))


class PetRecord(Base):
    __tablename__ = "pets"
    __table_args__ = (
        ForeignKeyConstraint(["breed_id", "species_id"], ["breeds.id", "breeds.species_id"]),
        CheckConstraint("size IN ('SMALL','MEDIUM','LARGE')", name="size"),
        CheckConstraint("sex IN ('UNKNOWN','FEMALE','MALE')", name="sex"),
        CheckConstraint("NOT birth_estimated OR birth_date IS NOT NULL", name="estimated_date"),
        UniqueConstraint("id", "customer_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"))
    breed_id: Mapped[UUID | None]
    size: Mapped[str] = mapped_column(String(16))
    sex: Mapped[str] = mapped_column(String(16))
    birth_date: Mapped[date | None]
    birth_estimated: Mapped[bool]
    care_notes: Mapped[str] = mapped_column(String(1000))
    allergies: Mapped[str] = mapped_column(String(1000), server_default="")
    handling_notes: Mapped[str] = mapped_column(String(1000), server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int]
