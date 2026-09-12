"""Magnitude-of-completeness estimation for the EPIP earthquake catalog."""

from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Iterable

from .events import CatalogEvent


@dataclass(frozen=True)
class CompletenessResult:
    """Reproducible magnitude-completeness result."""

    mc: float
    bin_width: float
    method: str
    sample_size: int
    quality: str


def estimate_mc(
    events: Iterable[CatalogEvent],
    *,
    bin_width: float = 0.1,
) -> CompletenessResult:
    """
    Estimate Mc using the maximum-curvature point of the
    magnitude-frequency distribution.

    This is a first reproducible implementation. More advanced
    methods such as GFT/EMR can be added later and compared.
    """

    if bin_width <= 0:
        raise ValueError("bin_width must be > 0")

    magnitudes = sorted(
        event.magnitude
        for event in events
        if event.magnitude is not None
    )

    if len(magnitudes) < 10:
        raise ValueError(
            "at least 10 events with magnitudes are required"
        )

    minimum = min(magnitudes)
    maximum = max(magnitudes)

    bins: list[float] = []
    current = (
        int(minimum / bin_width) * bin_width
    )

    while current <= maximum:
        bins.append(round(current, 10))
        current += bin_width

    counts: list[int] = []

    for lower in bins:
        upper = lower + bin_width
        counts.append(
            sum(
                1
                for magnitude in magnitudes
                if lower <= magnitude < upper
            )
        )

    if not counts or max(counts) <= 0:
        raise ValueError("unable to construct magnitude distribution")

    max_index = counts.index(max(counts))
    mc = bins[max_index]

    quality = "provisional"

    if len(magnitudes) >= 100:
        quality = "usable"

    if len(magnitudes) >= 500:
        quality = "good"

    return CompletenessResult(
        mc=mc,
        bin_width=bin_width,
        method="maximum_curvature",
        sample_size=len(magnitudes),
        quality=quality,
    )


def filter_complete_catalog(
    events: Iterable[CatalogEvent],
    mc: float,
) -> list[CatalogEvent]:
    """Return events at or above the estimated completeness magnitude."""

    return sorted(
        (
            event
            for event in events
            if event.magnitude is not None
            and event.magnitude >= mc
        ),
        key=lambda event: event.time,
    )
