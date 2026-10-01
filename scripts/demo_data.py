"""Privileged synthetic fixture, exclusively for the isolated P07 demo database."""

import json
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from petland.modules.catalog.domain.models import Option, Service
from petland.modules.catalog.infrastructure.store import PostgresCatalog
from petland.modules.customers.domain.models import Customer
from petland.modules.customers.infrastructure.store import PostgresCustomers
from petland.modules.identity.domain.models import Role, User
from petland.modules.identity.infrastructure.security import ArgonPasswords
from petland.modules.identity.infrastructure.store import PostgresIdentityStore
from petland.modules.pets.domain.models import Pet, Sex, Size
from petland.modules.pets.infrastructure.store import PostgresPets
from petland.modules.scheduling.domain.models import (
    Appointment,
    Calendar,
    Configuration,
    Day,
    Event,
    ExceptionDay,
    Offer,
    Resource,
    Window,
)
from petland.modules.scheduling.domain.operations import Note
from petland.modules.scheduling.infrastructure.models import EventRecord, NoteRecord
from petland.modules.scheduling.infrastructure.store import PostgresSchedule

FIXTURE = "petland-p07-synthetic-v1"
ACCOUNTS = {
    "admin": ("demo-admin@example.com", "Administrador demo", Role.ADMIN),
    "employee": ("demo-equipe@example.com", "Funcionário demo", Role.EMPLOYEE),
    "customer_a": ("demo-cliente-a@example.com", "Tutor A demo", Role.CUSTOMER),
    "customer_b": ("demo-cliente-b@example.com", "Tutor B demo", Role.CUSTOMER),
}


def fixture_id(name):
    return uuid5(NAMESPACE_URL, f"{FIXTURE}/{name}")


def seed(session: Session, passwords: dict[str, str], reference: date) -> dict:
    """Single transaction; never truncate, update or adopt an existing business database."""
    database = session.scalar(text("SELECT current_database()"))
    if database != "petland_demo" and not (
        database.startswith("petland_reset_") and database.endswith("_demo")
    ):
        raise ValueError("Seed requires an explicitly created P07 demo database")
    marker = session.scalar(text("SELECT to_regclass('petland_ops.demo_manifest')"))
    if marker:
        manifest = session.scalar(text("SELECT payload FROM petland_ops.demo_manifest WHERE id=1"))
        if manifest and manifest["fixture"] == FIXTURE:
            return manifest
        raise ValueError("Unknown demo marker; existing data preserved")
    if (
        session.scalar(text("SELECT count(*) FROM users"))
        or session.scalar(text("SELECT count(*) FROM customers"))
        or session.scalar(text("SELECT count(*) FROM appointments"))
        or session.scalar(text("SELECT count(*) FROM services"))
    ):
        raise ValueError("Nonempty unmarked database; existing data preserved")
    zone = ZoneInfo("America/Sao_Paulo")

    def at(days, minute):
        return datetime.combine(reference + timedelta(days=days), time(), zone).astimezone(
            UTC
        ) + timedelta(minutes=minute)

    created = at(-10, 540)
    identities = PostgresIdentityStore(session)
    users = {}
    for key, (email, name, role) in ACCOUNTS.items():
        user = User(
            email,
            name,
            ArgonPasswords().hash(passwords[key]),
            frozenset({role}),
            created,
            id=fixture_id(key),
            verified_at=created,
        )
        identities.save_user(user)
        users[key] = user
    customers = PostgresCustomers(session)
    owners = {}
    for key in ["customer_a", "customer_b"]:
        user = users[key]
        owner = Customer(
            user.display_name,
            user.email,
            "",
            "Endereço fictício de demonstração",
            created,
            created,
            user_id=user.id,
            id=fixture_id(f"owner/{key}"),
        )
        customers.save(owner)
        owners[key] = owner
    pets_store = PostgresPets(session)
    pets = {}
    for name, key, species, size, archived in [
        ("Luna demo", "customer_a", "DOG", Size.SMALL, False),
        ("Thor demo", "customer_a", "DOG", Size.LARGE, False),
        ("Mimi demo", "customer_b", "CAT", Size.SMALL, False),
        ("Nina arquivada demo", "customer_b", "DOG", Size.MEDIUM, True),
    ]:
        pet = Pet(
            owners[key].id,
            name,
            species,
            None,
            size,
            Sex.UNKNOWN,
            None,
            False,
            "Observação fictícia de demonstração",
            created,
            created,
            id=fixture_id(name),
            archived_at=created if archived else None,
        )
        pet.validate(reference)
        pets_store.save(pet)
        pets[name] = pet
    catalog = PostgresCatalog(session)
    services = {}
    for key, name, active, durations in [
        ("bath", "Banho demo", True, [40, 60, 90]),
        ("groom", "Banho e tosa demo", True, [80, 100, 120]),
        ("inactive", "Serviço inativo demo", False, [30, 40, 50]),
    ]:
        service = Service(
            name,
            "Oferta fictícia; valores e tempos apenas para demonstração.",
            ["DOG", "CAT"],
            [
                Option(size, Decimal(50 + i * 25), duration)
                for i, (size, duration) in enumerate(zip(Size, durations, strict=True))
            ],
            active,
            created,
            created,
            id=fixture_id(key),
        )
        service.validate()
        catalog.save(service)
        services[key] = service
    schedule = PostgresSchedule(session)
    config = Configuration(
        enabled=True,
        horizon_days=30,
        step_minutes=20,
        no_show_grace_minutes=15,
        shop_name="PetLand Demo — dados fictícios",
        shop_email="demo-loja@example.com",
        shop_address="Endereço fictício de demonstração",
        calendar=Calendar(
            [Day(d, [Window(540, 720), Window(780, 1080)]) for d in range(7)],
            [
                ExceptionDay(reference + timedelta(days=7), []),
                ExceptionDay(reference + timedelta(days=8), [Window(540, 720)]),
            ],
        ),
    )
    config.validate()
    schedule.save_configuration(config)
    resources = []
    for key in ["employee", "admin"]:
        resource = Resource(
            users[key].id,
            users[key].display_name,
            [services["bath"].id, services["groom"].id],
            id=fixture_id(f"resource/{key}"),
        )
        resource.validate()
        schedule.save_resource(resource)
        resources.append(resource)
    visits = {}
    for key, pet_name, service_key, days, minute, resource, status in [
        ("last_slot_a", "Luna demo", "bath", 1, 540, resources[0], "BOOKED"),
        ("last_slot_b", "Mimi demo", "bath", 1, 540, resources[1], "BOOKED"),
        ("long", "Thor demo", "groom", 1, 840, resources[0], "BOOKED"),
        ("completed", "Luna demo", "bath", -1, 540, resources[0], "COMPLETED"),
        ("cancelled", "Mimi demo", "bath", -2, 540, resources[1], "CANCELLED"),
        ("no_show", "Thor demo", "bath", -2, 840, resources[0], "NO_SHOW"),
    ]:
        pet, service = pets[pet_name], services[service_key]
        option = next(o for o in service.options if o.size == pet.size)
        starts = at(days, minute)
        ends = starts + timedelta(minutes=option.duration_minutes)
        offer = Offer(
            service.id,
            service.name,
            pet.name,
            pet.size,
            option.price,
            option.duration_minutes,
            0,
            0,
            service.version,
        )
        visit = Appointment(
            pet.customer_id,
            pet.id,
            service.id,
            resource.id,
            starts,
            ends,
            starts,
            ends,
            offer,
            config.timezone,
            0,
            created,
            ends,
            id=fixture_id(key),
            status=status,
            version=4 if status == "COMPLETED" else 1 if status == "BOOKED" else 2,
            no_show_grace_minutes=15,
            arrived_at=starts if status == "COMPLETED" else None,
            started_at=starts if status == "COMPLETED" else None,
            completed_at=ends if status == "COMPLETED" else None,
        )
        schedule.save(visit)
        event = Event(
            visit.id,
            users["employee"].id,
            "book",
            "Cenário sintético P07",
            starts,
            ends,
            created,
            id=fixture_id(f"event/{key}"),
        )
        # Seeded history is a fixture, not a claimed SMTP delivery or live reservation.
        session.add(EventRecord(**asdict(event)))
        trail = {
            "COMPLETED": [("arrive", starts), ("start", starts), ("complete", ends)],
            "CANCELLED": [("cancel", starts - timedelta(hours=1))],
            "NO_SHOW": [("no_show", starts + timedelta(minutes=15))],
        }.get(status, [])
        for kind, occurred_at in trail:
            session.add(
                EventRecord(
                    **asdict(
                        Event(
                            visit.id,
                            users["employee"].id,
                            kind,
                            "Cenário sintético P07",
                            starts,
                            ends,
                            occurred_at,
                            id=fixture_id(f"event/{key}/{kind}"),
                        )
                    )
                )
            )
        schedule.audit(users["employee"].id, visit.id, "demo.fixture.created", "p07-seed")
        visits[key] = visit
    for visibility, body in [
        ("INTERNAL", "Nota interna fictícia P07"),
        ("PUBLIC", "Atendimento de demonstração concluído."),
    ]:
        note = Note(
            visits["completed"].id,
            users["employee"].id,
            body,
            visibility,
            visits["completed"].ends_at,
            id=fixture_id(visibility),
        )
        session.add(NoteRecord(**asdict(note)))
    manifest = {
        "fixture": FIXTURE,
        "reference_date": reference.isoformat(),
        "accounts": {k: str(v.id) for k, v in users.items()},
        "customers": {k: str(v.id) for k, v in owners.items()},
        "pets": {k: str(v.id) for k, v in pets.items()},
        "services": {k: str(v.id) for k, v in services.items()},
        "appointments": {k: str(v.id) for k, v in visits.items()},
    }
    session.flush()
    session.execute(text("CREATE SCHEMA petland_ops"))
    session.execute(text("REVOKE ALL ON SCHEMA petland_ops FROM PUBLIC"))
    session.execute(
        text(
            "CREATE TABLE petland_ops.demo_manifest (id integer PRIMARY KEY CHECK(id=1), payload jsonb NOT NULL)"
        )
    )
    session.execute(
        text("INSERT INTO petland_ops.demo_manifest VALUES (1, CAST(:payload AS jsonb))"),
        {"payload": json.dumps(manifest)},
    )
    return manifest
