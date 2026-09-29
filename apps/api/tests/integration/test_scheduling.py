import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_catalogs import CONTACT, PET, SERVICE
from test_catalogs import crm as crm_fixture
from test_identity import identity as identity_fixture
from test_identity import identity_engine as engine_fixture
from test_identity import login, mutate, register

from petland.modules.catalog.application.service import Catalog
from petland.modules.catalog.domain.models import Option
from petland.modules.catalog.infrastructure.store import catalog_store
from petland.modules.identity.domain.models import Role
from petland.modules.pets.application.service import Pets
from petland.modules.pets.infrastructure.store import pet_store
from petland.modules.pets.public import Size
from petland.modules.scheduling.application.service import Scheduling
from petland.modules.scheduling.domain.models import (
    Calendar,
    Configuration,
    Day,
    ExceptionDay,
    Resource,
    Window,
)
from petland.modules.scheduling.infrastructure.models import (
    AppointmentRecord,
    ConfigurationRecord,
    OutboxRecord,
)
from petland.modules.scheduling.infrastructure.notifications import deliver_one
from petland.modules.scheduling.infrastructure.store import schedule_store
from petland.modules.scheduling.infrastructure.values import document
from petland.shared.database import build_engine
from petland.shared.domain.errors import BusinessError

identity = identity_fixture
identity_engine = engine_fixture
crm = crm_fixture
pytestmark = pytest.mark.integration


@pytest.fixture
def agenda(crm, identity_engine):
    identity, mailbox, _, customers, client = crm
    with Session(identity_engine) as db, db.begin():
        db.merge(ConfigurationRecord(id=1, data=document(Configuration())))
    staff = register(identity, mailbox, "staff@example.com", roles=[Role.EMPLOYEE])
    user = register(identity, mailbox)
    customer = customers.create(user, **CONTACT, assisted=False, request_id="test")
    login(client)
    pets = [
        UUID(mutate(client, "POST", "/me/pets", {**PET, "name": f"Pet sintético {i}"}).json()["id"])
        for i in range(10)
    ]
    login(client, staff.email)
    response = mutate(
        client,
        "POST",
        "/operations/services",
        {
            **SERVICE,
            "options": [{"size": "SMALL", "price": "80.25", "duration_minutes": 60}],
        },
    )
    assert response.status_code == 201, response.text
    service_id = UUID(response.json()["id"])
    schedule = Scheduling(lambda: schedule_store(identity_engine))
    resource = schedule.resource(
        staff, Resource(staff.id, "Equipe sintética", [service_id]), "test"
    )
    config = schedule.settings(staff)[0]
    schedule.configure(
        staff,
        replace(
            config,
            enabled=True,
            horizon_days=30,
            step_minutes=15,
            calendar=Calendar([Day(d, [Window(540, 720), Window(780, 1080)]) for d in range(7)]),
        ),
        "test",
    )
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=UTC) + timedelta(hours=12)
    return schedule, staff, user, customer, pets, service_id, start, resource, client


def book(a, pet=0, start=None, key=None, schedule=None):
    s, _, user, _, pets, service, at, _, _ = a
    config = s.settings(a[1])[0]
    return (schedule or s).command(
        user,
        None,
        "book",
        key or uuid4(),
        "test",
        pet_id=pets[pet],
        service_id=service,
        starts_at=start or at,
        offer_version=1,
        configuration_version=config.version,
    )


def race(*functions):
    barrier = Barrier(len(functions))

    def run(fn):
        barrier.wait(timeout=20)
        try:
            return fn()
        except BusinessError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=len(functions)) as pool:
        return list(pool.map(run, functions))


@pytest.mark.parametrize("capacity", [1, 2])
def test_last_capacity_ten_requests_independent_engines(agenda, identity_engine, crm, capacity):
    a = agenda
    if capacity == 2:
        worker = register(crm[0], crm[1], "second@example.com", roles=[Role.EMPLOYEE])
        a[0].resource(a[1], Resource(worker.id, "Segunda pessoa", [a[5]]), "test")
    engines = [
        build_engine(os.environ["TEST_DATABASE_URL"], statement_timeout_ms=10000) for _ in range(2)
    ]
    try:
        instances = [Scheduling(lambda e=e: schedule_store(e)) for e in engines]
        results = race(*[lambda i=i: book(a, i, schedule=instances[i % 2]) for i in range(10)])
        assert sum(not isinstance(r, str) for r in results) == capacity
        assert results.count("SLOT_UNAVAILABLE") == 10 - capacity
        with identity_engine.connect() as db:
            for table in [
                "appointments",
                "appointment_events",
                "booking_idempotency",
                "appointment_outbox",
            ]:
                assert db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == capacity
    finally:
        for engine in engines:
            engine.dispose()


def test_partial_overlap_adjacency_pet_exclusion_and_buffers(agenda, crm):
    a = agenda
    first = book(a)
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        book(a, 1, a[6] + timedelta(minutes=30))
    assert book(a, 1, first.ends_at).starts_at == first.ends_at
    worker = register(crm[0], crm[1], "second@example.com", roles=[Role.EMPLOYEE])
    a[0].resource(a[1], Resource(worker.id, "Segunda pessoa", [a[5]]), "test")
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        book(a, 0)
    assert book(a, 2).resource_id != first.resource_id


def test_replay_snapshot_and_payload_mismatch_after_cancel(agenda):
    a, key = agenda, uuid4()
    first = book(a, key=key)
    assert book(a, key=key) == first
    cancelled = a[0].command(
        a[2],
        None,
        "cancel",
        uuid4(),
        "test",
        appointment_id=first.id,
        version=1,
        reason="Mudança de planos",
    )
    assert cancelled.status == "CANCELLED"
    assert book(a, key=key) == first
    with pytest.raises(BusinessError, match="IDEMPOTENCY_MISMATCH"):
        book(a, 1, key=key)
    assert len(a[0].detail(a[2], False, first.id)[1]) == 2
    assert book(a, 1).status == "BOOKED"


def test_two_reschedules_one_version_and_failed_change_preserves_original(agenda):
    a = agenda
    original = book(a)
    occupied = book(a, 1, a[6] + timedelta(hours=2))

    def change(start):
        return a[0].command(
            a[2],
            None,
            "reschedule",
            uuid4(),
            "test",
            appointment_id=original.id,
            version=1,
            reason="Novo horário",
            starts_at=start,
            configuration_version=a[0].settings(a[1])[0].version,
        )

    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        change(occupied.starts_at)
    assert a[0].detail(a[2], False, original.id)[0] == original
    results = race(
        lambda: change(a[6] + timedelta(hours=1)), lambda: change(a[6] + timedelta(hours=4))
    )
    assert results.count("STALE_VERSION") == 1
    detail, events = a[0].detail(a[2], False, original.id)
    assert detail.version == 2 and len(events) == 2


def test_cancel_races_failed_reschedule_without_hybrid(agenda):
    a = agenda
    original = book(a)
    book(a, 1, a[6] + timedelta(hours=2))
    results = race(
        lambda: a[0].command(
            a[2],
            None,
            "cancel",
            uuid4(),
            "test",
            appointment_id=original.id,
            version=1,
            reason="Cancelamento",
        ),
        lambda: a[0].command(
            a[2],
            None,
            "reschedule",
            uuid4(),
            "test",
            appointment_id=original.id,
            version=1,
            reason="Troca",
            starts_at=a[6] + timedelta(hours=2),
            configuration_version=a[0].settings(a[1])[0].version,
        ),
    )
    assert any(r in ("SLOT_UNAVAILABLE", "STALE_VERSION") for r in results if isinstance(r, str))
    current, events = a[0].detail(a[2], False, original.id)
    assert current.status == "CANCELLED" and current.starts_at == original.starts_at
    assert len(events) == 2


def test_calendar_preview_cannot_override_new_booking_and_race(agenda):
    a = agenda
    config = a[0].settings(a[1])[0]
    closed = replace(
        config, calendar=Calendar(config.calendar.weekly, [ExceptionDay(a[6].date(), [])])
    )
    assert a[0].configure(a[1], closed, "test", preview=True) == []
    original = book(a)
    assert a[0].configure(a[1], closed, "test", preview=True) == [original.id]
    with pytest.raises(BusinessError, match="CALENDAR_IMPACT"):
        a[0].configure(a[1], closed, "test")
    # A different day has no bookings; closure vs creation is serialized.
    other = a[6] + timedelta(days=1)
    closing = replace(
        config, calendar=Calendar(config.calendar.weekly, [ExceptionDay(other.date(), [])])
    )
    results = race(lambda: a[0].configure(a[1], closing, "test"), lambda: book(a, 1, other))
    assert sum(isinstance(r, str) for r in results) == 1
    assert any(
        r in ("CALENDAR_IMPACT", "OFFER_CHANGED", "SLOT_UNAVAILABLE")
        for r in results
        if isinstance(r, str)
    )


def test_pet_archive_and_service_inactivation_coordinate_booking(agenda, identity_engine):
    a = agenda
    pets = Pets(lambda: pet_store(identity_engine))
    results = race(lambda: book(a), lambda: pets.archive(a[2], None, a[4][0], True, 1, "test"))
    assert sum(isinstance(r, str) for r in results) == 1
    catalog = Catalog(lambda: catalog_store(identity_engine))
    service = catalog.get(a[1], a[5])
    results = race(
        lambda: book(a, 1),
        lambda: catalog.save(
            a[1],
            service.name,
            service.description,
            service.species_ids,
            service.options,
            False,
            "test",
            service.id,
            service.version,
        ),
    )
    # Existing accepted bookings retain their contract; disabling only closes new sales.
    assert len(results) == 2
    with pytest.raises(BusinessError, match="OFFER_CHANGED"):
        book(a, 2)


def test_hours_pauses_exception_intersection_offer_and_resource_guards(agenda, identity_engine):
    a = agenda
    available = a[0].availability(a[2], None, a[4][0], a[5], a[6].date())
    assert a[6] in [slot.starts_at for slot in available.slots]
    assert a[6] + timedelta(hours=3) not in [slot.starts_at for slot in available.slots]
    resource = replace(a[7], calendar=Calendar([Day(d, [Window(600, 660)]) for d in range(7)]))
    a[0].resource(a[1], resource, "test", resource.id)
    available = a[0].availability(a[2], None, a[4][0], a[5], a[6].date())
    assert [s.starts_at for s in available.slots] == [a[6] + timedelta(hours=1)]
    booked = book(a, start=a[6] + timedelta(hours=1))
    with pytest.raises(BusinessError, match="CALENDAR_IMPACT"):
        a[0].resource(a[1], replace(resource, active=False, version=2), "test", resource.id)
    catalog = Catalog(lambda: catalog_store(identity_engine))
    service = catalog.get(a[1], a[5])
    catalog.save(
        a[1],
        service.name,
        "",
        service.species_ids,
        [Option(Size.SMALL, Decimal("200"), 90, 15, 15)],
        True,
        "test",
        service.id,
        service.version,
    )
    retained = a[0].availability(
        a[2], None, a[4][0], a[5], (a[6] + timedelta(days=1)).date(), booked.id
    )
    assert retained.offer.price == Decimal("80.25") and retained.offer.duration_minutes == 60
    with pytest.raises(BusinessError, match="OFFER_CHANGED"):
        book(a, 1)


def test_database_exclusions_independent_of_application(agenda, identity_engine):
    a = agenda
    first = book(a)
    with Session(identity_engine) as db:
        row = db.get(AppointmentRecord, first.id)
        data = {c.name: getattr(row, c.name) for c in AppointmentRecord.__table__.columns}
    with pytest.raises(IntegrityError), identity_engine.begin() as db:
        db.execute(
            AppointmentRecord.__table__.insert().values(
                **{**data, "id": uuid4(), "pet_id": a[4][1]}
            )
        )
    # Even a second capacity unit cannot overlap the same pet.
    with identity_engine.begin() as db:
        resource_id = uuid4()
        # Existing employee uniqueness is preserved; a different user represents another capacity.
        db.execute(
            text(
                "INSERT INTO schedule_resources (id,user_id,name,service_ids,active,version) VALUES (:id,:user,'Teste','[]',true,1)"
            ),
            {"id": resource_id, "user": a[2].id},
        )
    with pytest.raises(IntegrityError), identity_engine.begin() as db:
        db.execute(
            AppointmentRecord.__table__.insert().values(
                **{**data, "id": uuid4(), "resource_id": resource_id}
            )
        )


def test_outbox_rollback_retry_delivery_and_identity_guard(agenda, identity_engine, crm):
    a = agenda
    first = book(a)
    sent = []

    def fail(*args):
        raise OSError("synthetic SMTP unavailable")

    assert deliver_one(identity_engine, fail)
    with Session(identity_engine) as db, db.begin():
        message = db.scalar(select(OutboxRecord))
        assert message.attempts == 1 and message.delivered_at is None
        message.available_at = datetime.now(UTC)
    assert deliver_one(identity_engine, lambda *args: sent.append(args))
    assert len(sent) == 1 and "confirmada" in sent[0][1]
    assert not deliver_one(identity_engine, lambda *args: sent.append(args))
    with pytest.raises(BusinessError, match="FUTURE_BOOKINGS"), crm[0].uow() as work:
        work.store.lock_administration()
        user = work.store.user(user_id=a[1].id, lock=True)
        user.status = "INACTIVE"
        work.store.save_user(user)
    assert a[0].detail(a[2], False, first.id)[0].status == "BOOKED"


def test_http_authorization_forgery_double_confirmation_and_history(agenda, crm):
    a, client = agenda, agenda[-1]
    login(client)
    query = {"pet_id": str(a[4][0]), "service_id": str(a[5]), "date": a[6].date().isoformat()}
    available = client.get("/api/v1/me/availability", params=query)
    assert available.status_code == 200, available.text
    assert available.json()["change_cutoff_minutes"] == 0
    body = {
        "pet_id": query["pet_id"],
        "service_id": query["service_id"],
        "starts_at": a[6].isoformat(),
        "offer_version": 1,
        "configuration_version": available.json()["configuration_version"],
    }
    assert mutate(client, "POST", "/me/appointments", body).status_code == 422
    key = str(uuid4())
    assert (
        mutate(
            client,
            "POST",
            "/me/appointments",
            {**body, "resource_id": str(a[7].id)},
            **{"Idempotency-Key": key},
        ).status_code
        == 422
    )
    created = mutate(client, "POST", "/me/appointments", body, **{"Idempotency-Key": key})
    assert created.status_code == 201, created.text
    assert (
        mutate(client, "POST", "/me/appointments", body, **{"Idempotency-Key": key}).json()
        == created.json()
    )
    id = created.json()["id"]
    assert client.get(f"/api/v1/me/appointments/{id}").json()["events"][0]["kind"] == "book"
    assert client.get("/api/v1/operations/calendar").status_code == 403
    other = register(crm[0], crm[1], "other@example.com")
    crm[3].create(other, **CONTACT, assisted=False, request_id="test")
    login(client, other.email)
    assert client.get(f"/api/v1/me/appointments/{id}").status_code == 404
    assert client.get("/api/v1/me/appointments").json()["total"] == 0


def test_contracted_change_cutoff_and_staff_assistance(agenda):
    a = agenda
    config = a[0].settings(a[1])[0]
    a[0].configure(a[1], replace(config, change_cutoff_minutes=60), "test")
    original = book(a)
    a[0].clock = lambda: original.starts_at - timedelta(minutes=30)
    assert (
        a[0].availability(a[2], None, a[4][0], a[5], a[6].date(), original.id).change_cutoff_minutes
        == 60
    )
    with pytest.raises(BusinessError, match="CHANGE_WINDOW_CLOSED"):
        a[0].command(
            a[2],
            None,
            "cancel",
            uuid4(),
            "test",
            appointment_id=original.id,
            version=1,
            reason="Pedido do cliente",
        )
    assisted = a[0].command(
        a[1],
        None,
        "cancel",
        uuid4(),
        "test",
        appointment_id=original.id,
        version=1,
        reason="Equipe atendeu solicitação fora do prazo",
        assisted=True,
    )
    assert assisted.status == "CANCELLED"


def test_actor_is_revalidated_inside_booking_transaction(agenda, crm):
    a = agenda
    with crm[0].uow() as work:
        work.store.lock_administration()
        actor = work.store.user(user_id=a[2].id, lock=True)
        actor.status = "DISABLED"
        work.store.save_user(actor)
    with pytest.raises(BusinessError, match="AUTH_REQUIRED"):
        book(a)
