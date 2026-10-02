from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from uuid import UUID

from petland.modules.customers.application.ports import CustomerStore, Mailer, Tokens
from petland.modules.customers.domain.models import Claim, Customer
from petland.modules.identity.public import Actor
from petland.shared.domain.errors import BusinessError


class Customers:
    def __init__(
        self,
        store: Callable[[], AbstractContextManager[CustomerStore]],
        tokens: Tokens,
        mailer: Mailer,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.store, self.tokens, self.mailer, self.clock = store, tokens, mailer, clock

    def own(self, actor: Actor) -> Customer | None:
        actor.require("customer:own")
        with self.store() as store:
            return store.own(actor.id)

    def get(self, actor: Actor, customer_id: UUID) -> Customer:
        actor.require("customer:assist")
        with self.store() as store:
            return store.get(customer_id)

    def search(
        self, actor: Actor, query: str, offset: int, limit: int
    ) -> tuple[list[Customer], int]:
        actor.require("customer:assist")
        with self.store() as store:
            return store.search(query, offset, limit)

    def create(
        self,
        actor: Actor,
        name: str,
        email: str,
        phone: str,
        address: str,
        assisted: bool,
        request_id: str,
    ) -> Customer:
        actor.require("customer:assist" if assisted else "customer:own")
        now = self.clock()
        with self.store() as store:
            if not assisted:
                store.lock_owner(actor.id)
                if store.own(actor.id):
                    raise BusinessError("PROFILE_EXISTS", 409)
            customer = Customer(
                name,
                email if assisted else actor.email,
                phone,
                address,
                now,
                now,
                user_id=None if assisted else actor.id,
            )
            store.save(customer)
            store.audit(actor.id, customer.id, "customer.created", request_id)
            return customer

    def edit(
        self,
        actor: Actor,
        customer_id: UUID | None,
        name: str,
        email: str,
        phone: str,
        address: str,
        version: int,
        request_id: str,
    ) -> Customer:
        actor.require("customer:assist" if customer_id else "customer:own")
        with self.store() as store:
            if customer_id is None:
                own = store.own(actor.id)
                if not own:
                    raise BusinessError("NOT_FOUND", 404)
                customer_id = own.id
                email = actor.email
            customer = store.get(customer_id, lock=True)
            customer.edit(name, email, phone, address, version, self.clock())
            store.save(customer)
            store.invalidate_claims(customer.id)
            store.audit(actor.id, customer.id, "customer.updated", request_id)
            return customer

    def invite(self, actor: Actor, customer_id: UUID, request_id: str) -> None:
        actor.require("customer:assist")
        token = self.tokens.new()
        with self.store() as store:
            customer = store.get(customer_id, lock=True)
            if customer.user_id:
                raise BusinessError("PROFILE_EXISTS", 409)
            store.invalidate_claims(customer.id)
            store.save_claim(
                Claim(
                    customer.id,
                    customer.email,
                    self.tokens.digest(token),
                    self.clock() + timedelta(hours=24),
                )
            )
            store.audit(actor.id, customer.id, "customer.claim_requested", request_id)
        self.mailer.send(customer.email, "customer-claim", token)

    def accept(self, actor: Actor, token: str, request_id: str) -> Customer:
        actor.require("customer:own")
        with self.store() as store:
            store.lock_owner(actor.id)
            claim = store.claim(self.tokens.digest(token))
            if not claim:
                raise BusinessError("INVALID_TOKEN")
            customer = store.get(claim.customer_id, lock=True)
            # Refresh after obtaining the customer lock: two requests cannot consume one claim.
            claim = store.claim(self.tokens.digest(token))
            if (
                not claim
                or claim.used_at
                or claim.expires_at <= self.clock()
                or claim.email != actor.email
                or customer.email != actor.email
                or customer.user_id is not None
            ):
                raise BusinessError("INVALID_TOKEN")
            if store.own(actor.id):
                raise BusinessError("PROFILE_EXISTS", 409)
            customer.user_id = actor.id
            customer.version += 1
            customer.updated_at = self.clock()
            store.save(customer)
            store.invalidate_claims(customer.id)
            store.audit(actor.id, customer.id, "customer.linked", request_id)
            return customer
