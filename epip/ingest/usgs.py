"""USGS FDSN earthquake acquisition and normalization for EPIP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

USGS_FDSN_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def fetch_events(
    *,
    starttime: str,
    endtime: str,
    minmagnitude: float | None = None,
    minlatitude: float | None = None,
    maxlatitude: float | None = None,
    minlongitude: float | None = None,
    maxlongitude: float | None = None,
    limit: int = 20000,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Acquire and normalize USGS FDSN GeoJSON event records.

    Spatial bounds are optional for backward compatibility. When supplied,
    they are passed directly to the FDSN service and retained in the pipeline
    provenance by the caller.
    """

    if limit < 1:
        raise ValueError("limit must be >= 1")

    bounds = (minlatitude, maxlatitude, minlongitude, maxlongitude)
    if any(value is not None for value in bounds) and not all(value is not None for value in bounds):
        raise ValueError("all four spatial bounds must be supplied together")
    if minlatitude is not None and not -90 <= minlatitude <= maxlatitude <= 90:
        raise ValueError("invalid latitude bounds")
    if minlongitude is not None and not -180 <= minlongitude <= maxlongitude <= 180:
        raise ValueError("invalid longitude bounds")

    params: dict[str, Any] = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "limit": limit,
        "orderby": "time-asc",
    }

    if minmagnitude is not None:
        params["minmagnitude"] = minmagnitude
    if minlatitude is not None:
        params.update(
            minlatitude=minlatitude,
            maxlatitude=maxlatitude,
            minlongitude=minlongitude,
            maxlongitude=maxlongitude,
        )

    response = requests.get(USGS_FDSN_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    events: list[dict[str, Any]] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        event_id = feature.get("id")
        if len(coordinates) < 2 or not event_id:
            continue

        events.append(
            {
                "event_id": event_id,
                "time": _parse_time(properties.get("time")),
                "latitude": coordinates[1],
                "longitude": coordinates[0],
                "depth_km": coordinates[2] if len(coordinates) > 2 else None,
                "magnitude": properties.get("mag"),
                "magnitude_type": properties.get("magType"),
                "place": properties.get("place"),
                "source": "USGS",
                "url": properties.get("url"),
            }
        )

    return events
