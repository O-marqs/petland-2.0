from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from test_catalogs import crm as crm_fixture
from test_identity import identity as identity_fixture
from test_identity import identity_engine as engine_fixture
from test_identity import login, mutate, register
from test_scheduling import agenda as agenda_fixture
from test_scheduling import book, race

from petland.modules.identity.domain.models import Role
from petland.modules.scheduling.application.operations import Operations
from petland.modules.scheduling.application.service import Scheduling
from petland.modules.scheduling.domain.models import Calendar, Resource
from petland.modules.scheduling.domain.operations import AppointmentFilter
from petland.modules.scheduling.infrastructure.store import schedule_store
from petland.shared.domain.errors import BusinessError

identity, identity_engine, crm, agenda = (
    identity_fixture,
    engine_fixture,
    crm_fixture,
    agenda_fixture,
)
pytestmark = pytest.mark.integration


def ops(a, engine, now=None):
    return Operations(lambda: schedule_store(engine), lambda: now or a[6])


def act(op, actor, a, kind, **kwargs):
    return op.command(actor, a.id, kind, a.version, uuid4(), "test-p05", **kwargs)


def test_complete_journey_notes_visibility_owner_and_server_times(agenda, identity_engine, crm):
    a = agenda
    ap = book(a)
    op = ops(a, identity_engine)
    ap = act(op, a[1], ap, "note", body="INTERNAL_PRIVATE <script>alert(1)</script>")
    ap = act(op, a[1], ap, "arrive")
    ap = act(op, a[1], ap, "start")
    ap = act(
        ops(a, identity_engine, a[6] + timedelta(minutes=45)),
        a[1],
        ap,
        "complete",
        body="Banho concluído. Resumo público.",
    )
    assert ap.status == "COMPLETED" and ap.completed_at >= ap.started_at >= ap.arrived_at
    assert ap.starts_at == a[6] and ap.ends_at == a[6] + timedelta(hours=1)
    client = a[-1]
    login(client)
    response = client.get(f"/api/v1/me/appointments/{ap.id}")
    assert response.status_code == 200, response.text
    assert response.json()["summaries"][0]["body"] == "Banho concluído. Resumo público."
    assert all(
        word not in response.text
        for word in ["INTERNAL_PRIVATE", "note_internal", "actor_id", "resource_id", "authors"]
    )
    assert (
        client.get(f"/api/v1/me/appointments?period=history&pet_id={ap.pet_id}").json()["total"]
        == 1
    )
    assert client.get("/api/v1/me/appointments?period=upcoming").json()["total"] == 0
    for path in [
        "/operations/agenda",
        f"/operations/attendances/{ap.id}",
        "/management/metrics?date_from=2026-01-01&date_to=2026-01-02",
    ]:
        assert client.get("/api/v1" + path).status_code == 403
    assert (
        mutate(
            client,
            "POST",
            f"/operations/attendances/{ap.id}/notes",
            {"version": ap.version, "body": "injection", "visibility": "PUBLIC"},
            **{"Idempotency-Key": str(uuid4())},
        ).status_code
        == 403
    )
    other = register(crm[0], crm[1], "other-owner@example.com")
    crm[3].create(
        other,
        name="Outro cliente",
        email=other.email,
        phone="",
        address="",
        assisted=False,
        request_id="test",
    )
    login(client, other.email)
    assert client.get(f"/api/v1/me/appointments/{ap.id}").status_code == 404
    assert client.get(f"/api/v1/me/appointments?pet_id={ap.pet_id}").json()["total"] == 0
    login(client, a[1].email)
    detail = client.get(f"/api/v1/operations/attendances/{ap.id}")
    assert detail.status_code == 200, detail.text
    assert "INTERNAL_PRIVATE" in detail.text
    assert detail.json()["item"]["allowed_actions"] == []


def test_state_sequence_terminal_and_time_rules(agenda, identity_engine):
    a = agenda
    ap = book(a)
    op = ops(a, identity_engine)
    for kind in ["start", "complete"]:
        with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
            act(op, a[1], ap, kind)
    with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
        act(ops(a, identity_engine, a[6] - timedelta(days=1)), a[1], ap, "arrive")
    ap = act(ops(a, identity_engine, a[6] - timedelta(minutes=10)), a[1], ap, "arrive")
    with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
        act(ops(a, identity_engine, a[6] - timedelta(seconds=1)), a[1], ap, "start")
    ap = act(op, a[1], ap, "start")
    with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
        act(op, a[1], ap, "no_show", reason="não pode faltar após começar")
    ap = act(op, a[1], ap, "complete")
    for kind in ["arrive", "start", "complete", "no_show"]:
        with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
            act(op, a[1], ap, kind, reason="final não reabre")


def test_no_show_cutoff_is_snapshotted_and_frees_capacity(agenda, identity_engine):
    a = agenda
    config = a[0].settings(a[1])[0]
    a[0].configure(a[1], replace(config, no_show_grace_minutes=15), "test")
    ap = book(a)
    a[0].configure(a[1], replace(a[0].settings(a[1])[0], no_show_grace_minutes=90), "test")
    assert ap.no_show_grace_minutes == 15
    with pytest.raises(BusinessError, match="INVALID_TRANSITION"):
        act(
            ops(a, identity_engine, a[6] + timedelta(minutes=14, seconds=59)),
            a[1],
            ap,
            "no_show",
            reason="ausente",
        )
    ap = act(
        ops(a, identity_engine, a[6] + timedelta(minutes=15)),
        a[1],
        ap,
        "no_show",
        reason="Ausência confirmada pela equipe",
    )
    assert ap.status == "NO_SHOW"
    assert book(a, 1).id != ap.id


def test_arrived_cancellation_is_admin_only_and_queues_notice(agenda, identity_engine, crm):
    a = agenda
    ap = act(ops(a, identity_engine), a[1], book(a), "arrive")
    with pytest.raises(BusinessError, match="FORBIDDEN"):
        act(ops(a, identity_engine), a[1], ap, "cancel_exception", reason="motivo")
    admin = register(crm[0], crm[1], "admin-operations@example.com", roles=[Role.ADMIN])
    with pytest.raises(BusinessError, match="REASON_REQUIRED"):
        act(ops(a, identity_engine), admin, ap, "cancel_exception")
    ap = act(
        ops(a, identity_engine),
        admin,
        ap,
        "cancel_exception",
        reason="Tutor desistiu antes do início",
    )
    assert ap.status == "CANCELLED"
    with identity_engine.connect() as db:
        assert db.execute(text("SELECT count(*) FROM appointment_outbox")).scalar_one() == 2


def test_transition_concurrency_and_response_replay(agenda, identity_engine):
    a, key = agenda, uuid4()
    ap = book(a)
    op = ops(a, identity_engine)
    results = race(*[lambda: act(op, a[1], ap, "arrive") for _ in range(2)])
    assert results.count("STALE_VERSION") == 1
    arrived = next(r for r in results if not isinstance(r, str))
    first = op.command(a[1], ap.id, "start", arrived.version, key, "test")
    completed = act(op, a[1], first, "complete")
    assert completed.status == "COMPLETED"
    assert op.command(a[1], ap.id, "start", arrived.version, key, "test") == first
    with pytest.raises(BusinessError, match="IDEMPOTENCY_MISMATCH"):
        op.command(a[1], ap.id, "start", arrived.version + 1, key, "test")
    with identity_engine.connect() as db:
        assert (
            db.execute(
                text("SELECT count(*) FROM appointment_events WHERE kind='start'")
            ).scalar_one()
            == 1
        )


def test_extension_conflict_keeps_original_and_alternative_person_is_checked(
    agenda, identity_engine, crm
):
    a = agenda
    ap = book(a)
    next_ap = book(a, 1, ap.ends_at)
    op = ops(a, identity_engine)
    ap = act(op, a[1], ap, "arrive")
    ap = act(op, a[1], ap, "start")
    until = ap.ends_at + timedelta(minutes=30)
    with pytest.raises(BusinessError, match="EXTENSION_UNAVAILABLE"):
        act(op, a[1], ap, "extend", until=until, reason="Atraso")
    assert op.detail(a[1], ap.id).item.appointment == ap
    worker = register(crm[0], crm[1], "alternate@example.com", roles=[Role.EMPLOYEE])
    alternate = a[0].resource(a[1], Resource(worker.id, "Alternativa sintética", [a[5]]), "test")
    extended = act(
        op,
        a[1],
        ap,
        "extend",
        until=until,
        resource_id=alternate.id,
        reason="Atraso; capacidade alternativa disponível",
    )
    assert extended.ends_at == ap.ends_at and extended.reserved_until == until
    assert extended.resource_id == alternate.id and extended.occupied_end_at == until
    assert op.detail(a[1], next_ap.id).item.appointment == next_ap
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        book(a, 0, ap.ends_at)
    with pytest.raises(BusinessError, match="EXTENSION_UNAVAILABLE"):
        act(
            op,
            a[1],
            extended,
            "extend",
            until=a[6] + timedelta(hours=7),
            reason="Passaria do expediente",
        )


@pytest.mark.parametrize("state", ["ARRIVED", "IN_PROGRESS", "COMPLETED"])
def test_execution_states_keep_database_and_allocator_exclusions(agenda, identity_engine, state):
    a = agenda
    op, ap = ops(a, identity_engine), book(a)
    for kind in (
        ["arrive"]
        + (["start"] if state in {"IN_PROGRESS", "COMPLETED"} else [])
        + (["complete"] if state == "COMPLETED" else [])
    ):
        ap = act(op, a[1], ap, kind)
    with pytest.raises(BusinessError, match="SLOT_UNAVAILABLE"):
        book(a, 1)
    # Independent raw database defense, bypassing the application allocator.
    with pytest.raises(IntegrityError), identity_engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO appointments SELECT :id, customer_id, :pet, service_id, resource_id, starts_at, ends_at, occupied_start_at, occupied_end_at, offer, timezone, change_cutoff_minutes, 'BOOKED', 1, created_at, updated_at, no_show_grace_minutes, NULL, NULL, NULL, NULL FROM appointments WHERE id=:original"
            ),
            {"id": uuid4(), "pet": a[4][1], "original": ap.id},
        )


def test_configuration_and_archive_protection_include_overdue_work(agenda, identity_engine):
    a = agenda
    ap = act(ops(a, identity_engine), a[1], book(a), "arrive")
    later = a[6] + timedelta(hours=5)
    schedule = Scheduling(lambda: schedule_store(identity_engine), lambda: later)
    with pytest.raises(BusinessError, match="CALENDAR_IMPACT"):
        schedule.configure(a[1], replace(schedule.settings(a[1])[0], calendar=Calendar()), "test")
    login(a[-1])
    response = mutate(
        a[-1], "PATCH", f"/me/pets/{ap.pet_id}/archive", {"version": 1, "archived": True}
    )
    assert response.status_code == 409, response.text


def test_metrics_dates_zero_capacity_and_audit_authorization(agenda, identity_engine, crm):
    a = agenda
    admin = register(crm[0], crm[1], "reporter@example.com", roles=[Role.ADMIN])
    bookings = [book(a, i, a[6] + timedelta(hours=h)) for i, h in enumerate([0, 1, 2, 4, 5])]
    op = ops(a, identity_engine, a[6] + timedelta(hours=6))
    act(ops(a, identity_engine, bookings[1].starts_at), a[1], bookings[1], "arrive")
    completed = bookings[2]
    ontime = ops(a, identity_engine, completed.starts_at)
    for kind in ["arrive", "start", "complete"]:
        completed = act(ontime, a[1], completed, kind)
    act(op, admin, bookings[3], "cancel_exception", reason="Exceção sintética")
    act(op, a[1], bookings[4], "no_show", reason="Falta sintética")
    day = a[6].date()
    summary = op.metrics(admin, day, day)
    assert summary.total == 5 and summary.by_status["COMPLETED"] == 1
    assert summary.by_status["NO_SHOW"] == summary.by_status["CANCELLED"] == 1
    assert summary.occupied_minutes == 180 and summary.available_minutes == 480
    assert summary.occupancy_percent == 37.5
    assert sum(summary.by_service.values()) == summary.total
    assert op.metrics(admin, day - timedelta(days=1), day - timedelta(days=1)).total == 0
    with pytest.raises(BusinessError, match="FORBIDDEN"):
        op.metrics(a[1], day, day)
    with pytest.raises(BusinessError, match="INVALID_PERIOD"):
        op.metrics(admin, day, day + timedelta(days=31))
    items = op.agenda(
        a[1], day, day, AppointmentFilter(search="Pet sintético", status="COMPLETED"), 0, 20
    )
    assert items.total == 1 and items.items[0].appointment.id == completed.id
    login(a[-1], a[1].email)
    path = "/api/v1/management/audit?start=2020-01-01T00:00:00Z&end=2020-01-02T00:00:00Z"
    assert a[-1].get(path).status_code == 403
    login(a[-1], admin.email)
    assert a[-1].get(path).status_code == 200


def test_event_failure_rolls_back_state_note_and_idempotency(agenda, identity_engine):
    a, ap = agenda, book(agenda)
    with identity_engine.begin() as db:
        db.execute(
            text(
                "ALTER TABLE appointment_events ADD CONSTRAINT test_reject_note CHECK (kind <> 'note_internal')"
            )
        )
    try:
        with pytest.raises(IntegrityError):
            act(ops(a, identity_engine), a[1], ap, "note", body="Must rollback")
        assert a[0].detail(a[1], True, ap.id)[0] == ap
        with identity_engine.connect() as db:
            assert db.execute(text("SELECT count(*) FROM appointment_notes")).scalar_one() == 0
            assert db.execute(text("SELECT count(*) FROM booking_idempotency")).scalar_one() == 1
    finally:
        with identity_engine.begin() as db:
            db.execute(text("ALTER TABLE appointment_events DROP CONSTRAINT test_reject_note"))


def test_actual_overrun_blocks_next_start_and_allows_completion(agenda, identity_engine):
    a = agenda
    op = ops(a, identity_engine)
    first, second = book(a), book(a, 1, a[6] + timedelta(hours=1))
    first = act(op, a[1], first, "arrive")
    first = act(op, a[1], first, "start")
    later = ops(a, identity_engine, second.starts_at)
    second = act(later, a[1], second, "arrive")
    with pytest.raises(BusinessError, match="RESOURCE_IN_PROGRESS"):
        act(later, a[1], second, "start")
    act(later, a[1], first, "complete")
    assert act(later, a[1], second, "start").status == "IN_PROGRESS"


def test_http_staff_commands_validate_inputs_replay_and_note_audit(agenda, identity_engine):
    a = agenda
    ap = book(a)
    login(a[-1], a[1].email)
    path = f"/operations/attendances/{ap.id}/notes"
    data = {"version": ap.version, "body": "Nota pela API", "visibility": "INTERNAL"}
    key = {"Idempotency-Key": str(uuid4())}
    first = mutate(a[-1], "POST", path, data, **key)
    assert first.status_code == 200, first.text
    assert mutate(a[-1], "POST", path, data, **key).json() == first.json()
    assert mutate(a[-1], "POST", path, {**data, "actor_id": str(uuid4())}, **key).status_code == 422
    with identity_engine.connect() as db:
        assert (
            db.execute(
                text("SELECT count(*) FROM appointment_notes WHERE body = 'Nota pela API'")
            ).scalar_one()
            == 1
        )
        assert (
            db.execute(
                text("SELECT count(*) FROM audit_events WHERE action = 'appointment.note_internal'")
            ).scalar_one()
            == 1
        )


def test_reassignment_of_running_visit_rejects_person_with_overdue_visit(
    agenda, identity_engine, crm
):
    a, op = agenda, ops(agenda, identity_engine)
    first = book(a)
    for kind in ["arrive", "start"]:
        first = act(op, a[1], first, kind)
    worker = register(crm[0], crm[1], "busy-reassignment@example.com", roles=[Role.EMPLOYEE])
    alternate = a[0].resource(a[1], Resource(worker.id, "Alternativa", [a[5]]), "test")
    second = book(a, 1, first.ends_at)
    later = ops(a, identity_engine, second.starts_at)
    second = act(later, a[1], second, "arrive")
    second = act(
        later,
        a[1],
        second,
        "extend",
        until=second.ends_at + timedelta(minutes=10),
        resource_id=alternate.id,
        reason="Realocação inicial",
    )
    second = act(later, a[1], second, "start")
    key = uuid4()
    for _ in range(2):
        with pytest.raises(BusinessError, match="RESOURCE_IN_PROGRESS"):
            later.command(
                a[1],
                second.id,
                "extend",
                second.version,
                key,
                "test",
                until=second.capacity_end + timedelta(minutes=10),
                resource_id=first.resource_id,
                reason="Pessoa anterior ainda ocupada",
            )
    assert later.detail(a[1], second.id).item.appointment == second
    act(later, a[1], first, "complete")
    assert (
        act(
            later,
            a[1],
            second,
            "extend",
            until=second.capacity_end + timedelta(minutes=10),
            resource_id=first.resource_id,
            reason="Pessoa liberada após concluir",
        ).resource_id
        == first.resource_id
    )


def test_completed_history_does_not_block_capacity_changes_and_zero_denominator(
    agenda, identity_engine, crm
):
    a = agenda
    admin = register(crm[0], crm[1], "capacity-admin@example.com", roles=[Role.ADMIN])
    ap, op = book(a), ops(a, identity_engine)
    for kind in ["arrive", "start", "complete"]:
        ap = act(op, a[1], ap, kind)
    with crm[0].uow() as work:
        worker = work.store.user(user_id=a[1].id, lock=True)
        worker.status = "DISABLED"
        work.store.save_user(worker)
    config = a[0].settings(admin)[0]
    assert a[0].configure(admin, replace(config, enabled=False), "test") == []
    metrics = op.metrics(admin, a[6].date(), a[6].date())
    assert metrics.occupied_minutes == 60
    assert metrics.available_minutes == 0 and metrics.occupancy_percent is None
    assert a[0].detail(a[2], False, ap.id)[0].status == "COMPLETED"
