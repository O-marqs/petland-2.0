from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from petland.modules.scheduling.domain.models import (
    Appointment,
    Configuration,
    Resource,
    local_instant,
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


def available_minutes(
    config: Configuration, resources: list[Resource], start: datetime, end: datetime
) -> float:
    """Capacity of current configuration, clipped to the requested absolute interval."""
    if not config.enabled:
        return 0
    zone = ZoneInfo(config.timezone)
    day = start.astimezone(zone).date()
    minutes = 0.0
    while day <= end.astimezone(zone).date():
        shop = config.calendar.windows(day)
        for resource in resources:
            if not resource.active or not resource.service_ids:
                continue
            own = shop if resource.calendar is None else resource.calendar.windows(day)
            for left in shop:
                for right in own:
                    lo, hi = max(left.start, right.start), min(left.end, right.end)
                    if lo >= hi:
                        continue
                    begin, finish = local_instant(day, lo, zone), local_instant(day, hi, zone)
                    if begin is not None and finish is not None:
                        minutes += max(
                            0, (min(finish, end) - max(begin, start)).total_seconds() / 60
                        )
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
