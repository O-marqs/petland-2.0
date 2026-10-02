from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from petland.modules.customers.application.service import Customers
from petland.modules.customers.domain.models import Customer
from petland.modules.identity.public import Actor
from petland.modules.identity.public.http import HttpIdentity


class CustomerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(default="", max_length=25)
    address: str = Field(default="", max_length=500)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.casefold()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        if any(c not in "0123456789+() -. " for c in value):
            raise ValueError("invalid phone")
        digits = "".join(c for c in value if c.isdigit())
        if digits and not 10 <= len(digits) <= 15:
            raise ValueError("invalid phone")
        return digits


class CustomerUpdate(CustomerInput):
    version: int = Field(ge=1)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str
    phone: str
    address: str
    version: int
    linked: bool

    @classmethod
    def of(cls, value: Customer) -> "CustomerResponse":
        return cls(
            id=value.id,
            name=value.name,
            email=value.email,
            phone=value.phone,
            address=value.address,
            version=value.version,
            linked=value.user_id is not None,
        )


class CustomerPage(BaseModel):
    items: list[CustomerResponse]
    total: int


class ClaimInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=128)


class ClaimMessage(BaseModel):
    message: str = (
        "Link solicitado. O cliente deve entrar com o mesmo e-mail e confirmar o vínculo."
    )


def customer_router(service: Customers, auth: HttpIdentity) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1", tags=["customers"], dependencies=[Depends(auth.csrf_guard)]
    )
    User = Annotated[Actor, Depends(auth.actor)]

    @router.get("/me/customer", response_model=CustomerResponse | None)
    def own(actor: User) -> CustomerResponse | None:
        value = service.own(actor)
        return CustomerResponse.of(value) if value else None

    @router.post("/me/customer", response_model=CustomerResponse, status_code=201)
    def create_own(body: CustomerInput, actor: User, request: Request) -> CustomerResponse:
        return CustomerResponse.of(
            service.create(
                actor,
                body.name,
                str(body.email),
                body.phone,
                body.address,
                False,
                request.state.request_id,
            )
        )

    @router.put("/me/customer", response_model=CustomerResponse)
    def update_own(body: CustomerUpdate, actor: User, request: Request) -> CustomerResponse:
        return CustomerResponse.of(
            service.edit(
                actor,
                None,
                body.name,
                str(body.email),
                body.phone,
                body.address,
                body.version,
                request.state.request_id,
            )
        )

    @router.get("/operations/customers", response_model=CustomerPage)
    def search(
        actor: User,
        q: str = Query(default="", max_length=100),
        offset: int = Query(default=0, ge=0, le=100000),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> CustomerPage:
        items, total = service.search(actor, q.strip(), offset, limit)
        return CustomerPage(items=[CustomerResponse.of(c) for c in items], total=total)

    @router.post("/operations/customers", response_model=CustomerResponse, status_code=201)
    def create(body: CustomerInput, actor: User, request: Request) -> CustomerResponse:
        return CustomerResponse.of(
            service.create(
                actor,
                body.name,
                str(body.email),
                body.phone,
                body.address,
                True,
                request.state.request_id,
            )
        )

    @router.get("/operations/customers/{customer_id}", response_model=CustomerResponse)
    def get(customer_id: UUID, actor: User) -> CustomerResponse:
        return CustomerResponse.of(service.get(actor, customer_id))

    @router.put("/operations/customers/{customer_id}", response_model=CustomerResponse)
    def update(
        customer_id: UUID, body: CustomerUpdate, actor: User, request: Request
    ) -> CustomerResponse:
        return CustomerResponse.of(
            service.edit(
                actor,
                customer_id,
                body.name,
                str(body.email),
                body.phone,
                body.address,
                body.version,
                request.state.request_id,
            )
        )

    @router.post(
        "/operations/customers/{customer_id}/claim-invitations",
        response_model=ClaimMessage,
        status_code=202,
    )
    def invite(customer_id: UUID, actor: User, request: Request) -> ClaimMessage:
        actor.require("customer:assist")
        auth.sensitive_limit(request, actor)
        service.invite(actor, customer_id, request.state.request_id)
        return ClaimMessage()

    @router.post("/me/customer-claims", response_model=CustomerResponse)
    def accept(body: ClaimInput, actor: User, request: Request) -> CustomerResponse:
        actor.require("customer:own")
        auth.sensitive_limit(request, actor)
        return CustomerResponse.of(service.accept(actor, body.token, request.state.request_id))

    return router
