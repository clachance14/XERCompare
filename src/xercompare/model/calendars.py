"""Decode stored P6 calendar trees. No scheduling or date recalculation."""

from dataclasses import dataclass, field
from datetime import date, timedelta
import re


@dataclass
class CalendarDefinition:
    week: dict = field(default_factory=dict)
    exceptions: dict = field(default_factory=dict)
    available: bool = True
    note: str = ""


def _tree(blob):
    tokens = re.findall(r"\(|\)|[^()]+", blob.replace("\x7f", ""))
    tokens = [t.strip() for t in tokens if t.strip()]
    index = 0

    def group(depth=0):
        nonlocal index
        if depth > 32 or index >= len(tokens) or tokens[index] != "(":
            raise ValueError("invalid calendar tree")
        index += 1
        result = []
        while index < len(tokens) and tokens[index] != ")":
            if tokens[index] == "(":
                result.append(group(depth + 1))
            else:
                result.append(tokens[index])
                index += 1
        if index >= len(tokens):
            raise ValueError("unclosed calendar tree")
        index += 1
        return result

    result = group()
    if index != len(tokens):
        raise ValueError("trailing calendar data")
    return result


def _node(value):
    if (
        len(value) != 3
        or not isinstance(value[0], str)
        or not all(isinstance(x, list) for x in value[1:])
    ):
        raise ValueError("invalid calendar node")
    name = value[0].split("||")[-1]
    parts = value[1][0].split("|") if value[1] else []
    if len(parts) % 2:
        raise ValueError("invalid calendar properties")
    return name, dict(zip(parts[::2], parts[1::2])), value[2]


def _shifts(nodes):
    values = []
    for node in nodes:
        _, props, _ = _node(node)
        start, finish = props["s"], props["f"]

        def clock(text):
            h, m = map(int, text.split(":"))
            if not (0 <= h <= 24 and 0 <= m < 60 and (h != 24 or m == 0)):
                raise ValueError("invalid shift time")
            return f"{h:02d}:{m:02d}"

        start, finish = clock(start), clock(finish)
        values.append((start, "24:00" if finish == "00:00" else finish))
    return tuple(sorted(values))


def resolve_calendar(schedule, calendar_id, seen=()):
    if calendar_id in seen:
        return CalendarDefinition(available=False, note="Calendar inheritance cycle")
    cal = schedule.calendars.get(calendar_id)
    if cal is None:
        return CalendarDefinition(
            available=False, note="Referenced calendar was not exported"
        )
    parent = cal.raw.get("base_clndr_id", "")
    result = (
        resolve_calendar(schedule, parent, (*seen, calendar_id))
        if parent
        else CalendarDefinition()
    )
    # Copy inherited definitions; local days and dates override individually.
    result = CalendarDefinition(
        dict(result.week), dict(result.exceptions), result.available, result.note
    )
    blob = cal.raw.get("clndr_data", "")
    if not blob:
        if not parent:
            return CalendarDefinition(
                available=False, note="Calendar definition was not exported"
            )
        return result
    try:
        name, _, children = _node(_tree(blob))
        if name != "CalendarData":
            raise ValueError("missing CalendarData")
        for child in children:
            name, _, items = _node(child)
            if name == "VIEW":
                continue
            if name not in {"DaysOfWeek", "Exceptions"}:
                raise ValueError("unsupported calendar section " + name)
            for item in items:
                key, props, shifts = _node(item)
                if name == "DaysOfWeek":
                    day = int(key)
                    if day not in range(1, 8):
                        raise ValueError("invalid weekday")
                    result.week[day] = _shifts(shifts)
                else:
                    serial = float(props["d"])
                    if serial != int(serial):
                        raise ValueError("non-integral exception date")
                    day = (date(1899, 12, 30) + timedelta(days=int(serial))).isoformat()
                    result.exceptions[day] = _shifts(shifts)
    except (ValueError, KeyError, IndexError, TypeError, OverflowError) as error:
        return CalendarDefinition(
            available=False, note=f"Cannot parse calendar definition: {error}"
        )
    return result


def definition_values(schedule, cid, definition=None):
    cal = schedule.calendars.get(cid)
    definition = definition or resolve_calendar(schedule, cid)
    result = {
        "Calendar": cal.name if cal else cid,
        "Hours per day": cal.day_hr_cnt if cal else None,
        "Definition status": "Available" if definition.available else definition.note,
    }
    if cal:
        for field, label in [
            ("week_hr_cnt", "Hours per week"),
            ("month_hr_cnt", "Hours per month"),
            ("year_hr_cnt", "Hours per year"),
        ]:
            value = cal.raw.get(field, "")
            result[label] = float(value) if value else None
    if definition.available:
        days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]

        def shifts(values):
            return "; ".join(f"{s}-{f}" for s, f in values) or "Nonworking"

        result.update(
            {f"Workweek {days[d-1]}": shifts(v) for d, v in definition.week.items()}
        )
        result.update(
            {f"Exception {d}": shifts(v) for d, v in definition.exceptions.items()}
        )
    return result
