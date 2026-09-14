"""Validation of normalized seismic event observations.

This module validates structure, types, finite numeric values, units implied by
field names, and basic geographic/time-domain constraints. It does not perform
scientific interpretation or probabilistic inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation finding for one event field."""

    event_index: int
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Result of validating a collection of normalized events."""

    valid: bool
    checked: int
    issues: tuple[ValidationIssue, ...]


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_event(event: Mapping[str, Any], *, event_index: int = 0) -> tuple[ValidationIssue, ...]:
    """Validate one normalized seismic event without mutating it."""
    issues: list[ValidationIssue] = []

    required = ("event_id", "time", "latitude", "longitude", "depth_km", "magnitude")
    for field in required:
        if field not in event:
            issues.append(ValidationIssue(event_index, field, "MISSING_FIELD", "required field is missing"))

    event_id = event.get("event_id")
    if "event_id" in event and (not isinstance(event_id, str) or not event_id.strip()):
        issues.append(ValidationIssue(event_index, "event_id", "INVALID_ID", "event_id must be a non-empty string"))

    timestamp = event.get("time")
    if "time" in event:
        if not isinstance(timestamp, datetime):
            issues.append(ValidationIssue(event_index, "time", "INVALID_TIME", "time must be a datetime"))
        elif timestamp.tzinfo is None or timestamp.utcoffset() is None:
            issues.append(ValidationIssue(event_index, "time", "NAIVE_TIME", "time must be timezone-aware"))

    for field, low, high in (
        ("latitude", -90.0, 90.0),
        ("longitude", -180.0, 180.0),
    ):
        value = event.get(field)
        if field in event and not _is_finite_number(value):
            issues.append(ValidationIssue(event_index, field, "INVALID_NUMBER", "value must be a finite number"))
        elif field in event and not low <= float(value) <= high:
            issues.append(ValidationIssue(event_index, field, "OUT_OF_RANGE", f"value must be between {low} and {high}"))

    for field in ("depth_km", "magnitude"):
        value = event.get(field)
        if value is not None and not _is_finite_number(value):
            issues.append(ValidationIssue(event_index, field, "INVALID_NUMBER", "value must be a finite number or None"))

    source = event.get("source")
    if source is not None and (not isinstance(source, str) or not source.strip()):
        issues.append(ValidationIssue(event_index, "source", "INVALID_SOURCE", "source must be a non-empty string when provided"))

    return tuple(issues)


def validate_events(events: Iterable[Mapping[str, Any]]) -> ValidationReport:
    """Validate normalized events and return an auditable report."""
    issues: list[ValidationIssue] = []
    checked = 0

    for checked, event in enumerate(events, start=1):
        issues.extend(validate_event(event, event_index=checked - 1))

    return ValidationReport(
        valid=not issues,
        checked=checked,
        issues=tuple(issues),
    )
