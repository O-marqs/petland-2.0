from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from petland.modules.catalog.public.booking import booking_service
from petland.modules.customers.public.access import customer_for
from petland.modules.customers.public.contact import customer_email
from petland.modules.identity.public import Actor
from petland.modules.identity.public.audit import record
from petland.modules.identity.public.workforce import current_actor, eligible_workers
from petland.modules.pets.public.booking import booking_pet
from petland.modules.scheduling.application.ports import ScheduleStore
from petland.modules.scheduling.domain.models import (
    Appointment,
    Configuration,
    Event,
    Offer,
    Resource,
    Worker,
)
from petland.modules.scheduling.infrastructure.models import (
    AppointmentRecord,
    ConfigurationRecord,
    EventRecord,
    IdempotencyRecord,
    OutboxRecord,
    ResourceRecord,
)
from petland.modules.scheduling.infrastructure.values import (
    appointment_value,
    calendar_value,
    configuration_value,
    document,
)
from petland.modules.scheduling.public.coordination import lock_schedule
from petland.shared.domain.errors import BusinessError


class PostgresSchedule:
    def __init__(self, session: Session) -> None:
        self.db = session

    def lock(self) -> None:
        lock_schedule(self.db)

    def actor(self, actor_id: UUID) -> Actor:
        return current_actor(self.db, actor_id)

    def customer_for(self, actor_id: UUID, assisted_id: UUID | None) -> UUID:
        return customer_for(self.db, actor_id, assisted_id)

    def offer(self, customer_id: UUID, pet_id: UUID, service_id: UUID) -> Offer:
        pet = booking_pet(self.db, customer_id, pet_id)
        service = booking_service(self.db, service_id)
        option = next((o for o in service.options if o.size == pet.size), None)
        if not service.active or pet.species_id not in service.species_ids or option is None:
            raise BusinessError("OFFER_CHANGED", 409)
        return Offer(
            service.id,
            service.name,
            pet.name,
            pet.size,
            option.price,
            option.duration_minutes,
            option.buffer_before_minutes,
            option.buffer_after_minutes,
            service.version,
        )

    def validate_pet(self, customer_id: UUID, pet_id: UUID, offer: Offer) -> None:
        pet = booking_pet(self.db, customer_id, pet_id)
        if pet.size != offer.size:
            raise BusinessError("OFFER_CHANGED", 409)

    def configuration(self) -> Configuration:
        row = self.db.get(ConfigurationRecord, 1, populate_existing=True)
        if row is None:
            raise BusinessError("SERVICE_UNAVAILABLE", 503)
        return configuration_value(row.data)

    def save_configuration(self, value: Configuration) -> None:
        self.db.merge(ConfigurationRecord(id=1, data=document(value)))
        self.db.flush()

    def audit(self, actor_id: UUID, target_id: UUID, action: str, request_id: str) -> None:
        record(self.db, actor_id, target_id, action, request_id)

    def workers(self) -> list[Worker]:
        return [Worker(id, name) for id, name in eligible_workers(self.db)]

    def resources(self) -> list[Resource]:
        return [
            Resource(
                r.user_id,
                r.name,
                [UUID(s) for s in r.service_ids],
                r.active,
                calendar_value(r.calendar) if r.calendar is not None else None,
                r.id,
                r.version,
            )
            for r in self.db.scalars(
                select(ResourceRecord).order_by(ResourceRecord.name, ResourceRecord.id)
            )
        ]

    def validate_resource(self, value: Resource) -> None:
        if value.active and value.user_id not in {w.id for w in self.workers()}:
            raise BusinessError("INVALID_WORKER", 422)
        for service_id in value.service_ids:
            booking_service(self.db, service_id)

    def save_resource(self, value: Resource) -> None:
        self.db.merge(
            ResourceRecord(
                id=value.id,
                user_id=value.user_id,
                name=value.name,
                active=value.active,
                service_ids=[str(s) for s in value.service_ids],
                calendar=document(value.calendar) if value.calendar is not None else None,
                version=value.version,
            )
        )
        self.db.flush()

    @staticmethod
    def value(row: AppointmentRecord) -> Appointment:
        return appointment_value({k: getattr(row, k) for k in Appointment.__dataclass_fields__})

    def appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        return [
            self.value(r)
            for r in self.db.scalars(
                select(AppointmentRecord).where(
                    AppointmentRecord.occupied_start_at < end,
                    AppointmentRecord.occupied_end_at > start,
                    AppointmentRecord.status == "BOOKED",
                )
            )
        ]

    def appointments_page(
        self, customer_id: UUID | None, offset: int, limit: int
    ) -> tuple[list[Appointment], int]:
        query = select(AppointmentRecord)
        if customer_id is not None:
            query = query.where(AppointmentRecord.customer_id == customer_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = self.db.scalars(
            query.order_by(AppointmentRecord.starts_at.desc(), AppointmentRecord.id)
            .offset(offset)
            .limit(limit)
        )
        return [self.value(r) for r in rows], total

    def get(self, appointment_id: UUID, customer_id: UUID | None) -> Appointment:
        query = select(AppointmentRecord).where(AppointmentRecord.id == appointment_id)
        if customer_id is not None:
            query = query.where(AppointmentRecord.customer_id == customer_id)
        row = self.db.scalar(query)
        if row is None:
            raise BusinessError("NOT_FOUND", 404)
        return self.value(row)

    def save(self, value: Appointment) -> None:
        self.db.merge(AppointmentRecord(**{**asdict(value), "offer": document(value.offer)}))
        self.db.flush()

    def events(self, appointment_id: UUID) -> list[Event]:
        return [
            Event(**{k: getattr(row, k) for k in Event.__dataclass_fields__})
            for row in self.db.scalars(
                select(EventRecord)
                .where(EventRecord.appointment_id == appointment_id)
                .order_by(EventRecord.occurred_at, EventRecord.id)
            )
        ]

    def record(self, event: Event, appointment: Appointment, request_id: str) -> None:
        self.db.add(EventRecord(**asdict(event)))
        self.audit(event.actor_id, appointment.id, f"appointment.{event.kind}", request_id)
        labels = {
            "book": "Reserva confirmada",
            "reschedule": "Reserva reagendada",
            "cancel": "Reserva cancelada",
        }
        at = appointment.starts_at.astimezone(ZoneInfo(appointment.timezone)).strftime(
            "%d/%m/%Y às %H:%M"
        )
        self.db.add(
            OutboxRecord(
                id=event.id,
                appointment_id=appointment.id,
                recipient=customer_email(self.db, appointment.customer_id),
                subject=f"PetLand — {labels[event.kind]}",
                body=f"{labels[event.kind]}\nPet: {appointment.offer.pet_name}\nServiço: {appointment.offer.service_name}\nHorário: {at} ({appointment.timezone})\nMotivo: {event.reason or 'Reserva confirmada pelo responsável.'}\nReferência: {appointment.id}\nPara dúvidas, entre em contato com a equipe pelo contato habitual.",
                created_at=event.occurred_at,
                available_at=event.occurred_at,
                delivered_at=None,
                attempts=0,
                lease_until=None,
            )
        )

    def replay(
        self, actor_id: UUID, operation: str, key: UUID, signature: str
    ) -> Appointment | None:
        row = self.db.get(IdempotencyRecord, (actor_id, operation, key))
        if row is None:
            return None
        if row.signature != signature:
            raise BusinessError("IDEMPOTENCY_MISMATCH", 409)
        return appointment_value(row.response)

    def remember(
        self, actor_id: UUID, operation: str, key: UUID, signature: str, result: Appointment
    ) -> None:
        self.db.add(
            IdempotencyRecord(
                actor_id=actor_id,
                operation=operation,
                key=key,
                signature=signature,
                response=document(result),
                created_at=datetime.now(UTC),
            )
        )


@contextmanager
def schedule_store(engine: Engine) -> Iterator[ScheduleStore]:
    try:
        with Session(engine) as session, session.begin():
            yield PostgresSchedule(session)
    except IntegrityError as exc:
        if getattr(exc.orig, "sqlstate", None) == "23P01":
            raise BusinessError("SLOT_UNAVAILABLE", 409) from None
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise BusinessError("RESOURCE_EXISTS", 409) from None
        raise
    except DBAPIError as exc:
        if getattr(exc.orig, "sqlstate", None) in {"55P03", "57014", "40P01", "40001"}:
            raise BusinessError("SCHEDULE_BUSY", 503) from None
        raise
