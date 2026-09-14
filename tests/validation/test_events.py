from datetime import datetime, timezone

import pytest

from epip.catalog.events import CatalogEvent, normalize_events
from epip.validation.events import validate_event, validate_events


def valid_event(event_id="us7000test"):
    return {
        "event_id": event_id,
        "time": datetime(2026, 9, 13, tzinfo=timezone.utc),
        "latitude": 20.6,
        "longitude": -100.4,
        "depth_km": 10.0,
        "magnitude": 4.2,
        "magnitude_type": "ml",
        "source": "TEST",
    }


def test_valid_event_passes():
    report = validate_event(valid_event())
    assert report.valid
    assert report.checked == 1
    assert report.errors == ()


def test_invalid_coordinates_fail():
    event = valid_event()
    event["latitude"] = 91.0
    event["longitude"] = -181.0

    report = validate_event(event)

    assert not report.valid
    assert any("latitude" in error for error in report.errors)
    assert any("longitude" in error for error in report.errors)


def test_naive_timestamp_fails():
    event = valid_event()
    event["time"] = datetime(2026, 9, 13)

    report = validate_event(event)

    assert not report.valid
    assert any("timezone-aware" in error for error in report.errors)


def test_duplicate_event_ids_fail_collection_validation():
    report = validate_events([valid_event(), valid_event()])

    assert not report.valid
    assert any("duplicate id" in error for error in report.errors)


def test_normalization_converts_timestamp_to_utc():
    event = valid_event()
    event["time"] = datetime.fromisoformat("2026-09-13T06:00:00-05:00")

    normalized = normalize_events([event])

    assert normalized[0].time == datetime(2026, 9, 13, 11, tzinfo=timezone.utc)


def test_catalog_event_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        CatalogEvent(
            event_id="x",
            time=datetime(2026, 9, 13),
            latitude=0.0,
            longitude=0.0,
            depth_km=None,
            magnitude=None,
            magnitude_type=None,
            place=None,
            source="TEST",
        )
