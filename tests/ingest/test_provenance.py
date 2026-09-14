from datetime import datetime, timezone

from epip.ingest.provenance import build_provenance


def test_provenance_hash_is_deterministic():
    events = [
        {
            "event_id": "us1",
            "time": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "latitude": 20.0,
            "longitude": -100.0,
        }
    ]
    kwargs = {
        "source": "USGS FDSN",
        "endpoint": "https://example.test/query",
        "starttime": "2026-01-01T00:00:00Z",
        "endtime": "2026-01-02T00:00:00Z",
        "parameters": {"limit": 100, "format": "geojson"},
        "events": events,
        "acquired_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
    }

    first = build_provenance(**kwargs)
    second = build_provenance(**kwargs)

    assert first.events_sha256 == second.events_sha256
    assert len(first.events_sha256) == 64
    assert first.event_count == 1
    assert first.parameters == (("format", "geojson"), ("limit", "100"))


def test_provenance_normalizes_acquisition_time_to_utc():
    record = build_provenance(
        source="USGS FDSN",
        endpoint="https://example.test/query",
        starttime="2026-01-01T00:00:00Z",
        endtime="2026-01-02T00:00:00Z",
        parameters={},
        events=[],
        acquired_at=datetime.fromisoformat("2026-01-02T01:00:00+01:00"),
    )

    assert record.acquired_at == datetime(2026, 1, 2, tzinfo=timezone.utc)
