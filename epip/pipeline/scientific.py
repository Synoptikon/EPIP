"""Leakage-safe end-to-end EPIP scientific baseline pipeline.

OBS -> acquisition -> validation -> normalization -> completeness -> rate
-> MODEL -> forecast -> prospective evaluation -> RESULT.

No tectonic, geodetic, or stress-transfer inference is introduced here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from epip.catalog.completeness import CompletenessResult, estimate_mc
from epip.catalog.events import CatalogEvent, normalize_events
from epip.catalog.rates import SeismicRate, calculate_rate
from epip.forecast.poisson import PoissonForecastModel
from epip.ingest.provenance import AcquisitionProvenance, build_provenance
from epip.ingest.usgs import USGS_FDSN_URL, fetch_events
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
    minlatitude: float | None = None
    maxlatitude: float | None = None
    minlongitude: float | None = None
    maxlongitude: float | None = None
    acquisition_min_magnitude: float | None = None
    fetch_limit: int = 20000
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.region.strip():
            raise ValueError("region must not be empty")
        if not -2.0 <= self.minimum_magnitude <= 10.0:
            raise ValueError("minimum_magnitude must be between -2 and 10")
        if self.acquisition_min_magnitude is not None and not -2.0 <= self.acquisition_min_magnitude <= 10.0:
            raise ValueError("acquisition_min_magnitude must be between -2 and 10")
        if self.forecast_horizon_days <= 0:
            raise ValueError("forecast_horizon_days must be > 0")
        if self.fetch_limit < 1:
            raise ValueError("fetch_limit must be >= 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")

        bounds = (self.minlatitude, self.maxlatitude, self.minlongitude, self.maxlongitude)
        if any(value is not None for value in bounds) and not all(value is not None for value in bounds):
            raise ValueError("all four spatial bounds must be supplied together")
        if self.minlatitude is not None and not -90 <= self.minlatitude <= self.maxlatitude <= 90:
            raise ValueError("invalid latitude bounds")
        if self.minlongitude is not None and not -180 <= self.minlongitude <= self.maxlongitude <= 180:
            raise ValueError("invalid longitude bounds")

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
    training_provenance: AcquisitionProvenance
    evaluation_provenance: AcquisitionProvenance
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


def _fetch_window(
    config: ScientificPipelineConfig,
    start: str,
    end: str,
) -> tuple[list[dict], AcquisitionProvenance]:
    acquired_at = datetime.now(timezone.utc)
    events = fetch_events(
        starttime=start,
        endtime=end,
        minmagnitude=config.acquisition_min_magnitude,
        minlatitude=config.minlatitude,
        maxlatitude=config.maxlatitude,
        minlongitude=config.minlongitude,
        maxlongitude=config.maxlongitude,
        limit=config.fetch_limit,
        timeout=config.timeout,
    )

    parameters = {
        "format": "geojson",
        "starttime": start,
        "endtime": end,
        "limit": config.fetch_limit,
        "orderby": "time-asc",
    }
    if config.acquisition_min_magnitude is not None:
        parameters["minmagnitude"] = config.acquisition_min_magnitude
    if config.minlatitude is not None:
        parameters.update(
            minlatitude=config.minlatitude,
            maxlatitude=config.maxlatitude,
            minlongitude=config.minlongitude,
            maxlongitude=config.maxlongitude,
        )

    provenance = build_provenance(
        source="USGS FDSN",
        endpoint=USGS_FDSN_URL,
        starttime=start,
        endtime=end,
        parameters=parameters,
        events=events,
        acquired_at=acquired_at,
    )
    return events, provenance


def run_pipeline(
    config: ScientificPipelineConfig,
    *,
    region_match: Callable[[CatalogEvent], bool] | None = None,
) -> ScientificPipelineResult:
    """Execute the transparent baseline without future-data leakage."""

    training_raw, training_provenance = _fetch_window(
        config, config.training_start, config.cutoff
    )
    evaluation_raw, evaluation_provenance = _fetch_window(
        config, config.cutoff, config.evaluation_end
    )

    training_validation = validate_events(training_raw)
    evaluation_validation = validate_events(evaluation_raw)
    if not training_validation.valid:
        raise ValueError("training validation failed: " + "; ".join(training_validation.errors))
    if not evaluation_validation.valid:
        raise ValueError("evaluation validation failed: " + "; ".join(evaluation_validation.errors))

    training_events = tuple(normalize_events(training_raw))
    evaluation_events = tuple(normalize_events(evaluation_raw))

    completeness = estimate_mc(training_events)
    rate = calculate_rate(training_events, mc=completeness.mc)

    forecast_threshold = max(config.minimum_magnitude, completeness.mc)
    model = PoissonForecastModel(rate_per_year=rate.rate_per_year)
    cutoff = _parse_utc(config.cutoff)
    forecast = model.forecast(
        generated_at=cutoff,
        region=config.region,
        horizon_days=config.forecast_horizon_days,
        minimum_magnitude=forecast_threshold,
    )

    outcome = evaluate_forecast(
        forecast,
        evaluation_events,
        region_match=region_match,
    )

    return ScientificPipelineResult(
        generated_at=datetime.now(timezone.utc),
        config=config,
        training_provenance=training_provenance,
        evaluation_provenance=evaluation_provenance,
        training_validation=training_validation,
        evaluation_validation=evaluation_validation,
        training_events=training_events,
        evaluation_events=evaluation_events,
        completeness=completeness,
        rate=rate,
        forecast=forecast,
        outcome=outcome,
    )
