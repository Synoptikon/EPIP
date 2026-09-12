"""Gutenberg-Richter magnitude-frequency analysis for EPIP."""

from __future__ import annotations

from dataclasses import dataclass
from math import log10, sqrt
from typing import Iterable

from .events import CatalogEvent


@dataclass(frozen=True)
class GutenbergRichterResult:
    """Maximum-likelihood Gutenberg-Richter parameters."""

    mc: float
    bin_width: float
    sample_size: int
    mean_magnitude: float
    b_value: float
    a_value: float
    standard_error: float
    magnitude_min: float
    magnitude_max: float


def fit_gutenberg_richter(
    events: Iterable[CatalogEvent],
    *,
    mc: float,
    bin_width: float = 0.1,
) -> GutenbergRichterResult:
    """
    Fit the Gutenberg-Richter relation above Mc.

    Uses the maximum-likelihood estimator:

        b = log10(e) / (mean(M) - Mmin)

    with the half-bin correction Mmin = Mc - bin_width / 2.
    """

    if bin_width <= 0:
        raise ValueError("bin_width must be > 0")

    magnitudes = sorted(
        event.magnitude
        for event in events
        if event.magnitude is not None
        and event.magnitude >= mc
    )

    if len(magnitudes) < 10:
        raise ValueError(
            "at least 10 complete events are required"
        )

    mean_magnitude = sum(magnitudes) / len(magnitudes)

    magnitude_min = mc - (bin_width / 2.0)

    denominator = mean_magnitude - magnitude_min

    if denominator <= 0:
        raise ValueError(
            "invalid magnitude distribution for b-value estimation"
        )

    b_value = log10(2.718281828459045) / denominator

    # Standard uncertainty approximation for the MLE b-value.
    standard_error = (
        2.30 * b_value / sqrt(len(magnitudes))
    )

    # a-value is defined for the cumulative relation:
    #
    # log10 N(M >= m) = a - b*m
    #
    # Here N is the sample count, so this is the catalog-level
    # intercept rather than an annualized rate.
    a_value = log10(len(magnitudes)) + b_value * mc

    return GutenbergRichterResult(
        mc=mc,
        bin_width=bin_width,
        sample_size=len(magnitudes),
        mean_magnitude=mean_magnitude,
        b_value=b_value,
        a_value=a_value,
        standard_error=standard_error,
        magnitude_min=min(magnitudes),
        magnitude_max=max(magnitudes),
    )


def events_duration_years(
    magnitudes: Iterable[float],
) -> float:
    """
    Placeholder helper kept private to the scientific API.

    Duration is intentionally not inferred from magnitudes.
    Annualized rates belong to the catalog-rate layer.
    """

    raise RuntimeError(
        "duration must be calculated from event timestamps"
    )
