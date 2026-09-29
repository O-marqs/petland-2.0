from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from petland.shared.domain.errors import BusinessError


@dataclass
class Window:
    start: int
    end: int

    def validate(self) -> None:
        if not 0 <= self.start < self.end <= 1440:
            raise BusinessError("INVALID_CALENDAR", 422)


@dataclass
class Day:
    weekday: int
    windows: list[Window]


@dataclass
class ExceptionDay:
    date: date
    windows: list[Window]


@dataclass
class Calendar:
    weekly: list[Day] = field(default_factory=list)
    exceptions: list[ExceptionDay] = field(default_factory=list)

    def validate(self) -> None:
        if (
            len(self.weekly) > 7
            or len({d.weekday for d in self.weekly}) != len(self.weekly)
            or any(not 0 <= d.weekday <= 6 for d in self.weekly)
            or len(self.exceptions) > 100
            or len({d.date for d in self.exceptions}) != len(self.exceptions)
        ):
            raise BusinessError("INVALID_CALENDAR", 422)
        days: list[Day | ExceptionDay] = [*self.weekly, *self.exceptions]
        for day in days:
            windows = sorted(day.windows, key=lambda w: w.start)
            if len(windows) > 4:
                raise BusinessError("INVALID_CALENDAR", 422)
            for i, window in enumerate(windows):
                window.validate()
                if i and windows[i - 1].end > window.start:
                    raise BusinessError("INVALID_CALENDAR", 422)

    def windows(self, day: date) -> list[Window]:
        exception = next((d for d in self.exceptions if d.date == day), None)
        if exception is not None:
            return exception.windows
        return next((d.windows for d in self.weekly if d.weekday == day.weekday()), [])


@dataclass
class Configuration:
    timezone: str = "America/Sao_Paulo"
    enabled: bool = False
    lead_minutes: int = 0
    horizon_days: int = 1
    step_minutes: int = 15
    change_cutoff_minutes: int = 0
    calendar: Calendar = field(default_factory=Calendar)
    version: int = 1
    no_show_grace_minutes: int = 0
    shop_name: str = "PetLand"
    shop_phone: str = ""
    shop_email: str = ""
    shop_address: str = ""

    def validate(self) -> None:
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise BusinessError("INVALID_CALENDAR", 422) from None
        if (
            not 0 <= self.lead_minutes <= 525600
            or not 1 <= self.horizon_days <= 366
            or not 1 <= self.step_minutes <= 120
            or not 0 <= self.change_cutoff_minutes <= 525600
            or self.lead_minutes >= self.horizon_days * 1440
            or not 0 <= self.no_show_grace_minutes <= 1440
            or not 1 <= len(self.shop_name.strip()) <= 100
            or len(self.shop_phone) > 30
            or len(self.shop_email) > 254
            or len(self.shop_address) > 300
        ):
            raise BusinessError("INVALID_CALENDAR", 422)
        self.calendar.validate()


@dataclass
class Worker:
    id: UUID
    name: str


@dataclass
class Resource:
    user_id: UUID
    name: str
    service_ids: list[UUID]
    active: bool = True
    calendar: Calendar | None = None
    id: UUID = field(default_factory=uuid4)
    version: int = 1

    def validate(self) -> None:
        if (
            not self.name.strip()
            or len(self.name) > 100
            or len(self.service_ids) > 100
            or len(set(self.service_ids)) != len(self.service_ids)
        ):
            raise BusinessError("INVALID_CALENDAR", 422)
        if self.calendar is not None:
            self.calendar.validate()


@dataclass
class Offer:
    service_id: UUID
    service_name: str
    pet_name: str
    size: str
    price: Decimal
    duration_minutes: int
    buffer_before_minutes: int
    buffer_after_minutes: int
    version: int


@dataclass
class Slot:
    starts_at: datetime
    ends_at: datetime


@dataclass
class Availability:
    date: date
    timezone: str
    configuration_version: int
    offer: Offer
    slots: list[Slot]
    calculated_at: datetime
    enabled: bool
    change_cutoff_minutes: int


@dataclass
class Appointment:
    customer_id: UUID
    pet_id: UUID
    service_id: UUID
    resource_id: UUID
    starts_at: datetime
    ends_at: datetime
    occupied_start_at: datetime
    occupied_end_at: datetime
    offer: Offer
    timezone: str
    change_cutoff_minutes: int
    created_at: datetime
    updated_at: datetime
    id: UUID = field(default_factory=uuid4)
    status: str = "BOOKED"
    version: int = 1
    no_show_grace_minutes: int = 0
    arrived_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reserved_until: datetime | None = None

    @property
    def capacity_end(self) -> datetime:
        return self.reserved_until or self.ends_at


@dataclass
class Event:
    appointment_id: UUID
    actor_id: UUID
    kind: str
    reason: str
    starts_at: datetime
    ends_at: datetime
    occurred_at: datetime
    id: UUID = field(default_factory=uuid4)


def overlaps(a: datetime, b: datetime, c: datetime, d: datetime) -> bool:
    return a < d and c < b


def local_instant(day: date, minute: int, zone: ZoneInfo) -> datetime | None:
    local = datetime.combine(day, time()) + timedelta(minutes=minute)
    aware = local.replace(tzinfo=zone)
    # Ambiguous/nonexistent wall times are omitted, never guessed across DST.
    if aware.utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
        return None
    utc = aware.astimezone(UTC)
    return utc if utc.astimezone(zone).replace(tzinfo=None) == local else None


def fits(config: Configuration, resource: Resource, start: datetime, end: datetime) -> bool:
    zone = ZoneInfo(config.timezone)
    day = start.astimezone(zone).date()
    shop = config.calendar.windows(day)
    worker = shop if resource.calendar is None else resource.calendar.windows(day)
    for window in shop:
        for own in worker:
            left = local_instant(day, max(window.start, own.start), zone)
            right = local_instant(day, min(window.end, own.end), zone)
            if left is not None and right is not None and left <= start < end <= right:
                return True
    return False


def candidates(config: Configuration, day: date, now: datetime) -> list[datetime]:
    if not config.enabled:
        return []
    zone = ZoneInfo(config.timezone)
    today = now.astimezone(zone).date()
    if not today <= day <= today + timedelta(days=config.horizon_days):
        return []
    return [
        instant
        for minute in range(0, 1440, config.step_minutes)
        if (instant := local_instant(day, minute, zone)) is not None
        and instant > now
        and instant >= now + timedelta(minutes=config.lead_minutes)
    ]


def allocate(
    config: Configuration,
    resources: list[Resource],
    existing: list[Appointment],
    pet_id: UUID,
    offer: Offer,
    start: datetime,
    ignore_id: UUID | None = None,
) -> Resource | None:
    end = start + timedelta(minutes=offer.duration_minutes)
    occupied_start = start - timedelta(minutes=offer.buffer_before_minutes)
    occupied_end = end + timedelta(minutes=offer.buffer_after_minutes)
    occupied = [b for b in existing if b.status in OCCUPYING and b.id != ignore_id]
    if any(
        b.pet_id == pet_id and overlaps(start, end, b.starts_at, b.capacity_end) for b in occupied
    ):
        return None
    for resource in sorted(resources, key=lambda r: str(r.id)):
        if (
            resource.active
            and offer.service_id in resource.service_ids
            and fits(config, resource, occupied_start, occupied_end)
            and not any(
                b.resource_id == resource.id
                and overlaps(occupied_start, occupied_end, b.occupied_start_at, b.occupied_end_at)
                for b in occupied
            )
        ):
            return resource
    return None


OCCUPYING = frozenset({"BOOKED", "ARRIVED", "IN_PROGRESS", "COMPLETED"})
OPEN_STATUSES = frozenset({"BOOKED", "ARRIVED", "IN_PROGRESS"})
STATUSES = OCCUPYING | {"CANCELLED", "NO_SHOW"}
