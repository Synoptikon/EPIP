from datetime import datetime, timezone

import pytest

from epip.catalog.events import CatalogEvent
from epip.catalog.rates import calculate_rate


def event(event_id: str, timestamp: str, magnitude: float) -> CatalogEvent:
    return CatalogEvent(
        event_id=event_id,
        time=datetime.fromisoformat(timestamp).astimezone(timezone.utc),
        latitude=20.0,
        longitude=-100.0,
        depth_km=10.0,
        magnitude=magnitude,
        magnitude_type="ml",
        source="TEST",
    )


def test_rate_uses_declared_observation_window():
    events = (
        event("e1", "2026-01-01T00:00:00+00:00", 4.0),
        event("e2", "2026-01-02T00:00:00+00:00", 4.1),
    )

    rate = calculate_rate(
        events,
        mc=4.0,
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )

    assert rate.event_count == 2
    assert rate.duration_years == pytest.approx(1.0, rel=1e-6)
    assert rate.rate_per_year == pytest.approx(2.0, rel=1e-6)


def test_rate_requires_complete_declared_window():
    events = (event("e1", "2026-01-01T00:00:00+00:00", 4.0),)

    with pytest.raises(ValueError, match="must be supplied together"):
        calculate_rate(
            events,
            mc=4.0,
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
