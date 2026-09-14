from datetime import datetime, timedelta, timezone

import pytest

from epip.catalog.events import CatalogEvent
from epip.prospective import ForecastRecord, evaluate_forecast


def event(event_id, time, magnitude=4.0):
    return CatalogEvent(
        event_id=event_id,
        time=time,
        latitude=20.0,
        longitude=-100.0,
        depth_km=10.0,
        magnitude=magnitude,
        magnitude_type="ml",
        place=None,
        source="TEST",
    )


def test_future_event_is_counted_but_past_event_is_not():
    generated = datetime(2026, 9, 13, tzinfo=timezone.utc)
    forecast = ForecastRecord(
        generated_at=generated,
        region="TEST",
        horizon_hours=24,
        minimum_magnitude=4.0,
        probability=0.5,
        model_version="test-1",
    )

    events = [
        event("past", generated - timedelta(minutes=1)),
        event("future", generated + timedelta(hours=2)),
    ]

    outcome = evaluate_forecast(forecast, events)

    assert outcome.occurred
    assert outcome.observed_event_ids == ("future",)
    assert outcome.brier_score == pytest.approx(0.25)


def test_event_after_horizon_is_not_used():
    generated = datetime(2026, 9, 13, tzinfo=timezone.utc)
    forecast = ForecastRecord(
        generated_at=generated,
        region="TEST",
        horizon_hours=24,
        minimum_magnitude=4.0,
        probability=0.2,
        model_version="test-1",
    )

    outcome = evaluate_forecast(
        forecast,
        [event("late", generated + timedelta(hours=24, seconds=1))],
    )

    assert not outcome.occurred
    assert outcome.observed_event_ids == ()
    assert outcome.brier_score == pytest.approx(0.04)


def test_forecast_rejects_invalid_probability():
    with pytest.raises(ValueError, match="probability"):
        ForecastRecord(
            generated_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
            region="TEST",
            horizon_hours=24,
            minimum_magnitude=4.0,
            probability=1.1,
            model_version="test-1",
        )
