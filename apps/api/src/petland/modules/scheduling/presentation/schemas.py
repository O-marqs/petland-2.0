from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from petland.modules.scheduling.domain.models import (
    Calendar,
    CapacityPool,
    Configuration,
    Day,
    ExceptionDay,
    Resource,
    StaffShift,
    Window,
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class WindowInput(Input):
    start: int = Field(ge=0, le=1439, strict=True)
    end: int = Field(ge=1, le=1440, strict=True)


class DayInput(Input):
    weekday: int = Field(ge=0, le=6, strict=True)
    windows: list[WindowInput] = Field(max_length=4)


class ExceptionInput(Input):
    date: date
    windows: list[WindowInput] = Field(max_length=4)


class CalendarInput(Input):
    weekly: list[DayInput] = Field(max_length=7)
    exceptions: list[ExceptionInput] = Field(max_length=100)

    def value(self) -> Calendar:
        return Calendar(
            [Day(d.weekday, [Window(w.start, w.end) for w in d.windows]) for d in self.weekly],
            [
                ExceptionDay(d.date, [Window(w.start, w.end) for w in d.windows])
                for d in self.exceptions
            ],
        )


class ConfigurationInput(Input):
    timezone: str = Field(min_length=1, max_length=64)
    enabled: bool
    lead_minutes: int = Field(ge=0, le=525600, strict=True)
    horizon_days: int = Field(ge=1, le=366, strict=True)
    step_minutes: int = Field(ge=1, le=120, strict=True)
    change_cutoff_minutes: int = Field(ge=0, le=525600, strict=True)
    calendar: CalendarInput
    version: int = Field(ge=1)
    no_show_grace_minutes: int = Field(default=0, ge=0, le=1440, strict=True)
    shop_name: str = Field(default="PetLand", min_length=1, max_length=100)
    shop_phone: str = Field(default="", max_length=30)
    shop_email: str = Field(default="", max_length=254)
    shop_address: str = Field(default="", max_length=300)
    reminder_minutes: int = Field(default=0, ge=0, le=10080, strict=True)

    def value(self) -> Configuration:
        return Configuration(**{**self.model_dump(), "calendar": self.calendar.value()})


class ResourceInput(Input):
    user_id: UUID
    name: str = Field(min_length=1, max_length=100)
    service_ids: list[UUID] = Field(max_length=100)
    active: bool
    calendar: CalendarInput | None = None
    version: int = Field(default=1, ge=1)

    def value(self) -> Resource:
        return Resource(
            **{**self.model_dump(), "calendar": self.calendar.value() if self.calendar else None}
        )


class ResourceResponse(ResourceInput):
    id: UUID


class WorkerResponse(Input):
    id: UUID
    name: str


class SettingsResponse(Input):
    configuration: ConfigurationInput
    resources: list[ResourceResponse]
    workers: list[WorkerResponse]


class ImpactResponse(Input):
    appointment_ids: list[UUID]


class OfferResponse(Input):
    service_id: UUID
    service_name: str
    pet_name: str
    size: str
    price: Decimal
    currency: Literal["BRL"] = "BRL"
    duration_minutes: int
    buffer_before_minutes: int
    buffer_after_minutes: int
    version: int


class SlotResponse(Input):
    starts_at: datetime
    ends_at: datetime


class AvailabilityResponse(Input):
    date: date
    timezone: str
    configuration_version: int
    offer: OfferResponse
    slots: list[SlotResponse]
    calculated_at: datetime
    enabled: bool
    change_cutoff_minutes: int


class BookingInput(Input):
    pet_id: UUID
    service_id: UUID
    starts_at: AwareDatetime
    offer_version: int = Field(ge=1)
    configuration_version: int = Field(ge=1)


class AssistedBookingInput(BookingInput):
    customer_id: UUID


class ChangeInput(Input):
    version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=500)


class RescheduleInput(ChangeInput):
    starts_at: AwareDatetime
    configuration_version: int = Field(ge=1)


class AppointmentResponse(Input):
    id: UUID
    customer_id: UUID
    pet_id: UUID
    service_id: UUID
    starts_at: datetime
    ends_at: datetime
    offer: OfferResponse
    timezone: str
    change_cutoff_minutes: int
    status: Literal["BOOKED", "ARRIVED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"]
    version: int
    created_at: datetime
    updated_at: datetime
    no_show_grace_minutes: int
    arrived_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    reserved_until: datetime | None


class EventResponse(Input):
    id: UUID
    kind: str
    reason: str
    starts_at: datetime
    ends_at: datetime
    occurred_at: datetime


class DetailResponse(Input):
    appointment: AppointmentResponse
    events: list[EventResponse]
    summaries: list["PublicNoteResponse"] = Field(default_factory=list)
    communications: list["CommunicationResponse"] = Field(default_factory=list)


class AppointmentPage(Input):
    items: list[AppointmentResponse]
    total: int


class PublicNoteResponse(Input):
    id: UUID
    body: str
    occurred_at: datetime


class NoteResponse(PublicNoteResponse):
    actor_id: UUID
    visibility: Literal["PUBLIC", "INTERNAL"]


class OperationEventResponse(EventResponse):
    actor_id: UUID
    previous_resource_id: UUID | None
    resource_id: UUID | None


class CommunicationResponse(Input):
    id: UUID
    kind: str
    created_at: datetime
    available_at: datetime
    delivered_at: datetime | None
    attempts: int
    suppressed_at: datetime | None


class PreviousCareResponse(Input):
    appointment_id: UUID
    service_name: str
    resource_name: str
    completed_at: datetime
    actual_minutes: float | None
    notes: list[NoteResponse]


class CareContextResponse(Input):
    customer_name: str
    phone: str
    email: str
    pet_name: str
    species: str
    care_notes: str
    allergies: str
    handling_notes: str
    pet_version: int


class OperationItemResponse(Input):
    appointment: AppointmentResponse
    customer_name: str
    resource_name: str
    resource_id: UUID
    allowed_actions: list[str]
    overdue: bool


class OperationDetailResponse(Input):
    item: OperationItemResponse
    context: CareContextResponse
    events: list[OperationEventResponse]
    notes: list[NoteResponse]
    authors: dict[UUID, str]
    resources: dict[UUID, str]
    previous_care: list[PreviousCareResponse]
    communications: list[CommunicationResponse]


class AgendaResponse(Input):
    items: list[OperationItemResponse]
    total: int
    date_from: date
    date_to: date
    timezone: str
    calculated_at: datetime


class AttendanceInput(Input):
    version: int = Field(ge=1, strict=True)
    operation: Literal["arrive", "start", "complete", "no_show", "cancel_exception"]
    reason: str = Field(default="", max_length=500)
    summary: str = Field(default="", max_length=2000)
    care_version: int | None = Field(default=None, ge=1, strict=True)


class NoteInput(Input):
    version: int = Field(ge=1, strict=True)
    body: str = Field(min_length=1, max_length=2000)
    visibility: Literal["INTERNAL", "PUBLIC"]


class ExtensionInput(ChangeInput):
    until: AwareDatetime
    resource_id: UUID | None = None


class TransferInput(ChangeInput):
    resource_id: UUID


class ShiftInput(Input):
    resource_id: UUID
    windows: list[WindowInput] = Field(max_length=4)

    def value(self) -> StaffShift:
        return StaffShift(self.resource_id, [Window(w.start, w.end) for w in self.windows])


class RosterInput(Input):
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=1, max_length=500)
    shifts: list[ShiftInput] | None = Field(max_length=100)


class RosterRowResponse(ShiftInput):
    name: str


class RosterResponse(Input):
    date: date
    version: int
    timezone: str
    custom: bool
    reason: str
    rows: list[RosterRowResponse]


class PoolInput(Input):
    id: UUID
    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(ge=1, le=100, strict=True)
    service_ids: list[UUID] = Field(min_length=1, max_length=100)
    active: bool

    def value(self) -> CapacityPool:
        return CapacityPool(**self.model_dump())


class PoolsInput(Input):
    version: int = Field(ge=1, strict=True)
    pools: list[PoolInput] = Field(max_length=32)


class StaffMetricResponse(Input):
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
    available_minutes: float
    by_service: dict[str, int]


class ServiceMetricResponse(Input):
    service_id: UUID
    name: str
    total: int
    completed: int
    average_planned_minutes: float | None
    average_actual_minutes: float | None


class MetricsResponse(Input):
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
    staff: list[StaffMetricResponse]
    services: list[ServiceMetricResponse]
    completed_pets: int
    completed_customers: int


class DayLoadResponse(Input):
    resource_id: UUID
    name: str
    planned: int
    completed: int
    occupied_minutes: float
    available_minutes: float


class DailyDashboardResponse(Input):
    date: date
    timezone: str
    calculated_at: datetime
    total: int
    by_status: dict[str, int]
    my_resource_id: UUID | None
    appointments: list[OperationItemResponse]
    attention: list[OperationItemResponse]
    staff: list[DayLoadResponse]


class EstablishmentResponse(Input):
    shop_name: str
    shop_phone: str
    shop_email: str
    shop_address: str
    timezone: str
