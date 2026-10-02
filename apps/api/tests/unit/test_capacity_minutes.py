from datetime import UTC, date, datetime
from uuid import uuid4

from petland.modules.scheduling.domain.models import (
    Calendar,
    Configuration,
    Day,
    Resource,
    StaffDay,
    StaffShift,
    Window,
)
from petland.modules.scheduling.domain.operations import available_minutes_by_resource


def test_capacity_clips_each_person_and_overrides_only_the_roster_date():
    service = uuid4()
    inherited = Resource(uuid4(), "Habitual", [service])
    own = Resource(
        uuid4(),
        "Individual",
        [service],
        calendar=Calendar([Day(d, [Window(540, 600)]) for d in [4, 5]]),
    )
    omitted = Resource(uuid4(), "Fora da escala pontual", [service])
    inactive = Resource(uuid4(), "Inativa", [service], active=False)
    unskilled = Resource(uuid4(), "Sem serviços", [])
    config = Configuration(
        enabled=True,
        calendar=Calendar([Day(d, [Window(540, 720)]) for d in [4, 5]]),
        staff_days=[
            StaffDay(
                date(2026, 10, 2),
                [
                    StaffShift(inherited.id, [Window(600, 720)]),
                    StaffShift(own.id, [Window(540, 660)]),
                ],
                "Exceção da sexta-feira",
            )
        ],
    )
    result = available_minutes_by_resource(
        config,
        [inherited, own, omitted, inactive, unskilled],
        datetime(2026, 10, 2, 13, tzinfo=UTC),
        datetime(2026, 10, 3, 14, tzinfo=UTC),
    )
    assert result == {
        inherited.id: 240,
        own.id: 120,
        omitted.id: 120,
        inactive.id: 0,
        unskilled.id: 0,
    }


def test_capacity_does_not_guess_nonexistent_dst_boundaries():
    person = Resource(uuid4(), "Pessoa", [uuid4()])
    config = Configuration(
        timezone="Europe/Paris",
        enabled=True,
        calendar=Calendar([Day(6, [Window(120, 180)])]),
    )
    result = available_minutes_by_resource(
        config,
        [person],
        datetime(2026, 3, 29, tzinfo=UTC),
        datetime(2026, 3, 30, tzinfo=UTC),
    )
    assert result[person.id] == 0
