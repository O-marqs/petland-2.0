from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from petland.modules.identity.infrastructure.models import AuditRecord


def record(session: Session, actor: UUID, target: UUID, action: str, request_id: str) -> None:
    """Append a safe event in the caller's transaction. Never accept free-form payloads."""
    session.add(
        AuditRecord(
            id=uuid4(),
            actor_user_id=actor,
            target_id=target,
            action=action,
            occurred_at=datetime.now(UTC),
            request_id=request_id,
            result="success",
        )
    )
