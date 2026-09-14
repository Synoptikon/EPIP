"""Seismicity-rate calculations for the EPIP complete catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp
from typing import Iterable

from .events import CatalogEvent


SECONDS_PER_YEAR = 365.25 * 24.0 * 3600.0


@dataclass(frozen=True)
class SeismicRate:
    """Observed seismicity rate above a completeness threshold."""

    mc: float
    event_count: int
    duration_years: float
    rate_per_year: float


def calculate_rate(
    events: Iterable[CatalogEvent],
    *,
    mc: float,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> SeismicRate:
    """Calculate the observed annual rate for M >= Mc.

    When ``start_time`` and ``end_time`` are supplied, the rate denominator is
    the declared observation window rather than the span between the first
    and last observed events. This prevents event clustering from silently
    changing the exposure duration used by the forecast model.

    If no window is supplied, the historical event-span behavior is retained
    for backward compatibility.
    """

    catalog = sorted(events, key=lambda event: event.time)

    if not catalog:
        raise ValueError("catalog must not be empty")

    if mc < -2.0 or mc > 10.0:
        raise ValueError("mc must be between -2 and 10")

    if (start_time is None) != (end_time is None):
        raise ValueError("start_time and end_time must be supplied together")

    if start_time is not None and end_time is not None:
        if start_time.tzinfo is None or start_time.utcoffset() is None:
            raise ValueError("start_time must be timezone-aware")
        if end_time.tzinfo is None or end_time.utcoffset() is None:
            raise ValueError("end_time must be timezone-aware")
        start = start_time.astimezone(timezone.utc)
        end = end_time.astimezone(timezone.utc)
        if not start < end:
            raise ValueError("start_time must be before end_time")
    else:
        start = catalog[0].time.astimezone(timezone.utc)
        end = catalog[-1].time.astimezone(timezone.utc)

    complete = [
        event
        for event in catalog
        if event.magnitude is not None
        and event.magnitude >= mc
    ]

    if len(complete) < 1:
        raise ValueError("no events at or above Mc")

    duration_seconds = (end - start).total_seconds()
    if duration_seconds <= 0:
        raise ValueError("catalog duration must be greater than zero")

    duration_years = duration_seconds / SECONDS_PER_YEAR
    rate = len(complete) / duration_years

    return SeismicRate(
        mc=mc,
        event_count=len(complete),
        duration_years=duration_years,
        rate_per_year=rate,
    )


def poisson_probability(
    rate_per_year: float,
    *,
    duration_days: float,
) -> float:
    """Probability of at least one event during a time window."""

    if rate_per_year < 0:
        raise ValueError("rate_per_year must be >= 0")

    if duration_days < 0:
        raise ValueError("duration_days must be >= 0")

    duration_years = duration_days / 365.25

    probability = 1.0 - exp(
        -rate_per_year * duration_years
    )

    return max(0.0, min(1.0, probability))


def poisson_horizons(
    rate_per_year: float,
) -> dict[str, float]:
    """Return Poisson probabilities for EPIP forecast horizons."""

    return {
        "24h": poisson_probability(
            rate_per_year,
            duration_days=1.0,
        ),
        "7d": poisson_probability(
            rate_per_year,
            duration_days=7.0,
        ),
        "30d": poisson_probability(
            rate_per_year,
            duration_days=30.0,
        ),
        "90d": poisson_probability(
            rate_per_year,
            duration_days=90.0,
        ),
    }
