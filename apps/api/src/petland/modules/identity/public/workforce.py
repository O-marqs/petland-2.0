from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from petland.modules.identity.domain.models import User
from petland.modules.identity.infrastructure.models import RoleRecord, UserRecord
from petland.modules.identity.infrastructure.store import PostgresIdentityStore
from petland.shared.domain.errors import BusinessError


def current_actor(session: Session, user_id: UUID) -> User:
    user = PostgresIdentityStore(session).user(user_id=user_id)
    if user is None:
        raise BusinessError("AUTH_REQUIRED", 401)
    return user


def eligible_worker_ids() -> Select[tuple[UUID]]:
    return select(UserRecord.id).where(
        UserRecord.status == "ACTIVE",
        UserRecord.email_verified_at.is_not(None),
        UserRecord.id.in_(
            select(RoleRecord.user_id).where(RoleRecord.role.in_(["EMPLOYEE", "ADMIN"]))
        ),
    )


def eligible_workers(session: Session) -> list[tuple[UUID, str]]:
    return [
        (r.id, r.display_name)
        for r in session.scalars(
            select(UserRecord)
            .where(UserRecord.id.in_(eligible_worker_ids()))
            .order_by(UserRecord.display_name, UserRecord.id)
        )
    ]


def actor_names(session: Session, ids: list[UUID]) -> dict[UUID, str]:
    return dict(
        session.execute(
            select(UserRecord.id, UserRecord.display_name).where(UserRecord.id.in_(ids))
        )
        .tuples()
        .all()
    )
