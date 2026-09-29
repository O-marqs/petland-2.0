import hashlib
import json
from collections import Counter
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from petland.modules.identity.public import Actor
from petland.modules.scheduling.application.ports import ScheduleStore
from petland.modules.scheduling.domain.models import (
    OCCUPYING,
    STATUSES,
    Appointment,
    Event,
    fits,
    overlaps,
)
from petland.modules.scheduling.domain.operations import (
    AppointmentFilter,
    CareContext,
    Note,
    actions,
    available_minutes,
    transition,
)
from petland.shared.domain.errors import BusinessError


@dataclass
class OperationItem:
    appointment: Appointment
    customer_name: str
    resource_name: str
    resource_id: UUID
    allowed_actions: list[str]
    overdue: bool


@dataclass
class OperationDetail:
    item: OperationItem
    context: CareContext
    events: list[Event]
    notes: list[Note]
    authors: dict[UUID, str]


@dataclass
class Agenda:
    items: list[OperationItem]
    total: int
    date_from: date
    date_to: date
    timezone: str
    calculated_at: datetime


@dataclass
class Metrics:
    date_from: date
    date_to: date
    timezone: str
    calculated_at: datetime
    total: int
    by_status: dict[str, int]
    by_service: dict[str, int]
    occupied_minutes: float
    available_minutes: float
    occupancy_percent: float | None


class Operations:
    def __init__(
        self,
        store: Callable[[], AbstractContextManager[ScheduleStore]],
        clock: Callable[[], datetime],
    ) -> None:
        self.store, self.clock = store, clock

    @staticmethod
    def interval(zone: str, first: date, last: date) -> tuple[datetime, datetime]:
        if not 0 <= (last - first).days <= 30:
            raise BusinessError("INVALID_PERIOD", 422)
        tz = ZoneInfo(zone)
        return datetime.combine(first, time(), tzinfo=tz).astimezone(UTC), datetime.combine(
            last + timedelta(days=1), time(), tzinfo=tz
        ).astimezone(UTC)

    @staticmethod
    def item(a: Appointment, name: str, resource: str, now: datetime, admin: bool) -> OperationItem:
        return OperationItem(
            a,
            name,
            resource,
            a.resource_id,
            actions(a, now, admin),
            a.status in {"ARRIVED", "IN_PROGRESS"} and now >= a.capacity_end,
        )

    def agenda(
        self,
        actor: Actor,
        first: date | None,
        last: date | None,
        filters: AppointmentFilter,
        offset: int,
        limit: int,
    ) -> Agenda:
        with self.store() as store:
            live = store.actor(actor.id)
            live.require("operation:read")
            config, now = store.configuration(), self.clock()
            first = first or now.astimezone(ZoneInfo(config.timezone)).date()
            last = last or first
            start, end = self.interval(config.timezone, first, last)
            if filters.status and filters.status not in STATUSES:
                raise BusinessError("INVALID_BOOKING", 422)
            rows, total = store.appointments_page(
                None, offset, limit, replace(filters, start=start, end=end)
            )
            resources = {r.id: r.name for r in store.resources()}
            names = store.customer_names(list({a.customer_id for a in rows}))
            return Agenda(
                [
                    self.item(
                        a,
                        names[a.customer_id],
                        resources[a.resource_id],
                        now,
                        "identity:manage" in live.permissions,
                    )
                    for a in rows
                ],
                total,
                first,
                last,
                config.timezone,
                now,
            )

    def detail(self, actor: Actor, appointment_id: UUID) -> OperationDetail:
        with self.store() as store:
            live = store.actor(actor.id)
            live.require("attendance:execute")
            a = store.get(appointment_id, None)
            context = store.context(a)
            resources = {r.id: r.name for r in store.resources()}
            events, notes = store.events(a.id), store.notes(a.id, True)
            return OperationDetail(
                self.item(
                    a,
                    context.customer_name,
                    resources[a.resource_id],
                    self.clock(),
                    "identity:manage" in live.permissions,
                ),
                context,
                events,
                notes,
                store.actor_names(list({e.actor_id for e in events} | {n.actor_id for n in notes})),
            )

    def command(
        self,
        actor: Actor,
        appointment_id: UUID,
        operation: str,
        version: int,
        key: UUID,
        request_id: str,
        reason: str = "",
        body: str = "",
        visibility: str = "INTERNAL",
        until: datetime | None = None,
        resource_id: UUID | None = None,
    ) -> Appointment:
        if operation not in {
            "arrive",
            "start",
            "complete",
            "no_show",
            "cancel_exception",
            "note",
            "extend",
        }:
            raise BusinessError("INVALID_TRANSITION", 422)
        if len(reason) > 500 or len(body) > 2000 or visibility not in {"INTERNAL", "PUBLIC"}:
            raise BusinessError("INVALID_BOOKING", 422)
        if operation in {"no_show", "cancel_exception", "extend"} and not reason.strip():
            raise BusinessError("REASON_REQUIRED", 422)
        if operation == "note" and not body.strip():
            raise BusinessError("INVALID_BOOKING", 422)
        if until:
            if until.tzinfo is None:
                raise BusinessError("INVALID_BOOKING", 422)
            until = until.astimezone(UTC)
        signature = hashlib.sha256(
            json.dumps(
                [
                    str(appointment_id),
                    operation,
                    version,
                    reason,
                    body,
                    visibility,
                    str(until),
                    str(resource_id),
                ]
            ).encode()
        ).hexdigest()
        with self.store() as store:
            store.lock()
            live = store.actor(actor.id)
            live.require("notes:internal" if operation == "note" else "attendance:execute")
            if operation == "cancel_exception":
                live.require("identity:manage")
            a = store.get(appointment_id, None)
            replay = store.replay(actor.id, "attendance." + operation, key, signature)
            if replay:
                return replay
            if a.version != version:
                raise BusinessError("STALE_VERSION", 409)
            now = self.clock()
            if operation == "note":
                result = replace(a, version=a.version + 1, updated_at=now)
                store.add_note(Note(a.id, actor.id, body.strip(), visibility, now))
            elif operation == "extend":
                if (
                    until is None
                    or operation not in actions(a, now, False)
                    or until <= max(a.capacity_end, now)
                    or until > a.ends_at + timedelta(hours=8)
                ):
                    raise BusinessError("INVALID_EXTENSION", 409)
                resources = {r.id: r for r in store.resources()}
                resource = resources.get(resource_id or a.resource_id)
                workers = {w.id for w in store.workers()}
                occupied_end = until + timedelta(minutes=a.offer.buffer_after_minutes)
                if (
                    resource is None
                    or not resource.active
                    or resource.user_id not in workers
                    or a.service_id not in resource.service_ids
                    or not fits(store.configuration(), resource, a.occupied_start_at, occupied_end)
                ):
                    raise BusinessError("EXTENSION_UNAVAILABLE", 409)
                others = store.appointments(a.occupied_start_at, occupied_end)
                if a.status == "IN_PROGRESS" and any(
                    b.id != a.id and b.resource_id == resource.id and b.status == "IN_PROGRESS"
                    for b in others
                ):
                    raise BusinessError("RESOURCE_IN_PROGRESS", 409)
                if any(
                    b.id != a.id
                    and (
                        (
                            b.resource_id == resource.id
                            and overlaps(
                                a.occupied_start_at,
                                occupied_end,
                                b.occupied_start_at,
                                b.occupied_end_at,
                            )
                        )
                        or (
                            b.pet_id == a.pet_id
                            and overlaps(a.starts_at, until, b.starts_at, b.capacity_end)
                        )
                    )
                    for b in others
                ):
                    raise BusinessError("EXTENSION_UNAVAILABLE", 409)
                result = replace(
                    a,
                    resource_id=resource.id,
                    reserved_until=until,
                    occupied_end_at=occupied_end,
                    version=a.version + 1,
                    updated_at=now,
                )
                if resource.id != a.resource_id:
                    store.add_note(
                        Note(
                            a.id,
                            actor.id,
                            f"Pessoa responsável alterada de {resources[a.resource_id].name} para {resource.name}. Motivo: {reason.strip()}",
                            "INTERNAL",
                            now,
                        )
                    )
            else:
                result = transition(a, operation, now, "identity:manage" in live.permissions)
                if operation == "start":
                    resource = next(r for r in store.resources() if r.id == a.resource_id)
                    if (
                        not resource.active
                        or resource.user_id not in {w.id for w in store.workers()}
                        or a.service_id not in resource.service_ids
                    ):
                        raise BusinessError("INVALID_WORKER", 409)
                    if any(
                        b.id != a.id
                        and b.resource_id == a.resource_id
                        and b.status == "IN_PROGRESS"
                        for b in store.appointments(a.starts_at, a.occupied_end_at)
                    ):
                        raise BusinessError("RESOURCE_IN_PROGRESS", 409)
                if operation == "complete" and body.strip():
                    store.add_note(Note(a.id, actor.id, body.strip(), "PUBLIC", now))
            store.save(result)
            # Text of internal notes is kept exclusively in the protected table.
            kind = (
                ("note_internal" if visibility == "INTERNAL" else "note_public")
                if operation == "note"
                else operation
            )
            store.record(
                Event(
                    a.id,
                    actor.id,
                    kind,
                    "" if operation == "note" else reason.strip(),
                    result.starts_at,
                    result.capacity_end,
                    now,
                ),
                result,
                request_id,
            )
            store.remember(actor.id, "attendance." + operation, key, signature, result)
            return result

    def metrics(self, actor: Actor, first: date, last: date) -> Metrics:
        with self.store() as store:
            store.actor(actor.id).require("reporting:read")
            store.lock()
            config = store.configuration()
            start, end = self.interval(config.timezone, first, last)
            rows = store.period_appointments(start, end)
            cohort = [a for a in rows if start <= a.starts_at < end]
            workers = {w.id for w in store.workers()}
            capacity = available_minutes(
                config, [r for r in store.resources() if r.user_id in workers], start, end
            )
            occupied = sum(
                max(
                    0,
                    (min(end, a.occupied_end_at) - max(start, a.occupied_start_at)).total_seconds()
                    / 60,
                )
                for a in rows
                if a.status in OCCUPYING
            )
            counts = Counter(a.status for a in cohort)
            return Metrics(
                first,
                last,
                config.timezone,
                self.clock(),
                len(cohort),
                {state: counts[state] for state in sorted(STATUSES)},
                dict(Counter(a.offer.service_name for a in cohort)),
                occupied,
                capacity,
                round(100 * occupied / capacity, 2) if capacity else None,
            )
