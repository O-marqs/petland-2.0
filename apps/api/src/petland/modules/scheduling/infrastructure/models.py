from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, String, text
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from petland.shared.database import Base


class ConfigurationRecord(Base):
    __tablename__ = "schedule_configuration"
    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ResourceRecord(Base):
    __tablename__ = "schedule_resources"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    service_ids: Mapped[list[str]] = mapped_column(JSONB)
    active: Mapped[bool]
    calendar: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int]


class AppointmentRecord(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        ForeignKeyConstraint(["pet_id", "customer_id"], ["pets.id", "pets.customer_id"]),
        CheckConstraint(
            "status IN ('BOOKED','ARRIVED','IN_PROGRESS','COMPLETED','CANCELLED','NO_SHOW')",
            name="status",
        ),
        CheckConstraint(
            "reserved_until IS NULL OR (reserved_until >= ends_at AND reserved_until <= occupied_end_at)",
            name="extension",
        ),
        CheckConstraint(
            "(started_at IS NULL OR (arrived_at IS NOT NULL AND started_at >= arrived_at)) AND (completed_at IS NULL OR (started_at IS NOT NULL AND completed_at >= started_at))",
            name="actual_times",
        ),
        CheckConstraint(
            "occupied_start_at <= starts_at AND starts_at < ends_at AND ends_at <= occupied_end_at",
            name="interval",
        ),
        ExcludeConstraint(
            ("resource_id", "="),
            (text("tstzrange(occupied_start_at, occupied_end_at, '[)')"), "&&"),
            where=text("status IN ('BOOKED','ARRIVED','IN_PROGRESS','COMPLETED')"),
            name="appointments_resource_overlap",
            using="gist",
        ),
        ExcludeConstraint(
            ("pet_id", "="),
            (text("tstzrange(starts_at, COALESCE(reserved_until, ends_at), '[)')"), "&&"),
            where=text("status IN ('BOOKED','ARRIVED','IN_PROGRESS','COMPLETED')"),
            name="appointments_pet_overlap",
            using="gist",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id"), index=True)
    pet_id: Mapped[UUID]
    service_id: Mapped[UUID] = mapped_column(ForeignKey("services.id"))
    resource_id: Mapped[UUID] = mapped_column(ForeignKey("schedule_resources.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    occupied_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    occupied_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    offer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    timezone: Mapped[str] = mapped_column(String(64))
    change_cutoff_minutes: Mapped[int]
    status: Mapped[str] = mapped_column(String(16))
    version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    no_show_grace_minutes: Mapped[int] = mapped_column(server_default="0")
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NoteRecord(Base):
    __tablename__ = "appointment_notes"
    __table_args__ = (CheckConstraint("visibility IN ('INTERNAL','PUBLIC')", name="visibility"),)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    appointment_id: Mapped[UUID] = mapped_column(ForeignKey("appointments.id"), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(2000))
    visibility: Mapped[str] = mapped_column(String(16))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EventRecord(Base):
    __tablename__ = "appointment_events"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    appointment_id: Mapped[UUID] = mapped_column(ForeignKey("appointments.id"), index=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(String(500))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IdempotencyRecord(Base):
    __tablename__ = "booking_idempotency"
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    operation: Mapped[str] = mapped_column(String(40), primary_key=True)
    key: Mapped[UUID] = mapped_column(primary_key=True)
    signature: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OutboxRecord(Base):
    __tablename__ = "appointment_outbox"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    appointment_id: Mapped[UUID] = mapped_column(ForeignKey("appointments.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(120))
    body: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
