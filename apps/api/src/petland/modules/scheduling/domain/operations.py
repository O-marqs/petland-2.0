from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from petland.modules.scheduling.domain.models import (
    Appointment,
    Configuration,
    Resource,
    Window,
    local_instant,
    worker_windows,
)
from petland.shared.domain.errors import BusinessError


@dataclass
class Note:
    appointment_id: UUID
    actor_id: UUID
    body: str
    visibility: str
    occurred_at: datetime
    id: UUID = field(default_factory=uuid4)


@dataclass
class CareContext:
    customer_name: str
    phone: str
    email: str
    pet_name: str
    species: str
    care_notes: str
    allergies: str = ""
    handling_notes: str = ""
    pet_version: int = 1


@dataclass
class PreviousCare:
    appointment_id: UUID
    service_name: str
    resource_name: str
    completed_at: datetime
    actual_minutes: float | None
    notes: list[Note]


@dataclass
class Communication:
    id: UUID
    kind: str
    created_at: datetime
    available_at: datetime
    delivered_at: datetime | None
    attempts: int
    suppressed_at: datetime | None


@dataclass
class StaffMetric:
    resource_id: UUID
    name: str
    total: int
    completed: int
    cancelled: int
    no_show: int
    average_actual_minutes: float | None
    average_delay_minutes: float | None
    average_deviation_minutes: float | None
    occupied_minutes: float
    by_service: dict[str, int] = field(default_factory=dict)
    available_minutes: float = 0


@dataclass
class ServiceMetric:
    service_id: UUID
    name: str
    total: int
    completed: int
    average_planned_minutes: float | None
    average_actual_minutes: float | None


@dataclass
class Analytics:
    staff: list[StaffMetric]
    services: list[ServiceMetric]
    completed_pets: int
    completed_customers: int


@dataclass
class RosterRow:
    resource_id: UUID
    name: str
    windows: list[Window]


@dataclass
class Roster:
    date: date
    version: int
    timezone: str
    custom: bool
    reason: str
    rows: list[RosterRow]


def actions(a: Appointment, now: datetime, admin: bool) -> list[str]:
    result: list[str] = []
    if a.status == "BOOKED":
        if (
            now.astimezone(ZoneInfo(a.timezone)).date()
            == a.starts_at.astimezone(ZoneInfo(a.timezone)).date()
        ):
            result.append("arrive")
        if now >= a.starts_at + timedelta(minutes=a.no_show_grace_minutes):
            result.append("no_show")
        if admin:
            result.append("cancel_exception")
    if a.status == "ARRIVED":
        if a.starts_at <= now < a.capacity_end:
            result.append("start")
        if admin:
            result.append("cancel_exception")
    if a.status == "IN_PROGRESS":
        result.append("complete")
    if a.status in {"ARRIVED", "IN_PROGRESS"}:
        result.append("extend")
    if a.status in {"BOOKED", "ARRIVED", "IN_PROGRESS"}:
        result.append("transfer")
    return result


def transition(a: Appointment, operation: str, now: datetime, admin: bool) -> Appointment:
    if operation not in actions(a, now, admin):
        raise BusinessError("INVALID_TRANSITION", 409)
    # Real instants are server-owned; they never rewrite the agreed appointment times.
    if operation == "arrive":
        return replace(a, status="ARRIVED", arrived_at=now, version=a.version + 1, updated_at=now)
    if operation == "start":
        if a.arrived_at is None or now < a.arrived_at:
            raise BusinessError("INVALID_TRANSITION", 409)
        return replace(
            a, status="IN_PROGRESS", started_at=now, version=a.version + 1, updated_at=now
        )
    if operation == "complete":
        if a.started_at is None or now < a.started_at:
            raise BusinessError("INVALID_TRANSITION", 409)
        return replace(
            a, status="COMPLETED", completed_at=now, version=a.version + 1, updated_at=now
        )
    if operation in {"no_show", "cancel_exception"}:
        return replace(
            a,
            status="NO_SHOW" if operation == "no_show" else "CANCELLED",
            version=a.version + 1,
            updated_at=now,
        )
    raise BusinessError("INVALID_TRANSITION", 409)


def available_minutes_by_resource(
    config: Configuration, resources: list[Resource], start: datetime, end: datetime
) -> dict[UUID, float]:
    """Capacity of current configuration, clipped to the requested absolute interval."""
    minutes = {r.id: 0.0 for r in resources}
    if not config.enabled:
        return minutes
    zone = ZoneInfo(config.timezone)
    day = start.astimezone(zone).date()
    last = end.astimezone(zone).date()
    while day <= last:
        shop = config.calendar.windows(day)
        periods: dict[tuple[int, int], float] = {}
        for resource in resources:
            if not resource.active or not resource.service_ids:
                continue
            own = worker_windows(config, resource, day)
            for left in shop:
                for right in own:
                    lo, hi = max(left.start, right.start), min(left.end, right.end)
                    if lo >= hi:
                        continue
                    key = (lo, hi)
                    if key not in periods:
                        begin, finish = local_instant(day, lo, zone), local_instant(day, hi, zone)
                        periods[key] = (
                            max(0, (min(finish, end) - max(begin, start)).total_seconds() / 60)
                            if begin is not None and finish is not None
                            else 0.0
                        )
                    minutes[resource.id] += periods[key]
        day += timedelta(days=1)
    return minutes


@dataclass
class AppointmentFilter:
    start: datetime | None = None
    end: datetime | None = None
    status: str | None = None
    pet_id: UUID | None = None
    resource_id: UUID | None = None
    search: str = ""
    period: str = "all"
    now: datetime | None = None
