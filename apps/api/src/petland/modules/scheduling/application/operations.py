import hashlib
import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from petland.modules.identity.public import Actor
from petland.modules.scheduling.application.ports import ScheduleStore
from petland.modules.scheduling.domain.models import (
    STATUSES,
    Appointment,
    Configuration,
    Event,
    Resource,
    fits,
    overlaps,
    physical_fits,
)
from petland.modules.scheduling.domain.operations import (
    AppointmentFilter,
    CareContext,
    Communication,
    Note,
    PreviousCare,
    ServiceMetric,
    StaffMetric,
    actions,
    available_minutes_by_resource,
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
    previous_care: list[PreviousCare]
    communications: list[Communication]
    resources: dict[UUID, str]


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
    staff: list[StaffMetric]
    services: list[ServiceMetric]
    completed_pets: int
    completed_customers: int


@dataclass
class DayLoad:
    resource_id: UUID
    name: str
    planned: int
    completed: int
    occupied_minutes: float
    available_minutes: float


@dataclass
class DailyDashboard:
    date: date
    timezone: str
    calculated_at: datetime
    total: int
    by_status: dict[str, int]
    my_resource_id: UUID | None
    appointments: list[OperationItem]
    attention: list[OperationItem]
    staff: list[DayLoad]


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
        mine: bool = False,
    ) -> Agenda:
        with self.store() as store:
            live = store.actor(actor.id)
            live.require("operation:read")
            config, now = store.configuration(), self.clock()
            first = first or now.astimezone(ZoneInfo(config.timezone)).date()
            last = last or first
            start, end = self.interval(config.timezone, first, last)
            if mine:
                own = next((r for r in store.resources() if r.user_id == actor.id), None)
                if own is None:
                    return Agenda([], 0, first, last, config.timezone, now)
                filters = replace(filters, resource_id=own.id)
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
                store.previous_care(a),
                store.communications(a.id),
                resources,
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
        care_version: int | None = None,
    ) -> Appointment:
        if operation not in {
            "arrive",
            "start",
            "complete",
            "no_show",
            "cancel_exception",
            "note",
            "extend",
            "transfer",
        }:
            raise BusinessError("INVALID_TRANSITION", 422)
        if len(reason) > 500 or len(body) > 2000 or visibility not in {"INTERNAL", "PUBLIC"}:
            raise BusinessError("INVALID_BOOKING", 422)
        if (
            operation in {"no_show", "cancel_exception", "extend", "transfer"}
            and not reason.strip()
        ):
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
                + ([care_version] if care_version is not None else [])
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
            elif operation in {"extend", "transfer"}:
                if operation == "transfer":
                    if (
                        operation not in actions(a, now, False)
                        or resource_id is None
                        or resource_id == a.resource_id
                    ):
                        raise BusinessError("INVALID_TRANSFER", 409)
                    until = a.capacity_end
                if until is None or (
                    operation == "extend"
                    and (
                        operation not in actions(a, now, False)
                        or until <= max(a.capacity_end, now)
                        or until > a.ends_at + timedelta(hours=8)
                    )
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
                if not physical_fits(
                    store.configuration(),
                    others,
                    a.service_id,
                    a.occupied_start_at,
                    occupied_end,
                    a.id,
                ):
                    raise BusinessError("CAPACITY_UNAVAILABLE", 409)
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
                    reserved_until=until if operation == "extend" else a.reserved_until,
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
                    context = store.context(a)
                    if context.allergies.strip() and care_version != context.pet_version:
                        raise BusinessError("PET_CARE_ACK_REQUIRED", 409)
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
                    if context.allergies.strip():
                        store.add_note(
                            Note(
                                a.id,
                                actor.id,
                                f"Alerta crítico revisado antes do início. Versão do pet: {context.pet_version}.",
                                "INTERNAL",
                                now,
                            )
                        )
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
                    previous_resource_id=a.resource_id
                    if result.resource_id != a.resource_id
                    else None,
                    resource_id=result.resource_id if result.resource_id != a.resource_id else None,
                ),
                result,
                request_id,
            )
            store.remember(actor.id, "attendance." + operation, key, signature, result)
            return result

    def metrics(self, actor: Actor, first: date, last: date) -> Metrics:
        with self.store() as store:
            store.actor(actor.id).require("reporting:read")
            store.lock(shared=True)
            config = store.configuration()
            start, end = self.interval(config.timezone, first, last)
            totals = store.period_totals(start, end)
            occupied = totals.occupied_minutes
            analytics = store.analytics(start, end)
            staff = self.staff_capacity(
                analytics.staff, store.resources(eligible_only=True), config, start, end
            )
            capacity = sum(row.available_minutes for row in staff)
            return Metrics(
                first,
                last,
                config.timezone,
                self.clock(),
                totals.total,
                {state: totals.by_status.get(state, 0) for state in sorted(STATUSES)},
                totals.by_service,
                occupied,
                capacity,
                round(100 * occupied / capacity, 2) if capacity else None,
                staff,
                analytics.services,
                analytics.completed_pets,
                analytics.completed_customers,
            )

    def dashboard(self, actor: Actor, day: date | None = None, mine: bool = True) -> DailyDashboard:
        with self.store() as store:
            live = store.actor(actor.id)
            live.require("operation:read")
            store.lock(shared=True)
            config, now = store.configuration(), self.clock()
            day = day or now.astimezone(ZoneInfo(config.timezone)).date()
            start, end = self.interval(config.timezone, day, day)
            resources = store.resources()
            own = next((r for r in resources if r.user_id == actor.id), None)
            rows, _ = store.appointments_page(
                None,
                0,
                6,
                AppointmentFilter(
                    start=start,
                    end=end,
                    resource_id=own.id if mine and own else None,
                    period="upcoming",
                    now=now,
                ),
            )
            if mine and own is None:
                rows = []
            attention = store.attention(start, end, now)
            names = store.customer_names(list({a.customer_id for a in [*rows, *attention]}))
            labels = {r.id: r.name for r in resources}
            totals = store.period_totals(start, end)
            analytics = store.analytics(start, end, details=False)
            staff = self.staff_capacity(
                analytics.staff, store.resources(eligible_only=True), config, start, end
            )
            return DailyDashboard(
                day,
                config.timezone,
                now,
                totals.total,
                totals.by_status,
                own.id if own else None,
                [
                    self.item(
                        a,
                        names[a.customer_id],
                        labels[a.resource_id],
                        now,
                        "identity:manage" in live.permissions,
                    )
                    for a in rows
                ],
                [
                    self.item(
                        a,
                        names[a.customer_id],
                        labels[a.resource_id],
                        now,
                        "identity:manage" in live.permissions,
                    )
                    for a in attention
                ],
                [
                    DayLoad(
                        r.resource_id,
                        r.name,
                        r.total,
                        r.completed,
                        r.occupied_minutes,
                        r.available_minutes,
                    )
                    for r in staff
                ],
            )

    @staticmethod
    def staff_capacity(
        rows: list[StaffMetric],
        resources: list[Resource],
        config: Configuration,
        start: datetime,
        end: datetime,
    ) -> list[StaffMetric]:
        by_id = {row.resource_id: row for row in rows}
        capacity = available_minutes_by_resource(config, resources, start, end)
        for resource in resources:
            row = by_id.setdefault(
                resource.id,
                StaffMetric(resource.id, resource.name, 0, 0, 0, 0, None, None, None, 0),
            )
            row.available_minutes = capacity[resource.id]
        return sorted(by_id.values(), key=lambda row: (row.name.casefold(), str(row.resource_id)))
