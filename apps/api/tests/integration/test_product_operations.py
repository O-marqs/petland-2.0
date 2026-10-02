from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from test_catalogs import PET
from test_catalogs import crm as crm_fixture
from test_identity import identity as identity_fixture
from test_identity import identity_engine as engine_fixture
from test_identity import login, mutate, register
from test_scheduling import agenda as agenda_fixture
from test_scheduling import book, race

from petland.modules.identity.domain.models import Role
from petland.modules.scheduling.application.operations import Operations
from petland.modules.scheduling.domain.models import CapacityPool, Resource, StaffShift, Window
from petland.modules.scheduling.domain.operations import AppointmentFilter
from petland.modules.scheduling.infrastructure import notifications
from petland.modules.scheduling.infrastructure.models import OutboxRecord
from petland.modules.scheduling.infrastructure.store import schedule_store
from petland.shared.domain.errors import BusinessError

identity, identity_engine, crm, agenda = (
    identity_fixture,
    engine_fixture,
    crm_fixture,
    agenda_fixture,
)
pytestmark = pytest.mark.integration


def worker(a, crm, number=2):
    user = register(crm[0], crm[1], f"person-{number}@example.com", roles=[Role.EMPLOYEE])
    return user, a[0].resource(a[1], Resource(user.id, f"Pessoa {number}", [a[5]]), "test")


def operations(a, engine, minutes=0):
    return Operations(lambda: schedule_store(engine), lambda: a[6] + timedelta(minutes=minutes))


def act(op, a, appointment, action, **kwargs):
    return op.command(a[1], appointment.id, action, appointment.version, uuid4(), "test", **kwargs)


def cancel(a, appointment):
    return a[0].command(
        a[2],
        None,
        "cancel",
        uuid4(),
        "test",
        appointment_id=appointment.id,
        version=appointment.version,
        reason="Teste de capacidade",
    )


def test_collective_day_five_three_five_restores_inheritance_and_protects_bookings(agenda, crm):
    a = agenda
    resources = [a[7], *[worker(a, crm, n)[1] for n in range(2, 6)]]
    day = a[6].date()
    roster = a[0].roster(a[1], day)
    assert len(roster.rows) == 5 and not roster.custom
    shifts = [StaffShift(r.id, [Window(540, 720)]) for r in resources[:3]]
    assert a[0].set_roster(a[1], day, shifts, "Equipe reduzida", roster.version, "test", True) == []
    assert not a[0].roster(a[1], day).custom
    a[0].set_roster(a[1], day, shifts, "Equipe reduzida", roster.version, "test")
    results = race(*[lambda n=n: book(a, n) for n in range(5)])
    booked = [r for r in results if not isinstance(r, str)]
    assert len(booked) == 3 and results.count("SLOT_UNAVAILABLE") == 2
    assert {r.resource_id for r in booked} == {r.id for r in resources[:3]}
    assert sum(bool(r.windows) for r in a[0].roster(a[1], day).rows) == 3
    assert sum(bool(r.windows) for r in a[0].roster(a[1], day + timedelta(days=1)).rows) == 5
    version = a[0].roster(a[1], day).version
    impacts = a[0].set_roster(a[1], day, [], "Fechamento pontual", version, "test", True)
    assert set(impacts) == {b.id for b in booked}
    with pytest.raises(BusinessError, match="CALENDAR_IMPACT"):
        a[0].set_roster(a[1], day, [], "Fechamento pontual", version, "test")
    assert a[0].roster(a[1], day).version == version
    # Returning to inheritance does not create a permanent copy of shop hours.
    a[0].set_roster(a[1], day, None, "Retorno à escala habitual", version, "test")
    assert not a[0].roster(a[1], day).custom
    for b in booked:
        cancel(a, b)
    config = a[0].settings(a[1])[0]
    narrower = replace(
        config.calendar,
        weekly=[replace(d, windows=[Window(600, 720)]) for d in config.calendar.weekly],
    )
    a[0].configure(a[1], replace(config, calendar=narrower), "test")
    assert all(r.windows == [Window(600, 720)] for r in a[0].roster(a[1], day).rows)
    with pytest.raises(BusinessError, match="STALE_VERSION"):
        a[0].set_roster(a[1], day, shifts, "Resposta antiga", roster.version, "test")


def test_shared_capacity_concurrency_adjacency_reduction_and_cancel(agenda, crm):
    a = agenda
    worker(a, crm, 2)
    worker(a, crm, 3)
    pool = CapacityPool(uuid4(), "Duas banheiras", 2, [a[5]])
    a[0].set_pools(a[1], [pool], a[0].settings(a[1])[0].version, "test")
    results = race(*[lambda n=n: book(a, n) for n in range(3)])
    booked = [r for r in results if not isinstance(r, str)]
    assert len(booked) == 2 and results.count("SLOT_UNAVAILABLE") == 1
    # Half-open intervals release equipment exactly at the occupied end.
    next_booking = book(a, 3, a[6] + timedelta(hours=1))
    version = a[0].pools(a[1])[0]
    reduced = [replace(pool, capacity=1)]
    assert set(a[0].set_pools(a[1], reduced, version, "test", True)) == {b.id for b in booked}
    with pytest.raises(BusinessError, match="CALENDAR_IMPACT"):
        a[0].set_pools(a[1], reduced, version, "test")
    cancel(a, booked[0])
    a[0].set_pools(a[1], reduced, version, "test")
    assert a[0].detail(a[2], False, next_booking.id)[0] == next_booking
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        book(a, 4)
    cancel(a, booked[1])
    assert book(a, 4).status == "BOOKED"


def test_automatic_assignment_uses_least_planned_daily_load(agenda, crm):
    a = agenda
    first = book(a)
    _, alternate = worker(a, crm)
    second = book(a, 1, first.ends_at)
    assert first.resource_id == a[7].id and second.resource_id == alternate.id


def test_transfer_preserves_contract_replays_and_keeps_reason_internal(
    agenda, identity_engine, crm
):
    a = agenda
    ap = book(a)
    _, alternate = worker(a, crm)
    other = book(a, 1)
    op = operations(a, identity_engine)
    with pytest.raises(BusinessError, match="EXTENSION_UNAVAILABLE"):
        act(op, a, ap, "transfer", resource_id=alternate.id, reason="Saída antecipada")
    assert op.detail(a[1], ap.id).item.appointment == ap
    cancel(a, other)
    key = uuid4()
    transferred = op.command(
        a[1],
        ap.id,
        "transfer",
        ap.version,
        key,
        "test",
        resource_id=alternate.id,
        reason="MOTIVO_INTERNO",
    )
    assert transferred.resource_id == alternate.id
    assert (
        transferred.starts_at,
        transferred.ends_at,
        transferred.offer,
        transferred.reserved_until,
    ) == (ap.starts_at, ap.ends_at, ap.offer, ap.reserved_until)
    assert (
        op.command(
            a[1],
            ap.id,
            "transfer",
            ap.version,
            key,
            "test",
            resource_id=alternate.id,
            reason="MOTIVO_INTERNO",
        )
        == transferred
    )
    with pytest.raises(BusinessError, match="IDEMPOTENCY_MISMATCH"):
        op.command(
            a[1],
            ap.id,
            "transfer",
            ap.version,
            key,
            "test",
            resource_id=alternate.id,
            reason="Outro motivo",
        )
    detail = op.detail(a[1], ap.id)
    event = next(e for e in detail.events if e.kind == "transfer")
    assert (event.previous_resource_id, event.resource_id) == (ap.resource_id, alternate.id)
    login(a[-1])
    public = a[-1].get(f"/api/v1/me/appointments/{ap.id}")
    assert public.status_code == 200
    assert "MOTIVO_INTERNO" not in public.text and '"transfer"' not in public.text
    assert "resource_id" not in public.text
    transferred = act(op, a, transferred, "arrive")
    transferred = act(op, a, transferred, "start")
    transferred = act(operations(a, identity_engine, 42), a, transferred, "complete")
    with pytest.raises(BusinessError, match="INVALID_TRANSFER"):
        act(op, a, transferred, "transfer", resource_id=ap.resource_id, reason="Não reabre")


def test_report_attributes_completion_to_final_person_and_real_duration(
    agenda, identity_engine, crm
):
    a = agenda
    ap = book(a)
    _, alternate = worker(a, crm)
    ap = act(
        operations(a, identity_engine),
        a,
        ap,
        "transfer",
        resource_id=alternate.id,
        reason="Redistribuição",
    )
    ap = act(operations(a, identity_engine, 2), a, ap, "arrive")
    ap = act(operations(a, identity_engine, 11), a, ap, "start")
    act(operations(a, identity_engine, 53), a, ap, "complete", body="Resumo público")
    admin = register(crm[0], crm[1], "manager@example.com", roles=[Role.ADMIN])
    op = operations(a, identity_engine, 60)
    metrics = op.metrics(admin, a[6].date(), a[6].date())
    rows = {r.resource_id: r for r in metrics.staff}
    assert rows[a[7].id].completed == 0 and rows[alternate.id].completed == 1
    assert rows[alternate.id].average_actual_minutes == 42
    assert rows[alternate.id].average_delay_minutes == 11
    assert rows[alternate.id].average_deviation_minutes == -18
    assert (metrics.completed_pets, metrics.completed_customers) == (1, 1)
    assert metrics.services[0].average_planned_minutes == 60
    assert metrics.services[0].average_actual_minutes == 42
    with pytest.raises(BusinessError, match="FORBIDDEN"):
        op.metrics(a[1], a[6].date(), a[6].date())


def test_report_counts_returning_pets_once_and_keeps_idle_people(agenda, identity_engine, crm):
    a = agenda
    worker(a, crm, 2)
    for i, pet in enumerate([0, 0, 1]):
        ap = book(a, pet, a[6] + timedelta(hours=i))
        op = operations(a, identity_engine, i * 60)
        ap = act(op, a, ap, "arrive")
        ap = act(op, a, ap, "start")
        act(operations(a, identity_engine, i * 60 + 20), a, ap, "complete")
    cancel(a, book(a, 2, a[6] + timedelta(hours=4)))
    _, idle = worker(a, crm, 3)
    admin = register(crm[0], crm[1], "manager@example.com", roles=[Role.ADMIN])
    op = operations(a, identity_engine, 150)
    metrics = op.metrics(admin, a[6].date(), a[6].date())
    assert (metrics.total, metrics.completed_pets, metrics.completed_customers) == (4, 2, 1)
    assert sum(r.completed for r in metrics.staff) == 3
    assert metrics.services[0].completed == 3
    rows = {r.resource_id: r for r in metrics.staff}
    assert rows[idle.id].total == 0 and rows[idle.id].available_minutes == 480
    assert metrics.available_minutes == sum(r.available_minutes for r in metrics.staff)
    dashboard = op.dashboard(a[1], mine=False)
    assert dashboard.total == 4 and sum(r.completed for r in dashboard.staff) == 3
    assert next(r for r in dashboard.staff if r.resource_id == idle.id).planned == 0


def test_critical_care_requires_current_profile_ack_and_previous_care_is_private(
    agenda, identity_engine
):
    a = agenda
    login(a[-1])
    pet = a[-1].get(f"/api/v1/me/pets/{a[4][0]}").json()
    updated = mutate(
        a[-1],
        "PUT",
        f"/me/pets/{a[4][0]}",
        {
            **PET,
            "version": pet["version"],
            "allergies": "Alergia sintética",
            "handling_notes": "Secador baixo",
        },
    )
    assert updated.status_code == 200, updated.text
    ap = book(a)
    op = operations(a, identity_engine)
    ap = act(op, a, ap, "arrive")
    for version in [None, pet["version"]]:
        with pytest.raises(BusinessError, match="PET_CARE_ACK_REQUIRED"):
            act(op, a, ap, "start", care_version=version)
        assert op.detail(a[1], ap.id).item.appointment == ap
    ap = act(op, a, ap, "start", care_version=updated.json()["version"])
    ap = act(op, a, ap, "note", body="CONTEXT_PRIVATE")
    ap = act(operations(a, identity_engine, 42), a, ap, "complete", body="Resumo autorizado")
    following = book(a, start=ap.ends_at)
    detail = op.detail(a[1], following.id)
    assert detail.context.allergies == "Alergia sintética"
    assert detail.context.handling_notes == "Secador baixo"
    assert detail.previous_care[0].appointment_id == ap.id
    assert any(n.body == "CONTEXT_PRIVATE" for n in detail.previous_care[0].notes)
    public = a[-1].get(f"/api/v1/me/appointments/{following.id}")
    assert "CONTEXT_PRIVATE" not in public.text and "previous_care" not in public.text
    assert not op.detail(a[1], ap.id).previous_care


def test_reminders_are_due_once_old_schedule_is_suppressed_and_ready_notice_is_safe(
    agenda, identity_engine, monkeypatch
):
    a = agenda
    a[0].configure(a[1], replace(a[0].settings(a[1])[0], reminder_minutes=30), "test")
    ap = book(a)
    moment = [a[6] - timedelta(minutes=31)]

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return moment[0].astimezone(tz or UTC)

    monkeypatch.setattr(notifications, "datetime", Frozen)
    sent = []
    assert notifications.deliver_one(identity_engine, lambda *args: sent.append(args))
    assert not notifications.deliver_one(identity_engine, lambda *args: sent.append(args))
    moment[0] += timedelta(minutes=1)
    assert notifications.deliver_one(identity_engine, lambda *args: sent.append(args))
    assert not notifications.deliver_one(identity_engine, lambda *args: sent.append(args))
    assert len(sent) == 2 and "Lembrete" in sent[-1][1]
    op = operations(a, identity_engine)
    ap = act(op, a, ap, "arrive")
    ap = act(op, a, ap, "start")
    ap = act(op, a, ap, "note", body="EMAIL_PRIVATE")
    ap = act(operations(a, identity_engine, 42), a, ap, "complete", body="Publicado na área")
    moment[0] = a[6] + timedelta(minutes=42)
    assert notifications.deliver_one(identity_engine, lambda *args: sent.append(args))
    assert "pet ficou pronto" in sent[-1][1]
    assert "EMAIL_PRIVATE" not in sent[-1][2] and "Concluído:" in sent[-1][2]
    second = book(a, 1, a[6] + timedelta(hours=2))
    second = a[0].command(
        a[2],
        None,
        "reschedule",
        uuid4(),
        "test",
        appointment_id=second.id,
        version=second.version,
        reason="Novo horário",
        starts_at=a[6] + timedelta(hours=4),
        configuration_version=a[0].settings(a[1])[0].version,
    )
    cancel(a, second)
    with Session(identity_engine) as db:
        reminders = db.scalars(
            select(OutboxRecord).where(
                OutboxRecord.appointment_id == second.id, OutboxRecord.kind == "reminder"
            )
        ).all()
        assert len(reminders) == 2 and all(r.suppressed_at is not None for r in reminders)
    login(a[-1])
    detail = a[-1].get(f"/api/v1/me/appointments/{ap.id}")
    assert any(
        m["kind"] == "complete" and m["delivered_at"] for m in detail.json()["communications"]
    )
    assert all(word not in detail.text for word in ["recipient", "subject", "EMAIL_PRIVATE"])


def test_personal_dashboard_and_unconfigured_employee_do_not_show_team_as_mine(
    agenda, identity_engine, crm
):
    a = agenda
    ap = book(a)
    unconfigured = register(crm[0], crm[1], "unconfigured@example.com", roles=[Role.EMPLOYEE])
    op = operations(a, identity_engine, 10)
    own = op.dashboard(a[1])
    assert own.my_resource_id == ap.resource_id and own.appointments[0].appointment.id == ap.id
    assert own.attention[0].appointment.id == ap.id
    empty = op.dashboard(unconfigured)
    assert empty.my_resource_id is None and empty.appointments == [] and empty.total == 1
    assert op.agenda(unconfigured, None, None, AppointmentFilter(), 0, 20, True).total == 0
    assert op.dashboard(unconfigured, mine=False).appointments[0].appointment.id == ap.id
    login(a[-1])
    for path in [
        "/operations/dashboard",
        f"/operations/roster/{a[6].date()}",
        "/operations/capacity",
    ]:
        assert a[-1].get("/api/v1" + path).status_code == 403


def test_downgrade_refuses_critical_data_and_empty_extensions_remain_compatible(
    agenda, identity_engine
):
    a = agenda
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    login(a[-1])
    pet = a[-1].get(f"/api/v1/me/pets/{a[4][0]}").json()
    changed = mutate(
        a[-1],
        "PUT",
        f"/me/pets/{a[4][0]}",
        {**PET, "version": pet["version"], "allergies": "Não pode descartar"},
    ).json()
    with pytest.raises(RuntimeError, match="Preserve operational alerts"):
        command.downgrade(config, "0006_hardening")
    with identity_engine.connect() as db:
        assert (
            db.scalar(text("SELECT version_num FROM alembic_version")) == "0007_product_operations"
        )
        assert (
            db.scalar(text("SELECT allergies FROM pets WHERE id=:id"), {"id": a[4][0]})
            == "Não pode descartar"
        )
    assert (
        mutate(
            a[-1],
            "PUT",
            f"/me/pets/{a[4][0]}",
            {**PET, "version": changed["version"], "allergies": ""},
        ).status_code
        == 200
    )
    try:
        command.downgrade(config, "0006_hardening")
        with identity_engine.connect() as db:
            value = db.scalar(text("SELECT data FROM schedule_configuration WHERE id=1"))
            assert all(
                key not in value for key in ["staff_days", "capacity_pools", "reminder_minutes"]
            )
            assert db.scalar(text("SELECT count(*) FROM pets")) == 10
    finally:
        command.upgrade(config, "head")
    assert a[0].settings(a[1])[0].capacity_pools == []
