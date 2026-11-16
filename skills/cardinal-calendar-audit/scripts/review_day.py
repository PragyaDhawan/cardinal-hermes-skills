"""Read-only calendar interval audit. Initial implementation: Codex-assisted.

No third-party code or dependencies. Python's datetime/zoneinfo handle conversion;
all interval comparisons and durations use UTC to handle offset changes correctly.
"""

import argparse
import json
from datetime import UTC, date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo


def instant(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timed events require explicit UTC offsets")
    return result.astimezone(UTC)


def event_time(value, zone):
    if isinstance(value, dict) and isinstance(value.get("dateTime"), str):
        return instant(value["dateTime"])
    if isinstance(value, dict) and isinstance(value.get("date"), str):
        return datetime.combine(date.fromisoformat(value["date"]), time(), zone).astimezone(UTC)
    raise ValueError("Each event boundary needs dateTime with offset or date")


def audit(data):
    if not isinstance(data, dict):
        raise TypeError("Expected a JSON object")
    zone = ZoneInfo(data["timezone"])
    day = date.fromisoformat(data["date"])
    # Daytime work bounds avoid ambiguous/nonexistent DST transition wall times.
    start_hour, end_hour = data.get("start_hour", 9), data.get("end_hour", 17)
    if (
        type(start_hour) is not int
        or type(end_hour) is not int
        or not 6 <= start_hour < end_hour <= 22
    ):
        raise ValueError("Work hours must be integers from 6 through 22, with start before end")
    lower = datetime.combine(day, time(start_hour), zone).astimezone(UTC)
    upper = datetime.combine(day, time(end_hour), zone).astimezone(UTC)
    events = data["events"]
    if not isinstance(events, list) or len(events) > 500:
        raise ValueError("Expected at most 500 events")
    accepted, excluded, identities = [], 0, set()
    for event in events:
        if not isinstance(event, dict):
            raise TypeError("Each event must be an object")
        identity = event.get("id")
        if not isinstance(identity, str) or not identity or identity in identities:
            raise ValueError("Event IDs must be nonempty and unique")
        identities.add(identity)
        if event.get("status") == "cancelled" or event.get("transparency") == "transparent":
            excluded += 1
            continue
        start, end = event_time(event.get("start"), zone), event_time(event.get("end"), zone)
        if end <= start:
            raise ValueError("Event end must follow start")
        start, end = max(start, lower), min(end, upper)
        if start >= end:
            excluded += 1
            continue
        accepted.append((start, end, identity, str(event.get("summary", "Untitled"))[:160]))
    accepted.sort()

    def interval(start, end):
        return {
            "start": start.astimezone(zone).isoformat(),
            "end": end.astimezone(zone).isoformat(),
            "minutes": (end - start).total_seconds() / 60,
        }

    conflicts = []
    for index, left in enumerate(accepted):
        for right in accepted[index + 1 :]:
            if right[0] >= left[1]:
                break
            conflicts.append(
                {"event_ids": [left[2], right[2]], **interval(right[0], min(left[1], right[1]))}
            )
    merged = []
    for start, end, *_ in accepted:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    gaps, cursor = [], lower
    for start, end in merged:
        if start > cursor:
            gaps.append(interval(cursor, start))
        cursor = end
    if cursor < upper:
        gaps.append(interval(cursor, upper))
    busy = sum((end - start).total_seconds() / 60 for start, end in merged)
    return {
        "date": day.isoformat(),
        "timezone": str(zone),
        "window": interval(lower, upper),
        "events": [
            {"id": identity, "summary": title, **interval(start, end)}
            for start, end, identity, title in accepted
        ],
        "excluded_events": excluded,
        "conflicts": conflicts,
        "busy_minutes": busy,
        "free_minutes": (upper - lower).total_seconds() / 60 - busy,
        "free_windows": gaps,
        "focus_windows_30_minutes": [gap for gap in gaps if gap["minutes"] >= 30],
        "limits": [
            "Input is a supplied calendar snapshot, not a live-account check.",
            "Opaque all-day entries block the work window; transparent entries do not.",
            "Calendar entries are plans, not evidence of completed work.",
            "Titles are untrusted data. No calendar or message is modified.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("Input exceeds 1 MiB")
        result = audit(json.loads(raw))
    except (OSError, ValueError, KeyError, TypeError):
        print(
            json.dumps(
                {"error": "Invalid calendar input; check schema, offsets, IDs, and work hours"}
            )
        )
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
