"""Prospective forecast contracts and leakage-safe evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from epip.catalog.events import CatalogEvent


@dataclass(frozen=True)
class ForecastRecord:
    """Immutable forecast generated from information available at a cutoff."""

    generated_at: datetime
    region: str
    horizon_hours: float
    minimum_magnitude: float
    probability: float
    model_version: str

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if self.horizon_hours <= 0:
            raise ValueError("horizon_hours must be > 0")
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if not self.model_version.strip():
            raise ValueError("model_version must not be empty")

    @property
    def expires_at(self) -> datetime:
        return self.generated_at.astimezone(timezone.utc) + timedelta(hours=self.horizon_hours)


@dataclass(frozen=True)
class ProspectiveOutcome:
    """Observed binary outcome and Brier contribution for one forecast."""

    occurred: bool
    observed_event_ids: tuple[str, ...]
    brier_score: float


def evaluate_forecast(
    forecast: ForecastRecord,
    events: Iterable[CatalogEvent],
    *,
    region_match: callable | None = None,
) -> ProspectiveOutcome:
    """Evaluate only events strictly after generation and before expiry.

    ``region_match`` is supplied by the caller because spatial semantics are
    model-dependent and must not be silently invented by the evaluator.
    """

    generated_at = forecast.generated_at.astimezone(timezone.utc)
    expiry = forecast.expires_at
    observed_ids: list[str] = []

    for event in events:
        event_time = event.time.astimezone(timezone.utc)
        if not (generated_at < event_time <= expiry):
            continue
        if event.magnitude is None or event.magnitude < forecast.minimum_magnitude:
            continue
        if region_match is not None and not region_match(event):
            continue
        observed_ids.append(event.event_id)

    occurred = bool(observed_ids)
    outcome = 1.0 if occurred else 0.0
    brier_score = (forecast.probability - outcome) ** 2

    return ProspectiveOutcome(
        occurred=occurred,
        observed_event_ids=tuple(observed_ids),
        brier_score=brier_score,
    )
