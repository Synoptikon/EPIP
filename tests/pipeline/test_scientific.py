from datetime import datetime, timezone

import pytest

import epip.pipeline.scientific as scientific


def event(event_id, timestamp, magnitude):
    return {
        "event_id": event_id,
        "time": datetime.fromisoformat(timestamp).astimezone(timezone.utc),
        "latitude": 20.0,
        "longitude": -100.0,
        "depth_km": 10.0,
        "magnitude": magnitude,
        "magnitude_type": "ml",
        "source": "TEST",
    }


def test_pipeline_separates_training_and_future_evaluation(monkeypatch):
    training = [
        event("t1", "2026-01-01T00:00:00+00:00", 4.0),
        event("t2", "2026-01-02T00:00:00+00:00", 4.1),
        event("t3", "2026-01-03T00:00:00+00:00", 4.2),
        event("t4", "2026-01-04T00:00:00+00:00", 4.3),
        event("t5", "2026-01-05T00:00:00+00:00", 4.4),
        event("t6", "2026-01-06T00:00:00+00:00", 4.5),
        event("t7", "2026-01-07T00:00:00+00:00", 4.6),
        event("t8", "2026-01-08T00:00:00+00:00", 4.7),
        event("t9", "2026-01-09T00:00:00+00:00", 4.8),
        event("t10", "2026-01-10T00:00:00+00:00", 4.9),
    ]
    future = [event("f1", "2026-01-12T00:00:00+00:00", 5.0)]

    calls = []

    def fake_fetch(*, starttime, endtime, **kwargs):
        calls.append((starttime, endtime))
        return training if len(calls) == 1 else future

    monkeypatch.setattr(scientific, "fetch_events", fake_fetch)

    config = scientific.ScientificPipelineConfig(
        training_start="2026-01-01T00:00:00Z",
        cutoff="2026-01-11T00:00:00Z",
        evaluation_end="2026-01-20T00:00:00Z",
        region="TEST",
        minimum_magnitude=4.0,
        forecast_horizon_days=7.0,
    )

    result = scientific.run_pipeline(config)

    assert len(calls) == 2
    assert result.training_events[-1].event_id == "t10"
    assert result.evaluation_events == (result.evaluation_events[0],)
    assert result.forecast.generated_at == datetime(2026, 1, 11, tzinfo=timezone.utc)
    assert result.outcome.observed_event_ids == ("f1",)
    assert 0.0 <= result.forecast.probability <= 1.0
    assert result.training_provenance.source == "USGS FDSN"
    assert result.training_provenance.starttime == "2026-01-01T00:00:00Z"
    assert result.evaluation_provenance.endtime == "2026-01-20T00:00:00Z"
    assert result.training_provenance.event_count == len(training)
    assert len(result.training_provenance.events_sha256) == 64


def test_pipeline_requires_strictly_ordered_windows():
    with pytest.raises(ValueError, match="training_start < cutoff < evaluation_end"):
        scientific.ScientificPipelineConfig(
            training_start="2026-01-02T00:00:00Z",
            cutoff="2026-01-01T00:00:00Z",
            evaluation_end="2026-01-03T00:00:00Z",
            region="TEST",
            minimum_magnitude=4.0,
            forecast_horizon_days=7.0,
        )
