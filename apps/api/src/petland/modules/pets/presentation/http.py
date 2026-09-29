from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from petland.modules.identity.public import Actor
from petland.modules.identity.public.http import HttpIdentity
from petland.modules.pets.application.service import PetData, Pets
from petland.modules.pets.domain.models import Breed, Pet, Sex, Size, Species


class PetInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    species_id: str = Field(min_length=1, max_length=16)
    breed_id: UUID | None = None
    size: Size
    sex: Sex = Sex.UNKNOWN
    birth_date: date | None = None
    birth_estimated: bool = False
    care_notes: str = Field(default="", max_length=1000)

    def data(self) -> PetData:
        return PetData(**self.model_dump())


class PetUpdate(PetInput):
    version: int = Field(ge=1)

    def data(self) -> PetData:
        return PetData(**self.model_dump(exclude={"version"}))


class PetArchive(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(ge=1)
    archived: bool


class PetResponse(PetInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_id: UUID
    version: int
    archived_at: datetime | None


class PetPage(BaseModel):
    items: list[PetResponse]
    total: int


def pet_router(service: Pets, auth: HttpIdentity) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["pets"], dependencies=[Depends(auth.csrf_guard)])
    User = Annotated[Actor, Depends(auth.actor)]

    @router.get("/catalog/species", response_model=list[Species])
    def species() -> list[Species]:
        return service.species()

    @router.get("/catalog/breeds", response_model=list[Breed])
    def breeds(species_id: str = Query(max_length=16)) -> list[Breed]:
        return service.breeds(species_id)

    @router.get("/me/pets", response_model=PetPage)
    def own_list(
        actor: User,
        archived: bool = False,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> PetPage:
        items, total = service.list(actor, None, archived, offset, limit)
        return PetPage(items=[PetResponse.model_validate(p) for p in items], total=total)

    @router.get("/me/pets/{pet_id}", response_model=PetResponse)
    def own_get(pet_id: UUID, actor: User) -> Pet:
        return service.get(actor, None, pet_id)

    @router.post("/me/pets", response_model=PetResponse, status_code=201)
    def own_create(body: PetInput, actor: User, request: Request) -> Pet:
        return service.save(actor, None, body.data(), request.state.request_id)

    @router.put("/me/pets/{pet_id}", response_model=PetResponse)
    def own_update(pet_id: UUID, body: PetUpdate, actor: User, request: Request) -> Pet:
        return service.save(
            actor, None, body.data(), request.state.request_id, pet_id, body.version
        )

    @router.patch("/me/pets/{pet_id}/archive", response_model=PetResponse)
    def own_archive(pet_id: UUID, body: PetArchive, actor: User, request: Request) -> Pet:
        return service.archive(
            actor, None, pet_id, body.archived, body.version, request.state.request_id
        )

    @router.get("/operations/customers/{customer_id}/pets", response_model=PetPage)
    def assisted_list(
        customer_id: UUID,
        actor: User,
        archived: bool = False,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> PetPage:
        items, total = service.list(actor, customer_id, archived, offset, limit)
        return PetPage(items=[PetResponse.model_validate(p) for p in items], total=total)

    @router.get("/operations/customers/{customer_id}/pets/{pet_id}", response_model=PetResponse)
    def assisted_get(customer_id: UUID, pet_id: UUID, actor: User) -> Pet:
        return service.get(actor, customer_id, pet_id)

    @router.post(
        "/operations/customers/{customer_id}/pets", response_model=PetResponse, status_code=201
    )
    def assisted_create(customer_id: UUID, body: PetInput, actor: User, request: Request) -> Pet:
        return service.save(actor, customer_id, body.data(), request.state.request_id)

    @router.put("/operations/customers/{customer_id}/pets/{pet_id}", response_model=PetResponse)
    def assisted_update(
        customer_id: UUID, pet_id: UUID, body: PetUpdate, actor: User, request: Request
    ) -> Pet:
        return service.save(
            actor, customer_id, body.data(), request.state.request_id, pet_id, body.version
        )

    @router.patch(
        "/operations/customers/{customer_id}/pets/{pet_id}/archive", response_model=PetResponse
    )
    def assisted_archive(
        customer_id: UUID, pet_id: UUID, body: PetArchive, actor: User, request: Request
    ) -> Pet:
        return service.archive(
            actor, customer_id, pet_id, body.archived, body.version, request.state.request_id
        )

    return router
