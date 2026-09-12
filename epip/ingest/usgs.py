"""USGS FDSN event ingestion for EPIP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

USGS_FDSN_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def fetch_events(
    *,
    starttime: str,
    endtime: str,
    minmagnitude: float | None = None,
    limit: int = 20000,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Fetch and normalize earthquake events from USGS FDSN."""

    if limit < 1:
        raise ValueError("limit must be >= 1")

    params: dict[str, Any] = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "limit": limit,
        "orderby": "time-asc",
    }

    if minmagnitude is not None:
        params["minmagnitude"] = minmagnitude

    response = requests.get(
        USGS_FDSN_URL,
        params=params,
        timeout=timeout,
    )

    response.raise_for_status()

    payload = response.json()

    events: list[dict[str, Any]] = []

    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        if len(coordinates) < 2:
            continue

        event_id = feature.get("id")

        if not event_id:
            continue

        events.append(
            {
                "event_id": event_id,
                "time": _parse_time(properties.get("time")),
                "latitude": coordinates[1],
                "longitude": coordinates[0],
                "depth_km": (
                    coordinates[2]
                    if len(coordinates) > 2
                    else None
                ),
                "magnitude": properties.get("mag"),
                "magnitude_type": properties.get("magType"),
                "place": properties.get("place"),
                "source": "USGS",
                "url": properties.get("url"),
            }
        )

    return events
