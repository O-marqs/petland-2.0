from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from petland.modules.scheduling.domain.models import (
    Calendar,
    Configuration,
    Day,
    ExceptionDay,
    Resource,
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
    status: Literal["BOOKED", "CANCELLED"]
    version: int
    created_at: datetime
    updated_at: datetime


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


class AppointmentPage(Input):
    items: list[AppointmentResponse]
    total: int
