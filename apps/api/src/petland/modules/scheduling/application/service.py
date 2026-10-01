import hashlib
import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from petland.modules.identity.public import Actor
from petland.modules.scheduling.application.operations import Operations
from petland.modules.scheduling.application.ports import ScheduleStore
from petland.modules.scheduling.domain.models import (
    OPEN_STATUSES,
    Appointment,
    Availability,
    Configuration,
    Event,
    Resource,
    Slot,
    Worker,
    allocate,
    candidates,
    fits,
)
from petland.modules.scheduling.domain.operations import AppointmentFilter, Note
from petland.shared.domain.errors import BusinessError


class Scheduling:
    def __init__(
        self,
        store: Callable[[], AbstractContextManager[ScheduleStore]],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.store = store
        self.clock = clock
        self.operations = Operations(store, clock)

    @staticmethod
    def scope(store: ScheduleStore, actor: Actor, customer_id: UUID | None) -> UUID:
        store.actor(actor.id).require("booking:assist" if customer_id else "customer:own")
        return store.customer_for(actor.id, customer_id)

    @staticmethod
    def live_resources(store: ScheduleStore) -> list[Resource]:
        return store.resources(eligible_only=True)

    def settings(self, actor: Actor) -> tuple[Configuration, list[Resource], list[Worker]]:
        actor.require("establishment:manage")
        with self.store() as store:
            return store.configuration(), store.resources(), store.workers()

    def establishment(self) -> Configuration:
        with self.store() as store:
            return store.configuration()

    def impact(
        self, store: ScheduleStore, config: Configuration, resources: list[Resource]
    ) -> list[UUID]:
        now = self.clock()
        future = store.appointments(now, datetime.max.replace(tzinfo=UTC))
        previous = store.configuration()
        by_id = {r.id: r for r in resources if r.active}
        return [
            b.id
            for b in future
            if b.status in OPEN_STATUSES
            and (
                not config.enabled
                or previous.timezone != config.timezone
                or (r := by_id.get(b.resource_id)) is None
                or b.service_id not in r.service_ids
                or not fits(config, r, b.occupied_start_at, b.occupied_end_at)
            )
        ]

    def configure(
        self, actor: Actor, value: Configuration, request_id: str, preview: bool = False
    ) -> list[UUID]:
        value.validate()
        with self.store() as store:
            store.lock()
            store.actor(actor.id).require("establishment:manage")
            current = store.configuration()
            if current.version != value.version:
                raise BusinessError("STALE_VERSION", 409)
            impacted = self.impact(store, value, self.live_resources(store))
            if not preview:
                if impacted:
                    raise BusinessError("CALENDAR_IMPACT", 409)
                store.save_configuration(replace(value, version=value.version + 1))
                store.audit(actor.id, UUID(int=1), "calendar.updated", request_id)
            return impacted

    def resource(
        self, actor: Actor, value: Resource, request_id: str, existing_id: UUID | None = None
    ) -> Resource:
        value.validate()
        with self.store() as store:
            store.lock()
            store.actor(actor.id).require("establishment:manage")
            resources = store.resources()
            previous = next((r for r in resources if r.id == existing_id), None)
            if existing_id and previous is None:
                raise BusinessError("NOT_FOUND", 404)
            if previous:
                if previous.version != value.version:
                    raise BusinessError("STALE_VERSION", 409)
                if previous.user_id != value.user_id:
                    raise BusinessError("INVALID_CALENDAR", 422)
                value = replace(value, id=previous.id, version=previous.version + 1)
            store.validate_resource(value)
            if any(r.user_id == value.user_id and r.id != value.id for r in resources):
                raise BusinessError("RESOURCE_EXISTS", 409)
            next_resources = [r for r in resources if r.id != value.id] + [value]
            workers = {w.id for w in store.workers()}
            next_resources = [r for r in next_resources if r.user_id in workers]
            config = store.configuration()
            if self.impact(store, config, next_resources):
                raise BusinessError("CALENDAR_IMPACT", 409)
            store.save_resource(value)
            store.save_configuration(replace(config, version=config.version + 1))
            store.audit(
                actor.id,
                value.id,
                "resource.updated" if previous else "resource.created",
                request_id,
            )
            return value

    def availability(
        self,
        actor: Actor,
        customer_id: UUID | None,
        pet_id: UUID,
        service_id: UUID,
        day: date,
        appointment_id: UUID | None = None,
    ) -> Availability:
        with self.store() as store:
            owner = self.scope(store, actor, customer_id)
            original = store.get(appointment_id, owner) if appointment_id else None
            if original and (
                original.pet_id != pet_id
                or original.service_id != service_id
                or original.status != "BOOKED"
            ):
                raise BusinessError("INVALID_BOOKING", 422)
            offer = original.offer if original else store.offer(owner, pet_id, service_id)
            store.validate_pet(owner, pet_id, offer)
            config, now = store.configuration(), self.clock()
            resources = self.live_resources(store)
            times = candidates(config, day, now)
            existing = store.appointments(
                datetime.combine(day, datetime.min.time(), tzinfo=UTC) - timedelta(days=2),
                datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(days=3),
            )
            slots = [
                Slot(start, start + timedelta(minutes=offer.duration_minutes))
                for start in times
                if allocate(config, resources, existing, pet_id, offer, start, appointment_id)
            ]
            return Availability(
                day,
                config.timezone,
                config.version,
                offer,
                slots,
                now,
                config.enabled,
                original.change_cutoff_minutes if original else config.change_cutoff_minutes,
            )

    def appointments_page(
        self,
        actor: Actor,
        assisted: bool,
        customer_id: UUID | None,
        offset: int,
        limit: int,
        filters: AppointmentFilter | None = None,
    ) -> tuple[list[Appointment], int]:
        with self.store() as store:
            store.actor(actor.id).require("booking:assist" if assisted else "customer:own")
            owner = (
                None
                if assisted and customer_id is None
                else store.customer_for(actor.id, customer_id)
            )
            return store.appointments_page(owner, offset, limit, filters)

    def public_notes(self, actor: Actor, assisted: bool, appointment_id: UUID) -> list[Note]:
        with self.store() as store:
            store.actor(actor.id).require("booking:assist" if assisted else "customer:own")
            owner = None if assisted else store.customer_for(actor.id, None)
            store.get(appointment_id, owner)
            return store.notes(appointment_id, False)

    def detail(
        self, actor: Actor, assisted: bool, appointment_id: UUID
    ) -> tuple[Appointment, list[Event]]:
        with self.store() as store:
            store.actor(actor.id).require("booking:assist" if assisted else "customer:own")
            owner = None if assisted else store.customer_for(actor.id, None)
            appointment = store.get(appointment_id, owner)
            return appointment, [
                e for e in store.events(appointment.id) if e.kind != "note_internal"
            ]

    def command(
        self,
        actor: Actor,
        customer_id: UUID | None,
        operation: str,
        key: UUID,
        request_id: str,
        pet_id: UUID | None = None,
        service_id: UUID | None = None,
        starts_at: datetime | None = None,
        offer_version: int | None = None,
        configuration_version: int | None = None,
        appointment_id: UUID | None = None,
        version: int | None = None,
        reason: str = "",
        assisted: bool = False,
    ) -> Appointment:
        if operation not in {"book", "reschedule", "cancel"}:
            raise BusinessError("INVALID_BOOKING", 422)
        if starts_at is not None:
            if starts_at.tzinfo is None:
                raise BusinessError("INVALID_BOOKING", 422)
            starts_at = starts_at.astimezone(UTC)
        signature = hashlib.sha256(
            json.dumps(
                {
                    "customer": str(customer_id),
                    "pet": str(pet_id),
                    "service": str(service_id),
                    "start": starts_at.isoformat() if starts_at else None,
                    "offer": offer_version,
                    "configuration": configuration_version,
                    "appointment": str(appointment_id),
                    "version": version,
                    "reason": reason,
                    "assisted": assisted,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        with self.store() as store:
            store.lock()
            store.actor(actor.id).require("booking:assist" if assisted else "customer:own")
            if not assisted and customer_id is not None:
                raise BusinessError("FORBIDDEN", 403)
            owner = (
                None
                if assisted and customer_id is None
                else store.customer_for(actor.id, customer_id)
            )
            replay = store.replay(actor.id, operation, key, signature)
            if replay:
                return replay
            now = self.clock()
            original = store.get(appointment_id, owner) if appointment_id else None
            if operation == "book":
                if owner is None or pet_id is None or service_id is None or original is not None:
                    raise BusinessError("INVALID_BOOKING", 422)
                offer = store.offer(owner, pet_id, service_id)
                if offer.version != offer_version:
                    raise BusinessError("OFFER_CHANGED", 409)
            else:
                if original is None:
                    raise BusinessError("NOT_FOUND", 404)
                if original.version != version:
                    raise BusinessError("STALE_VERSION", 409)
                if original.status != "BOOKED" or original.starts_at <= now:
                    raise BusinessError("BOOKING_CLOSED", 409)
                if not assisted and now > original.starts_at - timedelta(
                    minutes=original.change_cutoff_minutes
                ):
                    raise BusinessError("CHANGE_WINDOW_CLOSED", 409)
                if not reason.strip() or len(reason) > 500:
                    raise BusinessError("INVALID_BOOKING", 422)
                offer, owner, pet_id = original.offer, original.customer_id, original.pet_id
            if operation == "cancel":
                assert original is not None
                result = replace(
                    original, status="CANCELLED", version=original.version + 1, updated_at=now
                )
            else:
                assert owner is not None and pet_id is not None
                if starts_at is None:
                    raise BusinessError("INVALID_BOOKING", 422)
                config = store.configuration()
                if configuration_version != config.version:
                    raise BusinessError("OFFER_CHANGED", 409)
                if operation != "book":
                    store.validate_pet(owner, pet_id, offer)
                day = starts_at.astimezone(ZoneInfo(config.timezone)).date()
                if starts_at not in candidates(config, day, now):
                    raise BusinessError("SLOT_UNAVAILABLE", 409)
                existing = store.appointments(
                    starts_at - timedelta(minutes=offer.buffer_before_minutes),
                    starts_at
                    + timedelta(minutes=offer.duration_minutes + offer.buffer_after_minutes),
                )
                resource = allocate(
                    config,
                    self.live_resources(store),
                    existing,
                    pet_id,
                    offer,
                    starts_at,
                    appointment_id,
                )
                if resource is None:
                    raise BusinessError("SLOT_UNAVAILABLE", 409)
                end = starts_at + timedelta(minutes=offer.duration_minutes)
                result = Appointment(
                    owner,
                    pet_id,
                    offer.service_id,
                    resource.id,
                    starts_at,
                    end,
                    starts_at - timedelta(minutes=offer.buffer_before_minutes),
                    end + timedelta(minutes=offer.buffer_after_minutes),
                    offer,
                    config.timezone,
                    original.change_cutoff_minutes if original else config.change_cutoff_minutes,
                    original.created_at if original else now,
                    now,
                )
                if original:
                    result.id, result.version = original.id, original.version + 1
                result.no_show_grace_minutes = (
                    original.no_show_grace_minutes if original else config.no_show_grace_minutes
                )
            store.save(result)
            store.record(
                Event(
                    result.id,
                    actor.id,
                    operation,
                    reason.strip(),
                    result.starts_at,
                    result.ends_at,
                    now,
                ),
                result,
                request_id,
            )
            store.remember(actor.id, operation, key, signature, result)
            return result
