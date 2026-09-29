import logging
import smtplib
import ssl
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from threading import Event

from sqlalchemy import or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from petland.modules.scheduling.infrastructure.models import OutboxRecord


class AppointmentMailer:
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        starttls: bool,
        username: str | None,
        password: str | None,
    ) -> None:
        self.host, self.port, self.sender = host, port, sender
        self.starttls, self.username, self.password = starttls, username, password

    def send(self, recipient: str, subject: str, body: str, message_id: str) -> None:
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self.sender, recipient, subject
        message["Message-ID"] = f"<{message_id}@petland.local>"
        message.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
            if self.starttls:
                smtp.starttls(context=ssl.create_default_context())
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(message)


def deliver_one(engine: Engine, send: Callable[[str, str, str, str], None]) -> bool:
    now = datetime.now(UTC)
    with Session(engine) as db, db.begin():
        row = db.scalar(
            select(OutboxRecord)
            .where(
                OutboxRecord.delivered_at.is_(None),
                OutboxRecord.available_at <= now,
                or_(OutboxRecord.lease_until.is_(None), OutboxRecord.lease_until < now),
            )
            .order_by(OutboxRecord.created_at, OutboxRecord.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if row is None:
            return False
        row.attempts += 1
        row.lease_until = now + timedelta(minutes=2)
        id, lease, attempt = row.id, row.lease_until, row.attempts
        payload = (row.recipient, row.subject, row.body, str(row.id))
    # SMTP never holds a database transaction or the booking lock.
    delivered = False
    try:
        send(*payload)
        delivered = True
    except (OSError, smtplib.SMTPException):
        logging.getLogger("petland").error("appointment_mail_delivery_failed")
    with Session(engine) as db, db.begin():
        row = db.scalar(select(OutboxRecord).where(OutboxRecord.id == id).with_for_update())
        if row is not None and row.lease_until == lease:
            row.lease_until = None
            if delivered:
                row.delivered_at = datetime.now(UTC)
            else:
                row.available_at = datetime.now(UTC) + timedelta(
                    seconds=min(3600, 30 * 2 ** min(attempt, 7))
                )
    return True


def notification_loop(engine: Engine, mailer: AppointmentMailer, stop: Event) -> None:
    while not stop.is_set():
        try:
            found = deliver_one(engine, mailer.send)
        except Exception:
            logging.getLogger("petland").error("appointment_outbox_unavailable")
            found = False
        if not found:
            stop.wait(5)
