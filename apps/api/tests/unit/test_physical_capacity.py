from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from petland.modules.scheduling.domain.models import (
    Appointment,
    CapacityPool,
    Configuration,
    Offer,
    physical_fits,
)


def test_services_share_pools_buffers_count_and_sequential_reservations_use_peak_not_sum():
    bath, groom, other = uuid4(), uuid4(), uuid4()
    start = datetime(2026, 10, 1, 12, tzinfo=UTC)
    end = start + timedelta(hours=1)
    offer = Offer(bath, "Banho", "Luna", "SMALL", Decimal("20"), 30, 10, 10, 1)
    first = Appointment(
        uuid4(),
        uuid4(),
        bath,
        uuid4(),
        start,
        start + timedelta(minutes=30),
        start - timedelta(minutes=10),
        start + timedelta(minutes=40),
        offer,
        "UTC",
        0,
        start,
        start,
    )
    second = replace(
        first, id=uuid4(), occupied_start_at=start + timedelta(minutes=40), occupied_end_at=end
    )
    pool = CapacityPool(uuid4(), "Banheira compartilhada", 2, [bath, groom])
    config = Configuration(capacity_pools=[pool])
    # One new groom plus two consecutive baths reaches two, not three.
    assert physical_fits(config, [first, second], groom, start, end)
    assert not physical_fits(
        replace(config, capacity_pools=[replace(pool, capacity=1)]),
        [first],
        groom,
        start - timedelta(minutes=5),
        start,
    )
    assert physical_fits(config, [first, second], other, start, end)
    # Groom additionally requires a free table even when the bath pool has room.
    tables = CapacityPool(uuid4(), "Mesa", 1, [groom])
    occupied_table = replace(first, id=uuid4(), service_id=groom)
    config = replace(config, capacity_pools=[pool, tables])
    assert not physical_fits(config, [occupied_table], groom, start, end)
    assert physical_fits(config, [occupied_table], groom, occupied_table.occupied_end_at, end)
    assert not physical_fits(
        replace(config, capacity_pools=[replace(pool, active=False)]), [], groom, start, end
    )
    assert physical_fits(Configuration(), [first, second], groom, start, end)
