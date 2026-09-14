"""Provenance records for externally acquired EPIP catalogs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class AcquisitionProvenance:
    """Immutable provenance for one acquisition window."""

    source: str
    endpoint: str
    starttime: str
    endtime: str
    parameters: tuple[tuple[str, str], ...]
    acquired_at: datetime
    event_count: int
    events_sha256: str


def build_provenance(
    *,
    source: str,
    endpoint: str,
    starttime: str,
    endtime: str,
    parameters: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    acquired_at: datetime | None = None,
) -> AcquisitionProvenance:
    """Build a deterministic provenance record for normalized acquisition output."""

    if not source.strip():
        raise ValueError("source must not be empty")
    if not endpoint.strip():
        raise ValueError("endpoint must not be empty")
    if acquired_at is None:
        acquired_at = datetime.now(timezone.utc)
    if acquired_at.tzinfo is None or acquired_at.utcoffset() is None:
        raise ValueError("acquired_at must be timezone-aware")

    canonical_events = json.dumps(
        list(events),
        sort_keys=True,
        separators=(",", ":"),
        default=lambda value: value.isoformat() if isinstance(value, datetime) else str(value),
    ).encode("utf-8")

    canonical_parameters = tuple(
        sorted((str(key), str(value)) for key, value in parameters.items())
    )

    return AcquisitionProvenance(
        source=source,
        endpoint=endpoint,
        starttime=starttime,
        endtime=endtime,
        parameters=canonical_parameters,
        acquired_at=acquired_at.astimezone(timezone.utc),
        event_count=len(events),
        events_sha256=hashlib.sha256(canonical_events).hexdigest(),
    )
