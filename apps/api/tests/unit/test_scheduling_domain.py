from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from petland.modules.scheduling.domain.models import (
    Appointment,
    Calendar,
    Configuration,
    Day,
    ExceptionDay,
    Offer,
    Resource,
    Window,
    allocate,
    candidates,
    fits,
    local_instant,
)
from petland.shared.domain.errors import BusinessError


def test_dst_nonexistent_and_ambiguous_wall_times_are_not_sold():
    zone = ZoneInfo("America/New_York")
    assert local_instant(date(2026, 3, 8), 150, zone) is None
    assert local_instant(date(2026, 11, 1), 90, zone) is None
    assert local_instant(date(2026, 3, 8), 210, zone) == datetime(2026, 3, 8, 7, 30, tzinfo=UTC)


def test_lead_horizon_and_grid_are_configured_not_service_duration():
    now = datetime(2026, 10, 5, 12, tzinfo=UTC)
    config = Configuration(enabled=True, lead_minutes=40, horizon_days=2, step_minutes=15)
    starts = candidates(config, now.date(), now)
    assert starts[0] == now + timedelta(minutes=45)
    assert candidates(config, now.date() + timedelta(days=3), now) == []
    assert candidates(config, now.date() - timedelta(days=1), now) == []


def test_full_buffer_interval_fits_and_adjacency_respects_resource_and_pet():
    start = datetime(2026, 10, 5, 12, tzinfo=UTC)
    service, pet, customer = uuid4(), uuid4(), uuid4()
    offer = Offer(
        service, "Banho sintético", "Pet sintético", "SMALL", Decimal("80"), 40, 15, 15, 1
    )
    resource = Resource(uuid4(), "Pessoa sintética", [service])
    config = Configuration(enabled=True, calendar=Calendar([Day(0, [Window(540, 720)])]))
    assert (
        allocate(config, [resource], [], pet, offer, start) is None
    )  # preparation starts before opening
    first = start + timedelta(minutes=15)
    assert allocate(config, [resource], [], pet, offer, first) == resource
    appointment = Appointment(
        customer,
        pet,
        service,
        resource.id,
        first,
        first + timedelta(minutes=40),
        start,
        first + timedelta(minutes=55),
        offer,
        config.timezone,
        0,
        start,
        start,
    )
    assert (
        allocate(config, [resource], [appointment], uuid4(), offer, first + timedelta(minutes=60))
        is None
    )
    assert (
        allocate(config, [resource], [appointment], uuid4(), offer, first + timedelta(minutes=70))
        == resource
    )


def test_date_override_and_worker_calendar_intersect_with_shop():
    day = date(2026, 10, 5)
    config = Configuration(calendar=Calendar([Day(0, [Window(540, 720)])]))
    resource = Resource(uuid4(), "Pessoa", [], calendar=Calendar([Day(0, [Window(480, 600)])]))
    at = datetime(2026, 10, 5, 12, tzinfo=UTC)
    assert fits(config, resource, at, at + timedelta(hours=1))
    assert not fits(config, resource, at - timedelta(hours=1), at)
    resource.calendar.exceptions = [ExceptionDay(day, [])]
    assert not fits(config, resource, at, at + timedelta(minutes=30))


@pytest.mark.parametrize(
    "calendar",
    [
        Calendar([Day(0, [Window(600, 540)])]),
        Calendar([Day(0, [Window(540, 650), Window(600, 700)])]),
        Calendar([Day(0, []), Day(0, [])]),
        Calendar(
            exceptions=[ExceptionDay(date(2026, 10, 5), []), ExceptionDay(date(2026, 10, 5), [])]
        ),
    ],
)
def test_invalid_calendar_is_rejected(calendar):
    with pytest.raises(BusinessError, match="INVALID_CALENDAR"):
        calendar.validate()
