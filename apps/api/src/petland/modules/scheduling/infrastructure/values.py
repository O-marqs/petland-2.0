import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from petland.modules.scheduling.domain.models import (
    Appointment,
    Calendar,
    CapacityPool,
    Configuration,
    Day,
    ExceptionDay,
    Offer,
    StaffDay,
    StaffShift,
    Window,
)


def document(value: Any) -> dict[str, Any]:
    result: dict[str, Any] = json.loads(json.dumps(asdict(value), default=str))
    return result


def calendar_value(value: dict[str, Any]) -> Calendar:
    return Calendar(
        [Day(d["weekday"], [Window(**w) for w in d["windows"]]) for d in value["weekly"]],
        [
            ExceptionDay(date.fromisoformat(d["date"]), [Window(**w) for w in d["windows"]])
            for d in value["exceptions"]
        ],
    )


def configuration_value(value: dict[str, Any]) -> Configuration:
    return Configuration(
        **{
            **value,
            "calendar": calendar_value(value["calendar"]),
            "staff_days": [
                StaffDay(
                    date.fromisoformat(d["date"]),
                    [
                        StaffShift(UUID(s["resource_id"]), [Window(**w) for w in s["windows"]])
                        for s in d["shifts"]
                    ],
                    d["reason"],
                )
                for d in value.get("staff_days", [])
            ],
            "capacity_pools": [
                CapacityPool(
                    UUID(p["id"]),
                    p["name"],
                    p["capacity"],
                    [UUID(s) for s in p["service_ids"]],
                    p["active"],
                )
                for p in value.get("capacity_pools", [])
            ],
        }
    )


def offer_value(value: dict[str, Any]) -> Offer:
    return Offer(
        **{**value, "service_id": UUID(value["service_id"]), "price": Decimal(value["price"])}
    )


def appointment_value(value: dict[str, Any]) -> Appointment:
    data = dict(value)
    for name in ("id", "customer_id", "pet_id", "service_id", "resource_id"):
        data[name] = UUID(str(data[name]))
    for name in (
        "starts_at",
        "ends_at",
        "occupied_start_at",
        "occupied_end_at",
        "created_at",
        "updated_at",
        "arrived_at",
        "started_at",
        "completed_at",
        "reserved_until",
    ):
        if isinstance(data.get(name), str):
            data[name] = datetime.fromisoformat(data[name])
    data["offer"] = offer_value(data["offer"])
    return Appointment(**data)
