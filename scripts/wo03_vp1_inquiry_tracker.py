"""Validate a local VP1 inquiry record and preview due dates; never send or write."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "docs/validation/rp1-vp1/response-tracker.json"
IDS = ("aircraft-spruce", "loc", "aerotech", "west-system", "laboratory")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_date(value: object, label: str) -> date:
    check(isinstance(value, str), f"{label} must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc
    check(parsed.isoformat() == value, f"{label} must be YYYY-MM-DD")
    return parsed


def add_business_days(sent: date, days: int, holidays: set[date]) -> date:
    """Count from the day after send; weekends and supplied holidays do not count."""
    current = sent
    remaining = days
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            remaining -= 1
    return current


def preview(record: dict) -> dict:
    """Validate a record and calculate dates without mutating the caller's data."""
    check(isinstance(record, dict) and record.get("schema_version") == 1, "Invalid schema")
    check(record.get("id") == "RP1-VP1-inquiry-response-tracker-v1", "Invalid tracker ID")
    calendar = record.get("holiday_calendar")
    check(isinstance(calendar, dict), "Missing holiday calendar choice")
    choice = calendar.get("choice")
    check(choice in ("unspecified", "none", "provided"), "Invalid holiday calendar choice")
    dates = calendar.get("dates")
    check(isinstance(dates, list), "Holiday dates must be a list")
    check(choice == "provided" or not dates, "Holiday dates require provided calendar")
    holidays = [parse_date(d, "Holiday date") for d in dates]
    check(len(holidays) == len(set(holidays)), "Duplicate holiday dates")
    check(
        choice != "provided" or bool(calendar.get("description")),
        "Provided calendar requires a description and coverage",
    )
    inquiries = record.get("inquiries")
    check(
        isinstance(inquiries, list) and all(isinstance(x, dict) for x in inquiries),
        "Inquiries must be a list of objects",
    )
    check([x.get("id") for x in inquiries] == list(IDS), "Expected five inquiry IDs in order")
    check(
        "cost_quote" in record
        and (record["cost_quote"] is None or isinstance(record["cost_quote"], dict)),
        "Cost quote must be null or an object",
    )
    if record["cost_quote"] is not None:
        check(
            isinstance(record["cost_quote"].get("reference"), str)
            and bool(record["cost_quote"]["reference"].strip()),
            "Quote record needs a reference; completeness remains a separate decision",
        )
    output = []
    for item in inquiries:
        sent = item.get("sent_date")
        timezone = item.get("sent_timezone")
        check("follow_up_date" in item, "Missing actual follow-up field")
        actual_follow_up = item["follow_up_date"]
        check("sent_date" in item and "sent_timezone" in item, "Missing send fields")
        check(isinstance(item.get("replies"), list), "Replies must be a list")
        check(item.get("status") in ("unsent", "sent"), "Invalid inquiry status")
        if sent is None:
            check(
                timezone is None and item["status"] == "unsent", "Unsent inquiry has send details"
            )
            check(not item["replies"], "Unsent inquiry cannot have replies")
            check(actual_follow_up is None, "Unsent inquiry cannot have a follow-up")
            follow_up = close = None
        else:
            check(item["status"] == "sent", "Dated inquiry must be marked sent")
            sent_date = parse_date(sent, "Send date")
            if actual_follow_up is not None:
                check(
                    parse_date(actual_follow_up, "Actual follow-up date") >= sent_date,
                    "Follow-up cannot precede send date",
                )
            check(isinstance(timezone, str) and bool(timezone), "Send timezone is required")
            try:
                ZoneInfo(timezone)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ValueError("Send timezone must be an IANA timezone") from exc
            for reply in item["replies"]:
                check(isinstance(reply, dict), "Reply must be an object")
                received = parse_date(reply.get("received_date"), "Reply date")
                check(received >= sent_date, "Reply cannot precede send date")
                check(
                    isinstance(reply.get("reference"), str) and bool(reply["reference"].strip()),
                    "Reply needs a local reference or summary",
                )
            follow_up = add_business_days(sent_date, 5, set(holidays)).isoformat()
            close = add_business_days(sent_date, 10, set(holidays)).isoformat()
        output.append(
            {
                "id": item["id"],
                "status": item["status"],
                "sent_date": sent,
                "sent_timezone": timezone,
                "follow_up_day_5": follow_up,
                "actual_follow_up_date": actual_follow_up,
                "close_day_10": close,
                "reply_count": len(item["replies"]),
            }
        )
    notes = {
        "unspecified": "Provisional Monday-Friday dates only; holiday calendar unspecified, so holiday ambiguity remains.",
        "none": "Explicit no-holidays choice: Monday-Friday dates count even on holidays.",
        "provided": "Monday-Friday dates exclude only the supplied holiday dates; verify the calendar covers the entire interval.",
    }
    return {
        "tracker_id": record["id"],
        "dry_run": True,
        "holiday_calendar_choice": choice,
        "holiday_note": notes[choice],
        "send_day_is_day_zero": True,
        "inquiries": output,
        "cost_quote_record_present": record["cost_quote"] is not None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_RECORD,
        help="local JSON record to validate; never modified",
    )
    args = parser.parse_args()
    print(json.dumps(preview(json.loads(args.input.read_text(encoding="utf-8"))), indent=2))


if __name__ == "__main__":
    main()
