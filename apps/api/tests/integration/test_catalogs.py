import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from test_identity import identity as identity_fixture
from test_identity import identity_engine as engine_fixture
from test_identity import login, mutate, register

from petland.bootstrap.app import create_app
from petland.bootstrap.settings import Settings
from petland.modules.customers.application.service import Customers
from petland.modules.customers.infrastructure.store import customer_store
from petland.modules.identity.domain.models import Role
from petland.modules.identity.infrastructure.security import SecureTokens
from petland.shared.domain.errors import BusinessError

identity = identity_fixture
identity_engine = engine_fixture
pytestmark = pytest.mark.integration
CONTACT = {
    "name": "Pessoa sintética",
    "email": "cliente@example.com",
    "phone": "(11) 99999-1234",
    "address": "Endereço de teste",
}
PET = {
    "name": "Luna de teste",
    "species_id": "DOG",
    "size": "SMALL",
    "care_notes": "Cuidado sintético",
}
SERVICE = {
    "name": "Banho de teste",
    "description": "Dados sintéticos de teste",
    "species_ids": ["DOG"],
    "options": [
        {"size": "SMALL", "price": "80.25", "duration_minutes": 40},
        {"size": "LARGE", "price": "120.50", "duration_minutes": 90},
    ],
    "active": True,
}


@pytest.fixture
def crm(identity, identity_engine):
    with identity_engine.begin() as conn:
        conn.execute(text("TRUNCATE services CASCADE"))
    identity_service, mailbox, now, _ = identity
    customers = Customers(
        lambda: customer_store(identity_engine), SecureTokens(), mailbox, lambda: now[0]
    )
    settings = Settings(
        _env_file=None, app_env="test", database_url=os.environ["TEST_DATABASE_URL"]
    )
    with TestClient(
        create_app(settings, identity=identity_service, customers=customers),
        headers={"Origin": "http://localhost:5173"},
    ) as client:
        yield identity_service, mailbox, now, customers, client


def account(crm, email="cliente@example.com", staff=False):
    identity, mailbox, _, _, client = crm
    user = register(identity, mailbox, email, roles=[Role.EMPLOYEE] if staff else None)
    login(client, email)
    return user


def test_own_profile_derived_owner_minimum_data_and_staff_search(crm):
    client = crm[-1]
    actor = account(crm)
    assert client.get("/api/v1/me/customer").json() is None
    injected = mutate(client, "POST", "/me/customer", {**CONTACT, "user_id": str(uuid4())})
    assert injected.status_code == 422
    response = mutate(client, "POST", "/me/customer", {**CONTACT, "email": "different@example.com"})
    assert response.status_code == 201, response.text
    own = response.json()
    assert own["email"] == actor.email and own["phone"] == "11999991234" and own["linked"]
    assert "user_id" not in own
    assert mutate(client, "POST", "/me/customer", CONTACT).status_code == 409
    assert client.get("/api/v1/operations/customers").status_code == 403
    assert (
        mutate(
            client, "PUT", "/me/customer", {**CONTACT, "name": "Nome atualizado", "version": 1}
        ).status_code
        == 200
    )
    assert mutate(client, "PUT", "/me/customer", {**CONTACT, "version": 1}).status_code == 409
    account(crm, "equipe@example.com", staff=True)
    assert client.get("/api/v1/operations/customers?q=Nome").json()["total"] == 1
    assert client.get("/api/v1/operations/customers?q=%25").json()["total"] == 0
    assert client.get("/api/v1/operations/customers?limit=101").status_code == 422
    edit = mutate(
        client,
        "PUT",
        "/operations/customers/" + own["id"],
        {**CONTACT, "email": "other@example.com", "version": 2},
    )
    assert edit.json()["code"] == "LINKED_EMAIL"
    assert client.get("/api/v1/management/users").status_code == 403


def test_no_auto_link_claim_matches_verified_email_and_preserves_assisted_pets(
    crm, identity_engine
):
    identity, mailbox, _, _, client = crm
    account(crm, "staff@example.com", staff=True)
    response = mutate(client, "POST", "/operations/customers", CONTACT)
    customer = response.json()
    assert response.status_code == 201 and not customer["linked"]
    pet = mutate(client, "POST", f"/operations/customers/{customer['id']}/pets", PET).json()
    assert (
        mutate(
            client, "POST", f"/operations/customers/{customer['id']}/claim-invitations"
        ).status_code
        == 202
    )
    token = mailbox.messages[-1][2]
    account(crm, "wrong@example.com")
    assert mutate(client, "POST", "/me/customer-claims", {"token": token}).status_code == 400
    identity.register(CONTACT["email"], CONTACT["name"], "Um passeio feliz pelo jardim 42!", "test")
    verification = mailbox.messages[-1][2]
    login(client)
    assert mutate(client, "POST", "/me/customer-claims", {"token": token}).status_code == 403
    identity.consume_token(verification, "verify", None, "test")
    assert client.get("/api/v1/me/customer").json() is None
    assert mutate(client, "POST", "/me/customer-claims", {"token": token}).status_code == 200
    assert client.get("/api/v1/me/customer").json()["id"] == customer["id"]
    assert client.get("/api/v1/me/pets").json()["items"][0]["id"] == pet["id"]
    assert mutate(client, "POST", "/me/customer-claims", {"token": token}).status_code == 400
    with identity_engine.connect() as conn:
        assert token not in str(conn.execute(text("SELECT * FROM customer_claims")).all())
        assert token not in str(conn.execute(text("SELECT * FROM audit_events")).all())


def test_claim_resend_edit_expiry_and_existing_profile_conflict(crm):
    _, mailbox, now, customers, client = crm
    staff = account(crm, "staff@example.com", staff=True)
    customer = customers.create(staff, **CONTACT, assisted=True, request_id="test")
    customers.invite(staff, customer.id, "test")
    old = mailbox.messages[-1][2]
    customers.invite(staff, customer.id, "test")
    current = mailbox.messages[-1][2]
    user = account(crm)
    with pytest.raises(BusinessError, match="INVALID_TOKEN"):
        customers.accept(user, old, "test")
    now[0] += timedelta(hours=25)
    with pytest.raises(BusinessError, match="INVALID_TOKEN"):
        customers.accept(user, current, "test")
    customers.invite(staff, customer.id, "test")
    stale = mailbox.messages[-1][2]
    customers.edit(staff, customer.id, **CONTACT, version=1, request_id="test")
    with pytest.raises(BusinessError, match="INVALID_TOKEN"):
        customers.accept(user, stale, "test")
    customers.invite(staff, customer.id, "test")
    customers.create(user, **CONTACT, assisted=False, request_id="test")
    with pytest.raises(BusinessError, match="PROFILE_EXISTS"):
        customers.accept(user, mailbox.messages[-1][2], "test")


def test_concurrent_claim_and_profile_creation_use_one_owner(crm, identity_engine):
    _, mailbox, _, customers, _ = crm
    staff = account(crm, "staff@example.com", staff=True)
    customer = customers.create(staff, **CONTACT, assisted=True, request_id="test")
    customers.invite(staff, customer.id, "test")
    token = mailbox.messages[-1][2]
    user = account(crm)

    def accept():
        try:
            return customers.accept(user, token, "concurrent").id
        except BusinessError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: accept(), range(2)))
    assert results.count(customer.id) == 1 and results.count("INVALID_TOKEN") == 1
    with identity_engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT count(*) FROM customers WHERE user_id=:id"), {"id": user.id}
            ).scalar_one()
            == 1
        )


def test_owner_isolation_archive_restore_and_stale_edits(crm):
    client = crm[-1]
    account(crm)
    own = mutate(client, "POST", "/me/customer", CONTACT).json()
    created = mutate(client, "POST", "/me/pets", PET)
    assert created.status_code == 201, created.text
    pet = created.json()
    assert pet["birth_date"] is None and pet["breed_id"] is None
    path = "/me/pets/" + pet["id"]
    account(crm, "other@example.com")
    mutate(client, "POST", "/me/customer", CONTACT)
    assert client.get("/api/v1/me/pets").json()["total"] == 0
    assert client.get("/api/v1" + path).status_code == 404
    assert mutate(client, "PUT", path, {**PET, "version": 1}).status_code == 404
    assert (
        mutate(client, "PATCH", path + "/archive", {"archived": True, "version": 1}).status_code
        == 404
    )
    assert client.get(f"/api/v1/operations/customers/{own['id']}/pets").status_code == 403
    # Supplying a query owner on the self URL cannot alter the ownership scope.
    assert client.get(f"/api/v1/me/pets?customer_id={own['id']}").json()["total"] == 0
    login(client)
    assert (
        mutate(client, "PUT", path, {**PET, "name": "Luna editada", "version": 1}).status_code
        == 200
    )
    assert mutate(client, "PUT", path, {**PET, "version": 1}).status_code == 409
    assert (
        mutate(client, "PATCH", path + "/archive", {"archived": True, "version": 2}).status_code
        == 200
    )
    assert client.get("/api/v1/me/pets").json()["total"] == 0
    assert client.get("/api/v1/me/pets?archived=true").json()["total"] == 1
    assert client.get("/api/v1" + path).status_code == 200
    assert mutate(client, "PUT", path, {**PET, "version": 3}).json()["code"] == "PET_ARCHIVED"
    assert (
        mutate(client, "PATCH", path + "/archive", {"archived": False, "version": 3}).status_code
        == 200
    )
    assert client.get("/api/v1/me/pets").json()["total"] == 1


def test_pet_reference_validation_and_database_constraint(crm, identity_engine):
    client = crm[-1]
    account(crm)
    mutate(client, "POST", "/me/customer", CONTACT)
    cat_breed = client.get("/api/v1/catalog/breeds?species_id=CAT").json()[0]["id"]
    for data in [
        {**PET, "breed_id": cat_breed},
        {**PET, "species_id": "INVALID"},
        {**PET, "birth_date": "2999-01-01"},
        {**PET, "birth_estimated": True},
        {**PET, "size": "INVALID"},
        {**PET, "customer_id": str(uuid4())},
    ]:
        assert mutate(client, "POST", "/me/pets", data).status_code == 422
    pet = mutate(client, "POST", "/me/pets", PET).json()
    with pytest.raises(IntegrityError), identity_engine.begin() as conn:
        conn.execute(
            text("UPDATE pets SET breed_id=:breed WHERE id=:id"),
            {"breed": UUID(cat_breed), "id": UUID(pet["id"])},
        )


def test_catalog_public_offers_filter_exact_money_inactivation_and_versions(crm, identity_engine):
    client = crm[-1]
    account(crm, "staff@example.com", staff=True)
    response = mutate(client, "POST", "/operations/services", SERVICE)
    assert response.status_code == 201, response.text
    service = response.json()
    assert service["currency"] == "BRL"
    assert {o["price"] for o in service["options"]} == {"80.25", "120.50"}
    public = "/api/v1/catalog/services"
    assert client.get(public + "?species_id=DOG&size=SMALL").json()["total"] == 1
    assert client.get(public + "?species_id=CAT").json()["total"] == 0
    assert client.get(public + "?size=MEDIUM").json()["total"] == 0
    path = "/operations/services/" + service["id"]
    edited = mutate(client, "PUT", path, {**SERVICE, "active": False, "version": 1})
    assert edited.status_code == 200
    assert client.get(public).json()["total"] == 0
    assert client.get(public + "/" + service["id"]).status_code == 404
    assert mutate(client, "PUT", path, {**SERVICE, "version": 1}).status_code == 409
    assert mutate(client, "PUT", path, {**SERVICE, "version": 2}).status_code == 200
    account(crm, "customer@example.com")
    assert client.get("/api/v1/operations/services").status_code == 403
    assert mutate(client, "POST", "/operations/services", SERVICE).status_code == 403
    assert client.get(public + "/" + service["id"]).status_code == 200
    with identity_engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT count(*) FROM audit_events WHERE action LIKE 'service.%'")
            ).scalar_one()
            == 3
        )


@pytest.mark.parametrize(
    "change",
    [
        {"options": []},
        {"options": [{"size": "SMALL", "price": "-1", "duration_minutes": 40}]},
        {"options": [{"size": "SMALL", "price": "1.123", "duration_minutes": 40}]},
        {"options": [{"size": "SMALL", "price": "10", "duration_minutes": 0}]},
        {"options": [{"size": "SMALL", "price": "10", "duration_minutes": 40.5}]},
        {"options": [SERVICE["options"][0], SERVICE["options"][0]]},
        {"species_ids": ["INVALID"]},
        {"species_ids": ["DOG", "DOG"]},
    ],
)
def test_invalid_offers_never_persist(crm, change):
    client = crm[-1]
    account(crm, "staff@example.com", staff=True)
    assert mutate(client, "POST", "/operations/services", {**SERVICE, **change}).status_code == 422
    assert client.get("/api/v1/catalog/services").json()["total"] == 0


def test_crm_auth_csrf_unverified_and_disabled_accounts(crm):
    identity, mailbox, _, _, client = crm
    assert client.get("/api/v1/operations/customers").status_code == 401
    identity.register(CONTACT["email"], CONTACT["name"], "Um passeio feliz pelo jardim 42!", "test")
    login(client)
    assert mutate(client, "POST", "/me/customer", CONTACT).status_code == 403
    identity.consume_token(mailbox.messages[-1][2], "verify", None, "test")
    assert client.post("/api/v1/me/customer", json=CONTACT).status_code == 403
    assert (
        mutate(
            client, "POST", "/me/customer", CONTACT, Origin="https://untrusted.example"
        ).status_code
        == 403
    )
    with identity.uow() as work:
        user = work.store.user(email=CONTACT["email"], lock=True)
        user.status = "DISABLED"
        work.store.save_user(user)
    assert client.get("/api/v1/me/customer").status_code == 401
