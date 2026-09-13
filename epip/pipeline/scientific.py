"""Leakage-safe end-to-end EPIP scientific baseline pipeline.

OBS -> validation -> normalization -> completeness -> rate -> model ->
forecast -> prospective evaluation -> RESULT.

This module orchestrates existing components; it does not introduce
tectonic, geodetic, or stress-transfer inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from epip.catalog.completeness import CompletenessResult, estimate_mc
from epip.catalog.events import CatalogEvent, normalize_events
from epip.catalog.rates import SeismicRate, calculate_rate
from epip.forecast.poisson import PoissonForecastModel
from epip.ingest.usgs import fetch_events
from epip.prospective import ForecastRecord, ProspectiveOutcome, evaluate_forecast
from epip.validation.events import EventValidationReport, validate_events


@dataclass(frozen=True)
class ScientificPipelineConfig:
    """Configuration for a two-window, leakage-safe prospective run."""

    training_start: str
    cutoff: str
    evaluation_end: str
    region: str
    minimum_magnitude: float
    forecast_horizon_days: float
    fetch_limit: int = 20000
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.region.strip():
            raise ValueError("region must not be empty")
        if self.minimum_magnitude < -2.0 or self.minimum_magnitude > 10.0:
            raise ValueError("minimum_magnitude must be between -2 and 10")
        if self.forecast_horizon_days <= 0:
            raise ValueError("forecast_horizon_days must be > 0")
        if self.fetch_limit < 1:
            raise ValueError("fetch_limit must be >= 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")

        start = _parse_utc(self.training_start)
        cutoff = _parse_utc(self.cutoff)
        end = _parse_utc(self.evaluation_end)
        if not start < cutoff < end:
            raise ValueError("training_start < cutoff < evaluation_end is required")


@dataclass(frozen=True)
class ScientificPipelineResult:
    """Auditable output of one end-to-end baseline run."""

    generated_at: datetime
    config: ScientificPipelineConfig
    training_validation: EventValidationReport
    evaluation_validation: EventValidationReport
    training_events: tuple[CatalogEvent, ...]
    evaluation_events: tuple[CatalogEvent, ...]
    completeness: CompletenessResult
    rate: SeismicRate
    forecast: ForecastRecord
    outcome: ProspectiveOutcome


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(timezone.utc)


def _fetch_window(config: ScientificPipelineConfig, start: str, end: str) -> list[dict]:
    return fetch_events(
        starttime=start,
        endtime=end,
        minmagnitude=config.minimum_magnitude,
        limit=config.fetch_limit,
        timeout=config.timeout,
    )


def run_pipeline(
    config: ScientificPipelineConfig,
    *,
    region_match: Callable[[CatalogEvent], bool] | None = None,
) -> ScientificPipelineResult:
    """Execute the transparent baseline pipeline without future-data leakage."""

    training_raw = _fetch_window(config, config.training_start, config.cutoff)
    evaluation_raw = _fetch_window(config, config.cutoff, config.evaluation_end)

    training_validation = validate_events(training_raw)
    evaluation_validation = validate_events(evaluation_raw)

    if not training_validation.valid:
        raise ValueError(
            "training validation failed: " + "; ".join(training_validation.errors)
        )
    if not evaluation_validation.valid:
        raise ValueError(
            "evaluation validation failed: " + "; ".join(evaluation_validation.errors)
        )

    training_events = tuple(normalize_events(training_raw))
    evaluation_events = tuple(normalize_events(evaluation_raw))

    completeness = estimate_mc(training_events)
    rate = calculate_rate(training_events, mc=completeness.mc)

    model = PoissonForecastModel(rate_per_year=rate.rate_per_year)
    cutoff = _parse_utc(config.cutoff)
    forecast = model.forecast(
        generated_at=cutoff,
        region=config.region,
        horizon_days=config.forecast_horizon_days,
        minimum_magnitude=completeness.mc,
    )

    outcome = evaluate_forecast(
        forecast,
        evaluation_events,
        region_match=region_match,
    )

    return ScientificPipelineResult(
        generated_at=datetime.now(timezone.utc),
        config=config,
        training_validation=training_validation,
        evaluation_validation=evaluation_validation,
        training_events=training_events,
        evaluation_events=evaluation_events,
        completeness=completeness,
        rate=rate,
        forecast=forecast,
        outcome=outcome,
    )
