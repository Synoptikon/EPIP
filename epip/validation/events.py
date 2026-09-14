"""Validation of canonical earthquake event records.

Validation is intentionally separated from normalization and modeling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from collections.abc import Iterable, Mapping
from typing import Any


REQUIRED_FIELDS = ("event_id", "time", "latitude", "longitude")


@dataclass(frozen=True)
class EventValidationReport:
    """Deterministic validation result for one or more event records."""

    valid: bool
    checked: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_event(event: Mapping[str, Any], *, index: int | None = None) -> EventValidationReport:
    """Validate one ingestion record without transforming it."""

    prefix = f"event[{index}]" if index is not None else "event"
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in event or event[field] is None:
            errors.append(f"{prefix}.{field}: required field is missing")

    event_id = event.get("event_id")
    if event_id is not None and not str(event_id).strip():
        errors.append(f"{prefix}.event_id: must not be empty")

    timestamp = event.get("time")
    if timestamp is not None:
        if not isinstance(timestamp, datetime):
            errors.append(f"{prefix}.time: must be a datetime")
        elif timestamp.tzinfo is None or timestamp.utcoffset() is None:
            errors.append(f"{prefix}.time: timezone-aware datetime required")
        elif timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
            warnings.append(f"{prefix}.time: datetime is not explicitly UTC")

    latitude = event.get("latitude")
    if latitude is not None:
        if not _finite_number(latitude):
            errors.append(f"{prefix}.latitude: must be a finite number")
        elif not -90.0 <= float(latitude) <= 90.0:
            errors.append(f"{prefix}.latitude: outside [-90, 90]")

    longitude = event.get("longitude")
    if longitude is not None:
        if not _finite_number(longitude):
            errors.append(f"{prefix}.longitude: must be a finite number")
        elif not -180.0 <= float(longitude) <= 180.0:
            errors.append(f"{prefix}.longitude: outside [-180, 180]")

    depth = event.get("depth_km")
    if depth is not None:
        if not _finite_number(depth):
            errors.append(f"{prefix}.depth_km: must be a finite number")
        elif float(depth) < 0.0:
            errors.append(f"{prefix}.depth_km: must be >= 0")

    magnitude = event.get("magnitude")
    if magnitude is not None and not _finite_number(magnitude):
        errors.append(f"{prefix}.magnitude: must be a finite number")

    return EventValidationReport(
        valid=not errors,
        checked=1,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_events(events: Iterable[Mapping[str, Any]]) -> EventValidationReport:
    """Validate a collection and aggregate all deterministic findings."""

    errors: list[str] = []
    warnings: list[str] = []
    checked = 0
    seen_ids: set[str] = set()

    for index, event in enumerate(events):
        checked += 1
        report = validate_event(event, index=index)
        errors.extend(report.errors)
        warnings.extend(report.warnings)

        event_id = event.get("event_id")
        if event_id is not None:
            normalized_id = str(event_id)
            if normalized_id in seen_ids:
                errors.append(f"event[{index}].event_id: duplicate id {normalized_id!r}")
            seen_ids.add(normalized_id)

    return EventValidationReport(
        valid=not errors,
        checked=checked,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
