"""Local inquiry date previews do not mutate records or infer outreach."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tracker", ROOT / "scripts/wo03_vp1_inquiry_tracker.py"
)
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)


@pytest.fixture
def record():
    return json.loads(tracker.DEFAULT_RECORD.read_text())


def sent(item, date="2026-11-06", timezone="America/Los_Angeles"):
    item.update(status="sent", sent_date=date, sent_timezone=timezone)


def test_empty_record_no_dates_or_quote(record):
    original = copy.deepcopy(record)
    result = tracker.preview(record)
    assert result["holiday_calendar_choice"] == "unspecified"
    assert "ambiguity" in result["holiday_note"]
    assert not result["cost_quote_record_present"]
    assert all(
        x["follow_up_day_5"] is None and x["close_day_10"] is None and x["reply_count"] == 0
        for x in result["inquiries"]
    )
    assert record == original


def test_per_inquiry_dates_and_holiday_choices(record):
    sent(record["inquiries"][0])
    sent(record["inquiries"][1], "2026-11-09", "America/New_York")
    record["holiday_calendar"] = {
        "choice": "provided",
        "description": "US example Nov 2026",
        "dates": ["2026-11-11"],
    }
    before = copy.deepcopy(record)
    result = tracker.preview(record)
    assert result["inquiries"][0]["follow_up_day_5"] == "2026-11-16"
    assert result["inquiries"][0]["close_day_10"] == "2026-11-23"
    assert result["inquiries"][1]["follow_up_day_5"] == "2026-11-17"
    assert record == before
    record["holiday_calendar"] = {"choice": "none", "description": "", "dates": []}
    assert tracker.preview(record)["inquiries"][0]["follow_up_day_5"] == "2026-11-13"


def test_replies_are_preserved_and_do_not_change_status(record):
    sent(record["inquiries"][0])
    record["inquiries"][0]["replies"] = [
        {"received_date": "2026-11-09", "reference": "local reply"}
    ]
    before = copy.deepcopy(record)
    assert tracker.preview(record)["inquiries"][0]["reply_count"] == 1
    assert record == before


@pytest.mark.parametrize(
    "change", ["missing_zone", "bad_zone", "bad_date", "unsent_reply", "bad_ids"]
)
def test_invalid_inputs_fail(record, change):
    item = record["inquiries"][0]
    if change == "missing_zone":
        sent(item, timezone=None)
    elif change == "bad_zone":
        sent(item, timezone="not/a-zone")
    elif change == "bad_date":
        sent(item, date="2026-11-31")
    elif change == "unsent_reply":
        item["replies"].append({"received_date": "2026-11-09", "reference": "reply"})
    else:
        item["id"] = "other"
    with pytest.raises(ValueError):
        tracker.preview(record)


def test_holiday_choice_and_calendar_validation(record):
    record["holiday_calendar"] = {"choice": "unspecified", "dates": ["2026-11-11"]}
    with pytest.raises(ValueError):
        tracker.preview(record)
    record["holiday_calendar"] = {"choice": "provided", "description": "", "dates": []}
    with pytest.raises(ValueError):
        tracker.preview(record)


def test_actual_follow_up_is_distinct_and_single(record):
    sent(record["inquiries"][0])
    record["inquiries"][0]["follow_up_date"] = "2026-11-16"
    result = tracker.preview(record)["inquiries"][0]
    assert result["follow_up_day_5"] == "2026-11-13"
    assert result["actual_follow_up_date"] == "2026-11-16"
    record["inquiries"][0]["follow_up_date"] = ["2026-11-13", "2026-11-16"]
    with pytest.raises(ValueError):
        tracker.preview(record)


@pytest.mark.parametrize("value", ["2026-11-05", "2026-11-31"])
def test_invalid_follow_up_date(record, value):
    sent(record["inquiries"][0])
    record["inquiries"][0]["follow_up_date"] = value
    with pytest.raises(ValueError):
        tracker.preview(record)


def test_follow_up_without_send_rejected(record):
    record["inquiries"][0]["follow_up_date"] = "2026-11-09"
    with pytest.raises(ValueError):
        tracker.preview(record)
