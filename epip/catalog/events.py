"""Normalized earthquake event catalog primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class CatalogEvent:
    """Canonical earthquake event used by the EPIP catalog layer."""

    event_id: str
    time: datetime
    latitude: float
    longitude: float
    depth_km: float | None
    magnitude: float | None
    magnitude_type: str | None
    place: str | None
    source: str
    url: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")

        if self.time.tzinfo is None or self.time.utcoffset() is None:
            raise ValueError("time must be timezone-aware")

        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

        if self.depth_km is not None and self.depth_km < 0:
            raise ValueError("depth_km must be >= 0")


def normalize_events(events: Iterable[dict]) -> list[CatalogEvent]:
    """Convert validated ingestion records into canonical catalog events."""

    result: list[CatalogEvent] = []
    seen: set[str] = set()

    for event in events:
        event_id = str(event["event_id"])

        if event_id in seen:
            continue

        time = event["time"]

        if not isinstance(time, datetime):
            raise TypeError("event time must be a datetime")

        if time.tzinfo is None or time.utcoffset() is None:
            raise ValueError("event time must be timezone-aware")

        result.append(
            CatalogEvent(
                event_id=event_id,
                time=time.astimezone(timezone.utc),
                latitude=float(event["latitude"]),
                longitude=float(event["longitude"]),
                depth_km=(
                    None
                    if event.get("depth_km") is None
                    else float(event["depth_km"])
                ),
                magnitude=(
                    None
                    if event.get("magnitude") is None
                    else float(event["magnitude"])
                ),
                magnitude_type=event.get("magnitude_type"),
                place=event.get("place"),
                source=str(event.get("source", "unknown")),
                url=event.get("url"),
            )
        )

        seen.add(event_id)

    return sorted(result, key=lambda item: item.time)
