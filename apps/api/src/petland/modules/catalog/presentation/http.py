from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from petland.modules.catalog.application.service import Catalog
from petland.modules.catalog.domain.models import Option, Service
from petland.modules.identity.public import Actor
from petland.modules.identity.public.http import HttpIdentity
from petland.modules.pets.public import Size


class ServiceOption(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    size: Size
    price: Decimal = Field(ge=0, le=Decimal("9999999.99"), max_digits=9, decimal_places=2)
    duration_minutes: int = Field(ge=1, le=1440, strict=True)
    buffer_before_minutes: int = Field(default=0, ge=0, le=240, strict=True)
    buffer_after_minutes: int = Field(default=0, ge=0, le=240, strict=True)


class ServiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1500)
    species_ids: list[str] = Field(min_length=1, max_length=20)
    options: list[ServiceOption] = Field(min_length=1, max_length=3)
    active: bool = False


class ServiceUpdate(ServiceInput):
    version: int = Field(ge=1)


class ServiceResponse(ServiceInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    version: int
    currency: Literal["BRL"] = "BRL"


class ServicePage(BaseModel):
    items: list[ServiceResponse]
    total: int


def catalog_router(service: Catalog, auth: HttpIdentity) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["catalog"], dependencies=[Depends(auth.csrf_guard)])
    User = Annotated[Actor, Depends(auth.actor)]

    @router.get("/catalog/services", response_model=ServicePage)
    def public_list(
        species_id: str | None = Query(default=None, max_length=16),
        size: Size | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> ServicePage:
        items, total = service.search(None, species_id, size, offset, limit)
        return ServicePage(items=[ServiceResponse.model_validate(s) for s in items], total=total)

    @router.get("/catalog/services/{service_id}", response_model=ServiceResponse)
    def public_get(service_id: UUID) -> Service:
        return service.get(None, service_id)

    @router.get("/operations/services", response_model=ServicePage)
    def staff_list(
        actor: User,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> ServicePage:
        items, total = service.search(actor, None, None, offset, limit)
        return ServicePage(items=[ServiceResponse.model_validate(s) for s in items], total=total)

    @router.get("/operations/services/{service_id}", response_model=ServiceResponse)
    def staff_get(service_id: UUID, actor: User) -> Service:
        return service.get(actor, service_id)

    @router.post("/operations/services", response_model=ServiceResponse, status_code=201)
    def create(body: ServiceInput, actor: User, request: Request) -> Service:
        return service.save(
            actor,
            body.name,
            body.description,
            body.species_ids,
            [Option(**o.model_dump()) for o in body.options],
            body.active,
            request.state.request_id,
        )

    @router.put("/operations/services/{service_id}", response_model=ServiceResponse)
    def update(service_id: UUID, body: ServiceUpdate, actor: User, request: Request) -> Service:
        return service.save(
            actor,
            body.name,
            body.description,
            body.species_ids,
            [Option(**o.model_dump()) for o in body.options],
            body.active,
            request.state.request_id,
            service_id,
            body.version,
        )

    return router
