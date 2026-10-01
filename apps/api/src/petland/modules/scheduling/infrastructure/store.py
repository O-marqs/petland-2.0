import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from petland.modules.catalog.public.booking import booking_service
from petland.modules.customers.public.access import customer_booking_contact
from petland.modules.customers.public.contact import (
    customer_contact,
    customer_email,
    customer_names,
    matching_customer_ids,
)
from petland.modules.identity.public import Actor
from petland.modules.identity.public.audit import record
from petland.modules.identity.public.workforce import (
    actor_names,
    current_actor,
    eligible_worker_ids,
    eligible_workers,
)
from petland.modules.pets.public.booking import booking_pet, care_context
from petland.modules.scheduling.application.ports import PeriodTotals, ScheduleStore
from petland.modules.scheduling.domain.models import (
    OCCUPYING,
    OPEN_STATUSES,
    Appointment,
    Configuration,
    Event,
    Offer,
    Resource,
    Worker,
)
from petland.modules.scheduling.domain.operations import AppointmentFilter, CareContext, Note
from petland.modules.scheduling.infrastructure.models import (
    AppointmentRecord,
    ConfigurationRecord,
    EventRecord,
    IdempotencyRecord,
    NoteRecord,
    OutboxRecord,
    ResourceRecord,
)
from petland.modules.scheduling.infrastructure.values import (
    appointment_value,
    calendar_value,
    configuration_value,
    document,
    offer_value,
)
from petland.modules.scheduling.public.coordination import lock_schedule
from petland.shared.domain.errors import BusinessError


class PostgresSchedule:
    def __init__(self, session: Session) -> None:
        self.db = session
        self._locked_configuration: Configuration | None = None
        self._customer_emails: dict[UUID, str] = {}

    def lock(self, shared: bool = False) -> None:
        self._locked_configuration = configuration_value(lock_schedule(self.db, shared=shared))

    def actor(self, actor_id: UUID) -> Actor:
        return current_actor(self.db, actor_id)

    def actor_names(self, ids: list[UUID]) -> dict[UUID, str]:
        return actor_names(self.db, ids)

    def customer_for(self, actor_id: UUID, assisted_id: UUID | None) -> UUID:
        owner, email = customer_booking_contact(self.db, actor_id, assisted_id)
        self._customer_emails[owner] = email
        return owner

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
        if self._locked_configuration is not None:
            return self._locked_configuration
        row = self.db.get(ConfigurationRecord, 1, populate_existing=True)
        if row is None:
            raise BusinessError("SERVICE_UNAVAILABLE", 503)
        return configuration_value(row.data)

    def save_configuration(self, value: Configuration) -> None:
        self.db.merge(ConfigurationRecord(id=1, data=document(value)))
        self.db.flush()
        if self._locked_configuration is not None:
            self._locked_configuration = value

    def audit(self, actor_id: UUID, target_id: UUID, action: str, request_id: str) -> None:
        record(self.db, actor_id, target_id, action, request_id)

    def workers(self) -> list[Worker]:
        return [Worker(id, name) for id, name in eligible_workers(self.db)]

    def resources(self, eligible_only: bool = False) -> list[Resource]:
        query = select(ResourceRecord).order_by(ResourceRecord.name, ResourceRecord.id)
        if eligible_only:
            query = query.where(
                ResourceRecord.active,
                ResourceRecord.user_id.in_(eligible_worker_ids()),
            )
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
            for r in self.db.scalars(query)
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
        return Appointment(
            **{
                **{k: getattr(row, k) for k in Appointment.__dataclass_fields__},
                "offer": offer_value(row.offer),
            }
        )

    def appointments(self, start: datetime, end: datetime) -> list[Appointment]:
        return [
            self.value(r)
            for r in self.db.scalars(
                select(AppointmentRecord).where(
                    AppointmentRecord.occupied_start_at < end,
                    or_(
                        AppointmentRecord.occupied_end_at > start,
                        AppointmentRecord.status.in_({"ARRIVED", "IN_PROGRESS"}),
                    ),
                    AppointmentRecord.status.in_(OCCUPYING),
                )
            )
        ]

    def appointments_page(
        self,
        customer_id: UUID | None,
        offset: int,
        limit: int,
        filters: AppointmentFilter | None = None,
    ) -> tuple[list[Appointment], int]:
        query = select(AppointmentRecord)
        if customer_id is not None:
            query = query.where(AppointmentRecord.customer_id == customer_id)
        f = filters or AppointmentFilter()
        if f.start:
            query = query.where(AppointmentRecord.starts_at >= f.start)
        if f.end:
            query = query.where(AppointmentRecord.starts_at < f.end)
        if f.status:
            query = query.where(AppointmentRecord.status == f.status)
        if f.pet_id:
            query = query.where(AppointmentRecord.pet_id == f.pet_id)
        if f.resource_id:
            query = query.where(AppointmentRecord.resource_id == f.resource_id)
        if f.search:
            query = query.where(
                or_(
                    AppointmentRecord.offer["pet_name"].astext.icontains(f.search, autoescape=True),
                    AppointmentRecord.customer_id.in_(matching_customer_ids(f.search)),
                )
            )
        if f.period == "upcoming":
            query = query.where(
                AppointmentRecord.status.in_(OPEN_STATUSES),
                or_(
                    AppointmentRecord.ends_at > f.now,
                    AppointmentRecord.status.in_({"ARRIVED", "IN_PROGRESS"}),
                ),
            )
        elif f.period == "history":
            query = query.where(
                or_(
                    AppointmentRecord.status.not_in(OPEN_STATUSES),
                    (AppointmentRecord.status == "BOOKED") & (AppointmentRecord.ends_at <= f.now),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = self.db.scalars(
            query.order_by(
                AppointmentRecord.starts_at
                if f.period == "upcoming" or f.start
                else AppointmentRecord.starts_at.desc(),
                AppointmentRecord.id,
            )
            .offset(offset)
            .limit(limit)
        )
        return [self.value(r) for r in rows], total

    def period_totals(self, start: datetime, end: datetime) -> PeriodTotals:
        a = AppointmentRecord
        service_name = a.offer["service_name"].astext
        cohort = (a.starts_at >= start) & (a.starts_at < end)
        minutes = (
            func.extract(
                "epoch",
                func.least(end, a.occupied_end_at) - func.greatest(start, a.occupied_start_at),
            )
            / 60
        )
        query = (
            select(
                a.status,
                service_name,
                func.sum(case((cohort, 1), else_=0)),
                func.sum(case((a.status.in_(OCCUPYING), minutes), else_=0)),
            )
            .where(a.occupied_start_at < end, a.occupied_end_at > start)
            .group_by(
                a.status,
                service_name,
            )
        )
        totals = PeriodTotals(0, {}, {}, 0)
        for status, service, count, occupied in self.db.execute(query):
            totals.total += count
            if count:
                totals.by_status[status] = totals.by_status.get(status, 0) + count
                totals.by_service[service] = totals.by_service.get(service, 0) + count
            totals.occupied_minutes += float(occupied)
        return totals

    def customer_names(self, ids: list[UUID]) -> dict[UUID, str]:
        return customer_names(self.db, ids)

    def context(self, appointment: Appointment) -> CareContext:
        return CareContext(
            *customer_contact(self.db, appointment.customer_id),
            *care_context(self.db, appointment.customer_id, appointment.pet_id),
        )

    def notes(self, appointment_id: UUID, internal: bool) -> list[Note]:
        query = select(NoteRecord).where(NoteRecord.appointment_id == appointment_id)
        if not internal:
            query = query.where(NoteRecord.visibility == "PUBLIC")
        return [
            Note(**{k: getattr(row, k) for k in Note.__dataclass_fields__})
            for row in self.db.scalars(query.order_by(NoteRecord.occurred_at, NoteRecord.id))
        ]

    def add_note(self, note: Note) -> None:
        self.db.add(NoteRecord(**asdict(note)))

    def get(self, appointment_id: UUID, customer_id: UUID | None) -> Appointment:
        query = select(AppointmentRecord).where(AppointmentRecord.id == appointment_id)
        if customer_id is not None:
            query = query.where(AppointmentRecord.customer_id == customer_id)
        row = self.db.scalar(query)
        if row is None:
            raise BusinessError("NOT_FOUND", 404)
        return self.value(row)

    def save(self, value: Appointment) -> None:
        row = AppointmentRecord(**{**asdict(value), "offer": document(value.offer)})
        if value.version == 1:
            self.db.add(row)
        else:
            self.db.merge(row)
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
            "cancel_exception": "Reserva cancelada pela equipe",
        }
        if event.kind not in labels:
            return
        at = appointment.starts_at.astimezone(ZoneInfo(appointment.timezone)).strftime(
            "%d/%m/%Y às %H:%M"
        )
        recipient = self._customer_emails.get(appointment.customer_id)
        if recipient is None:
            recipient = customer_email(self.db, appointment.customer_id)
        self.db.add(
            OutboxRecord(
                id=event.id,
                appointment_id=appointment.id,
                recipient=recipient,
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
            logging.getLogger("petland").warning(
                "schedule_busy", extra={"error_type": type(exc.orig).__name__}
            )
            raise BusinessError("SCHEDULE_BUSY", 503) from None
        raise
