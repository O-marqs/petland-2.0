from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_catalogs import crm as crm_fixture
from test_identity import identity as identity_fixture
from test_identity import identity_engine as engine_fixture
from test_identity import login, mutate, register
from test_scheduling import agenda as agenda_fixture
from test_scheduling import book

from petland.modules.identity.infrastructure.models import RoleRecord, UserRecord
from petland.modules.scheduling.infrastructure.models import AppointmentRecord, ResourceRecord
from petland.modules.scheduling.infrastructure.store import schedule_store
from petland.modules.scheduling.public.coordination import lock_schedule
from petland.shared.domain.errors import BusinessError

identity, identity_engine, crm, agenda = (
    identity_fixture,
    engine_fixture,
    crm_fixture,
    agenda_fixture,
)
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "change", ["resource_disabled", "user_disabled", "unverified", "role_lost"]
)
def test_capacity_rechecks_worker_eligibility_for_availability_and_booking(
    agenda, identity_engine, change
):
    a = agenda
    query = (a[2], None, a[4][0], a[5], a[6].date())
    assert a[0].availability(*query).slots
    with identity_engine.begin() as db:
        if change == "resource_disabled":
            db.execute(
                update(ResourceRecord).where(ResourceRecord.id == a[7].id).values(active=False)
            )
        elif change == "role_lost":
            db.execute(
                update(RoleRecord).where(RoleRecord.user_id == a[1].id).values(role="CUSTOMER")
            )
        else:
            db.execute(
                update(UserRecord)
                .where(UserRecord.id == a[1].id)
                .values(
                    **(
                        {"status": "DISABLED"}
                        if change == "user_disabled"
                        else {"email_verified_at": None}
                    )
                )
            )
    assert a[0].availability(*query).slots == []
    # Capture the known calendar version without depending on the changed worker's permission.
    with schedule_store(identity_engine) as store:
        version = store.configuration().version
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        a[0].command(
            a[2],
            None,
            "book",
            uuid4(),
            "p06-test",
            pet_id=a[4][0],
            service_id=a[5],
            starts_at=a[6],
            offer_version=1,
            configuration_version=version,
        )
    with identity_engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM appointments")) == 0
        assert db.scalar(text("SELECT count(*) FROM booking_idempotency")) == 0


def test_pagination_rejects_overflow_and_unbounded_work_before_querying(agenda):
    client = agenda[-1]
    for path in [
        "/catalog/services",
        "/operations/services",
        "/operations/customers",
        f"/operations/customers/{agenda[3].id}/pets",
        "/me/pets",
        "/me/appointments",
        "/operations/appointments",
        "/operations/agenda",
    ]:
        for query in [
            "offset=100001",
            "offset=99999999999999999999999999",
            "limit=101",
            "offset=-1",
        ]:
            response = client.get(f"/api/v1{path}?{query}")
            assert response.status_code == 422, (path, response.text)
            assert response.json()["request_id"] == response.headers["x-request-id"]
    assert client.get("/api/v1/catalog/services?offset=100000").status_code == 200


def test_cross_owner_commands_and_cross_origin_staff_writes_leave_no_effects(
    agenda, crm, identity_engine
):
    a = agenda
    appointment = book(a)
    client = a[-1]
    other = register(crm[0], crm[1], "hardening-other@example.com")
    crm[3].create(
        other,
        name="Outra pessoa sintética",
        email=other.email,
        phone="",
        address="",
        assisted=False,
        request_id="p06-test",
    )
    login(client, other.email)
    for operation, body in [
        ("cancel", {"version": 1, "reason": "Tentativa entre contas"}),
        (
            "reschedule",
            {
                "version": 1,
                "reason": "Tentativa entre contas",
                "starts_at": (a[6] + timedelta(hours=1)).isoformat(),
                "configuration_version": 2,
            },
        ),
    ]:
        response = mutate(
            client,
            "POST",
            f"/me/appointments/{appointment.id}/{operation}",
            body,
            **{"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 404, response.text
    login(client, a[1].email)
    csrf = client.get("/api/v1/auth/csrf").json()["csrf_token"]
    for suffix, body in [
        (
            "notes",
            {"version": 1, "body": "PRIVATE P06 <script>alert(1)</script>", "visibility": "PUBLIC"},
        ),
        ("transitions", {"version": 1, "operation": "arrive"}),
    ]:
        response = client.post(
            f"/api/v1/operations/attendances/{appointment.id}/{suffix}",
            json=body,
            headers={
                "Origin": "https://attacker.invalid",
                "X-CSRF-Token": csrf,
                "Idempotency-Key": str(uuid4()),
            },
        )
        assert response.status_code == 403, response.text
    oversized = client.post(
        f"/api/v1/operations/attendances/{appointment.id}/notes",
        content='{"body":"' + "X" * 17000 + '"}',
        headers={
            "X-CSRF-Token": csrf,
            "Idempotency-Key": str(uuid4()),
            "Content-Type": "application/json",
        },
    )
    assert oversized.status_code == 413
    assert client.get("/api/v1/management/users").status_code == 403
    with identity_engine.connect() as db:
        assert db.execute(
            text("SELECT status, version FROM appointments WHERE id=:id"), {"id": appointment.id}
        ).one() == ("BOOKED", 1)
        assert db.scalar(text("SELECT count(*) FROM appointment_notes")) == 0
        assert db.scalar(text("SELECT count(*) FROM booking_idempotency")) == 1


def test_report_totals_clip_boundaries_and_ignore_cancelled_occupancy(agenda, identity_engine):
    a = agenda
    first = book(a)
    second = book(a, pet=1, start=a[6] + timedelta(hours=2))
    third = book(a, pet=2, start=a[6] + timedelta(hours=5))
    start, end = a[6], a[6] + timedelta(days=1)
    with identity_engine.begin() as db:
        for appointment, at, status in [
            (first, start - timedelta(minutes=10), "BOOKED"),
            (second, start + timedelta(hours=1), "BOOKED"),
            (third, end - timedelta(minutes=20), "CANCELLED"),
        ]:
            db.execute(
                update(AppointmentRecord)
                .where(AppointmentRecord.id == appointment.id)
                .values(
                    starts_at=at,
                    ends_at=at + timedelta(hours=1),
                    occupied_start_at=at,
                    occupied_end_at=at + timedelta(hours=1),
                    status=status,
                )
            )
    with schedule_store(identity_engine) as store:
        totals = store.period_totals(start, end)
    assert totals.total == 2  # Started during the interval, including the cancelled visit.
    assert totals.by_status == {"BOOKED": 1, "CANCELLED": 1}
    assert totals.by_service == {first.offer.service_name: 2}
    assert (
        totals.occupied_minutes == 110
    )  # 50 minutes carried in + 60; cancellation contributes zero.


def test_report_read_locks_coexist_and_still_exclude_booking_writes(agenda, identity_engine):
    with Session(identity_engine) as first, first.begin():
        lock_schedule(first, shared=True)
        with Session(identity_engine) as second, second.begin():
            second.execute(text("SET LOCAL lock_timeout = '200ms'"))
            lock_schedule(second, shared=True)
            with pytest.raises(DBAPIError), Session(identity_engine) as writer, writer.begin():
                writer.execute(text("SET LOCAL lock_timeout = '200ms'"))
                lock_schedule(writer)
    with Session(identity_engine) as writer, writer.begin():
        writer.execute(text("SET LOCAL lock_timeout = '200ms'"))
        lock_schedule(writer)
