from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, TypeVar

T = TypeVar("T")
CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def hours_between(later: str | None, earlier: str | None) -> Decimal | None:
    left = parse_timestamp(later)
    right = parse_timestamp(earlier)
    if left is None or right is None:
        return None
    value = Decimal(str((left - right).total_seconds())) / Decimal("3600")
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def unique_in_order(values: Iterable[T]) -> list[T]:
    result: list[T] = []
    seen: set[T] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
