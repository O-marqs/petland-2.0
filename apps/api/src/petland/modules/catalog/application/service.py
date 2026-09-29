from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from uuid import UUID

from petland.modules.catalog.application.ports import CatalogStore
from petland.modules.catalog.domain.models import Option, Service
from petland.modules.identity.public import Actor
from petland.modules.pets.public import Size
from petland.shared.domain.errors import BusinessError


class Catalog:
    def __init__(self, store: Callable[[], AbstractContextManager[CatalogStore]]) -> None:
        self.store = store

    def search(
        self,
        actor: Actor | None,
        species_id: str | None,
        size: Size | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Service], int]:
        if actor:
            actor.require("catalog:manage")
        with self.store() as store:
            return store.list(actor is None, species_id, size, offset, limit)

    def get(self, actor: Actor | None, service_id: UUID) -> Service:
        if actor:
            actor.require("catalog:manage")
        with self.store() as store:
            service = store.get(service_id)
            if actor is None and not service.active:
                raise BusinessError("NOT_FOUND", 404)
            return service

    def save(
        self,
        actor: Actor,
        name: str,
        description: str,
        species_ids: list[str],
        options: list[Option],
        active: bool,
        request_id: str,
        service_id: UUID | None = None,
        version: int | None = None,
    ) -> Service:
        actor.require("catalog:manage")
        now = datetime.now(UTC)
        service = Service(name, description, species_ids, options, active, now, now)
        service.validate()
        with self.store() as store:
            store.authorize_write(actor.id)
            if not store.species_exist(species_ids):
                raise BusinessError("INVALID_REFERENCE", 422)
            if service_id:
                previous = store.get(service_id, lock=True)
                if previous.version != version:
                    raise BusinessError("STALE_VERSION", 409)
                service.id, service.created_at = previous.id, previous.created_at
                service.version = previous.version + 1
            store.save(service)
            store.audit(
                actor.id,
                service.id,
                "service.updated" if service_id else "service.created",
                request_id,
            )
            return service
