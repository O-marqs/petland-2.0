from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from petland.modules.identity.domain.models import User
from petland.modules.identity.infrastructure.models import RoleRecord, UserRecord
from petland.shared.domain.errors import BusinessError


def current_actor(session: Session, user_id: UUID) -> User:
    row = session.get(UserRecord, user_id)
    if row is None:
        raise BusinessError("AUTH_REQUIRED", 401)
    from petland.modules.identity.domain.models import Role

    roles = session.scalars(select(RoleRecord.role).where(RoleRecord.user_id == row.id))
    return User(
        row.email,
        row.display_name,
        row.password_hash,
        frozenset(Role(r) for r in roles),
        row.created_at,
        row.id,
        row.status,
        row.email_verified_at,
        row.version,
    )


def eligible_workers(session: Session) -> list[tuple[UUID, str]]:
    return [
        (r.id, r.display_name)
        for r in session.scalars(
            select(UserRecord)
            .where(
                UserRecord.status == "ACTIVE",
                UserRecord.email_verified_at.is_not(None),
                UserRecord.id.in_(
                    select(RoleRecord.user_id).where(RoleRecord.role.in_(["EMPLOYEE", "ADMIN"]))
                ),
            )
            .order_by(UserRecord.display_name, UserRecord.id)
        )
    ]
