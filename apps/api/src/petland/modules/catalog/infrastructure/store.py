from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from petland.modules.catalog.application.ports import CatalogStore
from petland.modules.catalog.domain.models import Option, Service
from petland.modules.catalog.infrastructure.models import (
    OptionRecord,
    ServiceRecord,
    ServiceSpeciesRecord,
)
from petland.modules.identity.public.audit import record
from petland.modules.pets.public import Size
from petland.modules.pets.public.references import species_exist
from petland.shared.domain.errors import BusinessError


class PostgresCatalog:
    def __init__(self, session: Session) -> None:
        self.session = session

    def species_exist(self, species_ids: list[str]) -> bool:
        return species_exist(self.session, species_ids)

    def values(self, rows: Sequence[ServiceRecord]) -> list[Service]:
        ids = [r.id for r in rows]
        species: dict[UUID, list[str]] = {id: [] for id in ids}
        options: dict[UUID, list[Option]] = {id: [] for id in ids}
        for reference in self.session.scalars(
            select(ServiceSpeciesRecord)
            .where(ServiceSpeciesRecord.service_id.in_(ids))
            .order_by(ServiceSpeciesRecord.species_id)
        ):
            species[reference.service_id].append(reference.species_id)
        for option in self.session.scalars(
            select(OptionRecord).where(OptionRecord.service_id.in_(ids)).order_by(OptionRecord.size)
        ):
            options[option.service_id].append(
                Option(Size(option.size), option.price, option.duration_minutes)
            )
        return [
            Service(
                r.name,
                r.description,
                species[r.id],
                options[r.id],
                r.active,
                r.created_at,
                r.updated_at,
                r.id,
                r.version,
            )
            for r in rows
        ]

    def get(self, service_id: UUID, lock: bool = False) -> Service:
        query = select(ServiceRecord).where(ServiceRecord.id == service_id)
        row = self.session.scalar(query.with_for_update(read=not lock))
        if not row:
            raise BusinessError("NOT_FOUND", 404)
        return self.values([row])[0]

    def list(
        self, public: bool, species_id: str | None, size: Size | None, offset: int, limit: int
    ) -> tuple[list[Service], int]:
        query = select(ServiceRecord)
        if public:
            query = query.where(ServiceRecord.active.is_(True))
        if species_id:
            query = query.where(
                ServiceRecord.id.in_(
                    select(ServiceSpeciesRecord.service_id).where(
                        ServiceSpeciesRecord.species_id == species_id
                    )
                )
            )
        if size:
            query = query.where(
                ServiceRecord.id.in_(
                    select(OptionRecord.service_id).where(OptionRecord.size == size)
                )
            )
        total = self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = self.session.scalars(
            query.order_by(ServiceRecord.name, ServiceRecord.id)
            .offset(offset)
            .limit(limit)
            .with_for_update(read=True)
        ).all()
        return self.values(rows), total or 0

    def save(self, service: Service) -> None:
        self.session.merge(
            ServiceRecord(
                id=service.id,
                name=service.name,
                description=service.description,
                active=service.active,
                created_at=service.created_at,
                updated_at=service.updated_at,
                version=service.version,
            )
        )
        self.session.flush()
        self.session.execute(delete(OptionRecord).where(OptionRecord.service_id == service.id))
        self.session.execute(
            delete(ServiceSpeciesRecord).where(ServiceSpeciesRecord.service_id == service.id)
        )
        self.session.add_all(
            [
                ServiceSpeciesRecord(service_id=service.id, species_id=id)
                for id in service.species_ids
            ]
        )
        self.session.add_all(
            [
                OptionRecord(
                    service_id=service.id,
                    size=o.size,
                    price=o.price,
                    duration_minutes=o.duration_minutes,
                )
                for o in service.options
            ]
        )
        self.session.flush()

    def audit(self, actor: UUID, target: UUID, action: str, request_id: str) -> None:
        record(self.session, actor, target, action, request_id)


@contextmanager
def catalog_store(engine: Engine) -> Iterator[CatalogStore]:
    with Session(engine) as session, session.begin():
        yield PostgresCatalog(session)
