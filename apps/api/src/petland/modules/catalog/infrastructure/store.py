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
from petland.modules.identity.public.workforce import current_actor
from petland.modules.pets.public import Size
from petland.modules.pets.public.references import species_exist
from petland.modules.scheduling.public.coordination import lock_schedule
from petland.shared.domain.errors import BusinessError


class PostgresCatalog:
    def __init__(self, session: Session) -> None:
        self.session = session

    def species_exist(self, species_ids: list[str]) -> bool:
        return species_exist(self.session, species_ids)

    def authorize_write(self, actor_id: UUID) -> None:
        lock_schedule(self.session)
        current_actor(self.session, actor_id).require("catalog:manage")

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
                Option(
                    Size(option.size),
                    option.price,
                    option.duration_minutes,
                    option.buffer_before_minutes,
                    option.buffer_after_minutes,
                )
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
        if lock:
            lock_schedule(self.session)
        rows = self.session.execute(
            select(ServiceRecord, OptionRecord, ServiceSpeciesRecord.species_id)
            .outerjoin(OptionRecord)
            .outerjoin(ServiceSpeciesRecord)
            .where(ServiceRecord.id == service_id)
            .order_by(OptionRecord.size, ServiceSpeciesRecord.species_id)
            .with_for_update(read=not lock, of=ServiceRecord)
        ).all()
        if not rows:
            raise BusinessError("NOT_FOUND", 404)
        row = rows[0][0]
        options = {
            option.size: Option(
                Size(option.size),
                option.price,
                option.duration_minutes,
                option.buffer_before_minutes,
                option.buffer_after_minutes,
            )
            for _, option, _ in rows
            if option is not None
        }
        return Service(
            row.name,
            row.description,
            sorted({species for _, _, species in rows if species is not None}),
            list(options.values()),
            row.active,
            row.created_at,
            row.updated_at,
            row.id,
            row.version,
        )

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
                    buffer_before_minutes=o.buffer_before_minutes,
                    buffer_after_minutes=o.buffer_after_minutes,
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
