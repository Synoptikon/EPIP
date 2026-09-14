from datetime import datetime, timezone

from epip.ingest.validation import validate_event, validate_events


def valid_event():
    return {
        "event_id": "us123",
        "time": datetime(2026, 9, 13, tzinfo=timezone.utc),
        "latitude": 20.5,
        "longitude": -100.4,
        "depth_km": 10.0,
        "magnitude": 4.2,
        "magnitude_type": "mw",
        "source": "USGS",
    }


def test_valid_event_passes():
    assert validate_event(valid_event()) == ()


def test_missing_event_id_is_rejected():
    event = valid_event()
    del event["event_id"]

    issues = validate_event(event)

    assert any(issue.code == "MISSING_FIELD" and issue.field == "event_id" for issue in issues)


def test_invalid_coordinates_are_rejected():
    event = valid_event()
    event["latitude"] = 91.0
    event["longitude"] = -181.0

    issues = validate_event(event)

    assert {issue.code for issue in issues} == {"OUT_OF_RANGE"}


def test_naive_time_is_rejected():
    event = valid_event()
    event["time"] = datetime(2026, 9, 13)

    issues = validate_event(event)

    assert any(issue.code == "NAIVE_TIME" for issue in issues)


def test_collection_report_is_auditable():
    report = validate_events([valid_event(), {**valid_event(), "latitude": 100.0}])

    assert report.checked == 2
    assert report.valid is False
    assert len(report.issues) == 1
    assert report.issues[0].event_index == 1
