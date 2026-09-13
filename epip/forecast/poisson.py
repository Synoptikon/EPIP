"""Baseline Poisson probabilistic forecast for prospective testing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp

from epip.prospective import ForecastRecord


DAYS_PER_YEAR = 365.25


@dataclass(frozen=True)
class PoissonForecastModel:
    """Transparent baseline model using a stationary observed event rate.

    MODEL: event arrivals are represented by a homogeneous Poisson process
    over the selected forecast interval. This is a baseline assumption, not
    a claim that earthquake occurrence is globally Poisson or stationary.
    """

    rate_per_year: float
    model_version: str = "poisson-baseline-1"

    def __post_init__(self) -> None:
        if self.rate_per_year < 0:
            raise ValueError("rate_per_year must be >= 0")
        if not self.model_version.strip():
            raise ValueError("model_version must not be empty")

    def probability(self, horizon_days: float) -> float:
        """Return P(N >= 1) for the requested horizon."""
        if horizon_days < 0:
            raise ValueError("horizon_days must be >= 0")
        years = horizon_days / DAYS_PER_YEAR
        return 1.0 - exp(-self.rate_per_year * years)

    def forecast(
        self,
        *,
        generated_at: datetime,
        region: str,
        horizon_days: float,
        minimum_magnitude: float,
    ) -> ForecastRecord:
        """Create an auditable forecast record from the baseline model."""
        return ForecastRecord(
            generated_at=generated_at,
            region=region,
            horizon_hours=horizon_days * 24.0,
            minimum_magnitude=minimum_magnitude,
            probability=self.probability(horizon_days),
            model_version=self.model_version,
        )
