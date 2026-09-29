from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from petland.modules.scheduling.infrastructure.models import (
    AppointmentRecord,
    ConfigurationRecord,
    ResourceRecord,
)
from petland.shared.domain.errors import BusinessError


def lock_schedule(session: Session) -> None:
    session.execute(
        select(ConfigurationRecord.id).where(ConfigurationRecord.id == 1).with_for_update()
    ).scalar_one()


def protect_pet(session: Session, pet_id: UUID) -> None:
    if session.scalar(
        select(AppointmentRecord.id)
        .where(
            AppointmentRecord.pet_id == pet_id,
            AppointmentRecord.status == "BOOKED",
            AppointmentRecord.ends_at > datetime.now(UTC),
        )
        .limit(1)
    ):
        raise BusinessError("FUTURE_BOOKINGS", 409)


def protect_worker(session: Session, user_id: UUID) -> None:
    if session.scalar(
        select(AppointmentRecord.id)
        .join(ResourceRecord)
        .where(
            ResourceRecord.user_id == user_id,
            AppointmentRecord.status == "BOOKED",
            AppointmentRecord.ends_at > datetime.now(UTC),
        )
        .limit(1)
    ):
        raise BusinessError("FUTURE_BOOKINGS", 409)
