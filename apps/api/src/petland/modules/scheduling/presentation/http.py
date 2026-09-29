from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request

from petland.modules.identity.public import Actor
from petland.modules.identity.public.http import HttpIdentity
from petland.modules.scheduling.application.operations import Agenda, Metrics, OperationDetail
from petland.modules.scheduling.application.service import Scheduling
from petland.modules.scheduling.domain.models import Appointment, Availability, Resource
from petland.modules.scheduling.domain.operations import AppointmentFilter
from petland.modules.scheduling.presentation.schemas import (
    AgendaResponse,
    AppointmentPage,
    AppointmentResponse,
    AssistedBookingInput,
    AttendanceInput,
    AvailabilityResponse,
    BookingInput,
    ChangeInput,
    ConfigurationInput,
    DetailResponse,
    EstablishmentResponse,
    EventResponse,
    ExtensionInput,
    ImpactResponse,
    MetricsResponse,
    NoteInput,
    OperationDetailResponse,
    PublicNoteResponse,
    RescheduleInput,
    ResourceInput,
    ResourceResponse,
    SettingsResponse,
    WorkerResponse,
)
from petland.shared.domain.errors import BusinessError


def scheduling_router(service: Scheduling, auth: HttpIdentity) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1", tags=["scheduling"], dependencies=[Depends(auth.csrf_guard)]
    )
    User = Annotated[Actor, Depends(auth.actor)]
    Key = Annotated[UUID, Header(alias="Idempotency-Key")]

    @router.get("/establishment", response_model=EstablishmentResponse)
    def establishment() -> EstablishmentResponse:
        return EstablishmentResponse.model_validate(service.establishment())

    @router.get("/operations/agenda", response_model=AgendaResponse)
    def agenda(
        actor: User,
        date_from: date | None = None,
        date_to: date | None = None,
        status: Literal["BOOKED", "ARRIVED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"]
        | None = None,
        resource_id: UUID | None = None,
        search: str = Query(default="", max_length=100),
        offset: int = Query(default=0, ge=0, le=100000),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> Agenda:
        return service.operations.agenda(
            actor,
            date_from,
            date_to,
            AppointmentFilter(status=status, resource_id=resource_id, search=search.strip()),
            offset,
            limit,
        )

    @router.get("/operations/attendances/{appointment_id}", response_model=OperationDetailResponse)
    def attendance(appointment_id: UUID, actor: User) -> OperationDetail:
        return service.operations.detail(actor, appointment_id)

    @router.post(
        "/operations/attendances/{appointment_id}/transitions", response_model=AppointmentResponse
    )
    def transition(
        appointment_id: UUID, body: AttendanceInput, actor: User, key: Key, request: Request
    ) -> Appointment:
        if body.summary and body.operation != "complete":
            raise BusinessError("INVALID_BOOKING", 422)
        return service.operations.command(
            actor,
            appointment_id,
            body.operation,
            body.version,
            key,
            request.state.request_id,
            reason=body.reason,
            body=body.summary,
        )

    @router.post(
        "/operations/attendances/{appointment_id}/notes", response_model=AppointmentResponse
    )
    def note(
        appointment_id: UUID, body: NoteInput, actor: User, key: Key, request: Request
    ) -> Appointment:
        return service.operations.command(
            actor,
            appointment_id,
            "note",
            body.version,
            key,
            request.state.request_id,
            body=body.body,
            visibility=body.visibility,
        )

    @router.post(
        "/operations/attendances/{appointment_id}/extensions", response_model=AppointmentResponse
    )
    def extend(
        appointment_id: UUID, body: ExtensionInput, actor: User, key: Key, request: Request
    ) -> Appointment:
        return service.operations.command(
            actor,
            appointment_id,
            "extend",
            body.version,
            key,
            request.state.request_id,
            reason=body.reason,
            until=body.until,
            resource_id=body.resource_id,
        )

    @router.get("/management/metrics", response_model=MetricsResponse)
    def metrics(actor: User, date_from: date, date_to: date) -> Metrics:
        return service.operations.metrics(actor, date_from, date_to)

    @router.get("/operations/calendar", response_model=SettingsResponse)
    def settings(actor: User) -> SettingsResponse:
        config, resources, workers = service.settings(actor)
        return SettingsResponse(
            configuration=ConfigurationInput.model_validate(config),
            resources=[ResourceResponse.model_validate(r) for r in resources],
            workers=[WorkerResponse.model_validate(w) for w in workers],
        )

    @router.put("/operations/calendar", response_model=SettingsResponse)
    def configure(body: ConfigurationInput, actor: User, request: Request) -> SettingsResponse:
        service.configure(actor, body.value(), request.state.request_id)
        return settings(actor)

    @router.post("/operations/calendar/impact-preview", response_model=ImpactResponse)
    def preview(body: ConfigurationInput, actor: User, request: Request) -> ImpactResponse:
        return ImpactResponse(
            appointment_ids=service.configure(
                actor, body.value(), request.state.request_id, preview=True
            )
        )

    @router.post("/operations/resources", response_model=ResourceResponse, status_code=201)
    def create_resource(body: ResourceInput, actor: User, request: Request) -> Resource:
        return service.resource(actor, body.value(), request.state.request_id)

    @router.put("/operations/resources/{resource_id}", response_model=ResourceResponse)
    def update_resource(
        resource_id: UUID, body: ResourceInput, actor: User, request: Request
    ) -> Resource:
        return service.resource(actor, body.value(), request.state.request_id, resource_id)

    @router.get("/me/availability", response_model=AvailabilityResponse)
    def own_availability(
        actor: User,
        pet_id: UUID,
        service_id: UUID,
        date: date,
        appointment_id: UUID | None = None,
    ) -> Availability:
        return service.availability(actor, None, pet_id, service_id, date, appointment_id)

    @router.get("/operations/availability", response_model=AvailabilityResponse)
    def assisted_availability(
        actor: User,
        customer_id: UUID,
        pet_id: UUID,
        service_id: UUID,
        date: date,
        appointment_id: UUID | None = None,
    ) -> Availability:
        return service.availability(actor, customer_id, pet_id, service_id, date, appointment_id)

    @router.post("/me/appointments", response_model=AppointmentResponse, status_code=201)
    def book(body: BookingInput, actor: User, key: Key, request: Request) -> Appointment:
        return service.command(
            actor, None, "book", key, request.state.request_id, **body.model_dump()
        )

    @router.post("/operations/appointments", response_model=AppointmentResponse, status_code=201)
    def assist(body: AssistedBookingInput, actor: User, key: Key, request: Request) -> Appointment:
        return service.command(
            actor,
            body.customer_id,
            "book",
            key,
            request.state.request_id,
            assisted=True,
            **body.model_dump(exclude={"customer_id"}),
        )

    def account_routes(prefix: str, assisted: bool) -> None:
        @router.get(prefix, response_model=AppointmentPage)
        def list_appointments(
            actor: User,
            customer_id: UUID | None = None,
            offset: int = Query(default=0, ge=0),
            limit: int = Query(default=20, ge=1, le=100),
            pet_id: UUID | None = None,
            status: Literal["BOOKED", "ARRIVED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"]
            | None = None,
            period: Literal["all", "upcoming", "history"] = "all",
        ) -> AppointmentPage:
            if customer_id and not assisted:
                raise BusinessError("FORBIDDEN", 403)
            items, total = service.appointments_page(
                actor,
                assisted,
                customer_id,
                offset,
                limit,
                AppointmentFilter(pet_id=pet_id, status=status, period=period, now=service.clock()),
            )
            return AppointmentPage(
                items=[AppointmentResponse.model_validate(b) for b in items], total=total
            )

        @router.get(prefix + "/{appointment_id}", response_model=DetailResponse)
        def detail(appointment_id: UUID, actor: User) -> DetailResponse:
            appointment, events = service.detail(actor, assisted, appointment_id)
            return DetailResponse(
                appointment=AppointmentResponse.model_validate(appointment),
                events=[EventResponse.model_validate(e) for e in events],
                summaries=[
                    PublicNoteResponse.model_validate(n)
                    for n in service.public_notes(actor, assisted, appointment_id)
                ],
            )

        @router.post(prefix + "/{appointment_id}/cancel", response_model=AppointmentResponse)
        def cancel(
            appointment_id: UUID, body: ChangeInput, actor: User, key: Key, request: Request
        ) -> Appointment:
            return service.command(
                actor,
                None,
                "cancel",
                key,
                request.state.request_id,
                appointment_id=appointment_id,
                assisted=assisted,
                **body.model_dump(),
            )

        @router.post(prefix + "/{appointment_id}/reschedule", response_model=AppointmentResponse)
        def reschedule(
            appointment_id: UUID, body: RescheduleInput, actor: User, key: Key, request: Request
        ) -> Appointment:
            return service.command(
                actor,
                None,
                "reschedule",
                key,
                request.state.request_id,
                appointment_id=appointment_id,
                assisted=assisted,
                **body.model_dump(),
            )

    account_routes("/me/appointments", False)
    account_routes("/operations/appointments", True)
    return router
