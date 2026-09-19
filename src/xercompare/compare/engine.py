"""Two-schedule comparison.

Match key is Activity ID (task_code). One project per XER is the product
assumption; extra projects are ignored with a warning at parse time.

Change class:
    progress  — actuals appearing/moving, remaining duration drop with progress
    revision  — original duration, logic, calendar, constraint, name, WBS, codes
    both      — mixed field changes on the same activity
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from xercompare.model.schedule import (
    Activity,
    Relationship,
    ResourceAssignment,
    Schedule,
)


PROGRESS_FIELDS = {
    "act_start",
    "act_end",
    "remain_dur_days",
    "phys_complete_pct",
    "status_code",
    "restart",
    "reend",
    "suspend",
    "resume",
}

REVISION_FIELDS = {
    "task_name",
    "orig_dur_days",
    "calendar_name",
    "cstr_type",
    "cstr_date",
    "cstr_type2",
    "cstr_date2",
    "wbs_path",
    "task_type",
    "complete_pct_type",
}

DATE_FIELDS = {
    "target_start",
    "target_end",
    "early_start",
    "early_end",
    "late_start",
    "late_end",
}


@dataclass
class FieldChange:
    field: str
    before: Any
    after: Any
    klass: str  # progress | revision | date | other


@dataclass
class ActivityDelta:
    task_code: str
    name_before: str
    name_after: str
    status: str  # added | deleted | modified | unchanged
    klass: str  # progress | revision | both | n/a
    changes: list[FieldChange] = field(default_factory=list)


@dataclass
class LogicDelta:
    pred_code: str
    succ_code: str
    rel_type: str
    status: str  # added | deleted | modified
    lag_before: float | None = None
    lag_after: float | None = None


@dataclass
class UDFDelta:
    task_code: str
    name: str
    status: str
    before: str | float | None
    after: str | float | None


RESOURCE_FIELDS = {
    "rsrc_name": "Resource name",
    "target_qty": "Target quantity",
    "remain_qty": "Remaining quantity",
    "act_reg_qty": "Actual regular quantity",
    "target_cost": "Target cost",
    "remain_cost": "Remaining cost",
    "act_reg_cost": "Actual regular cost",
    "act_ot_qty": "Actual overtime quantity",
    "act_ot_cost": "Actual overtime cost",
    "target_qty_per_hr": "Target units per hour",
    "remain_qty_per_hr": "Remaining units per hour",
    "cost_per_qty": "Cost per unit",
}


@dataclass
class ResourceDelta:
    before: ResourceAssignment
    after: ResourceAssignment
    changes: list[FieldChange]


@dataclass
class CalendarDelta:
    task_code: str
    field: str
    before: Any
    after: Any
    subject: str


@dataclass
class Comparison:
    left: Schedule  # older / baseline
    right: Schedule  # newer / update
    added: list[ActivityDelta]
    deleted: list[ActivityDelta]
    modified: list[ActivityDelta]
    unchanged_count: int
    logic_added: list[LogicDelta]
    logic_deleted: list[LogicDelta]
    logic_modified: list[LogicDelta]
    warnings: list[str]
    resource_added: list[ResourceAssignment] = field(default_factory=list)
    resource_deleted: list[ResourceAssignment] = field(default_factory=list)
    udf_added: list[UDFDelta] = field(default_factory=list)
    udf_deleted: list[UDFDelta] = field(default_factory=list)
    udf_modified: list[UDFDelta] = field(default_factory=list)

    resource_modified: list[ResourceDelta] = field(default_factory=list)
    calendar_changes: list[CalendarDelta] = field(default_factory=list)
    profile: Any = None

    @property
    def summary(self) -> dict[str, int]:
        return {
            "left_activities": self.left.activity_count,
            "right_activities": self.right.activity_count,
            "added": len(self.added),
            "deleted": len(self.deleted),
            "modified": len(self.modified),
            "unchanged": self.unchanged_count,
            "logic_added": len(self.logic_added),
            "logic_deleted": len(self.logic_deleted),
            "logic_modified": len(self.logic_modified),
        }


def compare_schedules(left: Schedule, right: Schedule, profile=None) -> Comparison:
    warnings = list(left.warnings) + list(right.warnings)
    if left.project.short_name and right.project.short_name:
        if left.project.short_name != right.project.short_name:
            warnings.append(
                f"Project short names differ: {left.project.short_name!r} vs "
                f"{right.project.short_name!r}"
            )

    left_ids = set(left.activities)
    right_ids = set(right.activities)

    added = [
        ActivityDelta(
            task_code=code,
            name_before="",
            name_after=right.activities[code].task_name,
            status="added",
            klass="revision",
        )
        for code in sorted(right_ids - left_ids)
    ]
    deleted = [
        ActivityDelta(
            task_code=code,
            name_before=left.activities[code].task_name,
            name_after="",
            status="deleted",
            klass="revision",
        )
        for code in sorted(left_ids - right_ids)
    ]

    modified: list[ActivityDelta] = []
    unchanged = 0
    for code in sorted(left_ids & right_ids):
        delta = _diff_activity(left.activities[code], right.activities[code])
        if delta.changes:
            modified.append(delta)
        else:
            unchanged += 1

    la = _rel_map(left.relationships)
    ra = _rel_map(right.relationships)
    logic_added = []
    logic_deleted = []
    logic_modified = []
    for key in sorted(set(la) | set(ra)):
        lrel = la.get(key)
        rrel = ra.get(key)
        pred, succ, typ = key
        if lrel is None and rrel is not None:
            logic_added.append(LogicDelta(pred, succ, typ, "added", None, rrel.lag_hr))
        elif lrel is not None and rrel is None:
            logic_deleted.append(
                LogicDelta(pred, succ, typ, "deleted", lrel.lag_hr, None)
            )
        elif lrel is not None and rrel is not None and lrel.lag_hr != rrel.lag_hr:
            logic_modified.append(
                LogicDelta(pred, succ, typ, "modified", lrel.lag_hr, rrel.lag_hr)
            )

    resource_added, resource_deleted, resource_modified = _diff_resources(
        left.assignments, right.assignments, warnings
    )
    calendar_changes = _diff_calendars(left, right, warnings)

    udf_deltas = _diff_udfs(left, right)

    return Comparison(
        left=left,
        right=right,
        added=added,
        deleted=deleted,
        modified=modified,
        unchanged_count=unchanged,
        logic_added=logic_added,
        logic_deleted=logic_deleted,
        logic_modified=logic_modified,
        warnings=warnings,
        resource_added=resource_added,
        resource_deleted=resource_deleted,
        resource_modified=resource_modified,
        calendar_changes=calendar_changes,
        profile=profile,
        udf_added=[d for d in udf_deltas if d.status == "added"],
        udf_deleted=[d for d in udf_deltas if d.status == "deleted"],
        udf_modified=[d for d in udf_deltas if d.status == "modified"],
    )


def _rel_map(rels: list[Relationship]) -> dict[tuple[str, str, str], Relationship]:
    out: dict[tuple[str, str, str], Relationship] = {}
    for r in rels:
        out[r.key] = r
    return out


def _norm(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 4)
    return value


def _diff_activity(a: Activity, b: Activity) -> ActivityDelta:
    fields = {
        "task_name": (a.task_name, b.task_name),
        "status_code": (a.status_code, b.status_code),
        "orig_dur_days": (a.orig_dur_days, b.orig_dur_days),
        "remain_dur_days": (a.remain_dur_days, b.remain_dur_days),
        "target_start": (a.target_start, b.target_start),
        "target_end": (a.target_end, b.target_end),
        "early_start": (a.early_start, b.early_start),
        "early_end": (a.early_end, b.early_end),
        "late_start": (a.late_start, b.late_start),
        "late_end": (a.late_end, b.late_end),
        "act_start": (a.act_start, b.act_start),
        "act_end": (a.act_end, b.act_end),
        "restart": (a.restart, b.restart),
        "reend": (a.reend, b.reend),
        "suspend": (a.suspend, b.suspend),
        "resume": (a.resume, b.resume),
        "cstr_type": (a.cstr_type, b.cstr_type),
        "cstr_date": (a.cstr_date, b.cstr_date),
        "cstr_type2": (a.cstr_type2, b.cstr_type2),
        "cstr_date2": (a.cstr_date2, b.cstr_date2),
        "calendar_name": (a.calendar_name, b.calendar_name),
        "wbs_path": (a.wbs_path, b.wbs_path),
        "phys_complete_pct": (a.phys_complete_pct, b.phys_complete_pct),
        "total_float_days": (a.total_float_days, b.total_float_days),
        "free_float_days": (a.free_float_days, b.free_float_days),
        "task_type": (a.task_type, b.task_type),
    }
    changes: list[FieldChange] = []
    for name, (before, after) in fields.items():
        if _norm(before) != _norm(after):
            if name in PROGRESS_FIELDS:
                klass = "progress"
            elif name in REVISION_FIELDS:
                klass = "revision"
            elif name in DATE_FIELDS or name in {"total_float_days", "free_float_days"}:
                klass = "date"
            else:
                klass = "other"
            changes.append(FieldChange(name, before, after, klass))

    # activity codes
    all_codes = set(a.activity_codes) | set(b.activity_codes)
    for ck in sorted(all_codes):
        bv = a.activity_codes.get(ck, "")
        av = b.activity_codes.get(ck, "")
        if bv != av:
            changes.append(FieldChange(f"code:{ck}", bv, av, "revision"))

    for name in sorted(set(a.udfs) | set(b.udfs)):
        before, after = a.udfs.get(name), b.udfs.get(name)
        if name not in a.udfs or name not in b.udfs or _norm(before) != _norm(after):
            changes.append(FieldChange(f"udf:{name}", before, after, "revision"))

    klasses = {c.klass for c in changes}
    if "progress" in klasses and "revision" in klasses:
        klass = "both"
    elif "revision" in klasses:
        klass = "revision"
    elif "progress" in klasses:
        klass = "progress"
    elif changes:
        klass = "date"
    else:
        klass = "n/a"

    return ActivityDelta(
        task_code=a.task_code,
        name_before=a.task_name,
        name_after=b.task_name,
        status="modified",
        klass=klass,
        changes=changes,
    )


def _diff_resources(left, right, warnings=None):
    remaining_left, remaining_right = set(range(len(left))), set(range(len(right)))
    matched = []
    keys = (
        lambda a: (a.task_code, "guid", a.guid) if a.guid else None,
        lambda a: (
            a.task_code,
            a.rsrc_name,
            a.role_id,
            tuple(_norm(getattr(a, f)) for f in RESOURCE_FIELDS),
        ),
        lambda a: (a.task_code, a.rsrc_name, a.rsrc_id, a.role_id),
        lambda a: (a.task_code, a.rsrc_name, a.role_id) if a.rsrc_name else None,
        lambda a: (a.task_code, a.rsrc_id, a.role_id) if a.rsrc_id else None,
    )
    ambiguous = set()
    for level, key_for in enumerate(keys):
        buckets = defaultdict(deque)
        for i in sorted(remaining_left):
            key = key_for(left[i])
            if key is not None:
                buckets[key].append(i)
        for i in sorted(remaining_right):
            key = key_for(right[i])
            if key is not None and buckets[key]:
                if level >= 2 and len(buckets[key]) > 1:
                    ambiguous.add((right[i].task_code, right[i].rsrc_name))
                j = buckets[key].popleft()
                remaining_left.remove(j)
                remaining_right.remove(i)
                matched.append((left[j], right[i]))
    if warnings is not None and ambiguous:
        warnings.append(
            f"{len(ambiguous)} activity/resource groups have ambiguous duplicate assignment matches; remaining rows paired in export order. Review Resource Value Changes."
        )
    changes = []
    for a, b in matched:
        fields = [
            FieldChange(f, getattr(a, f), getattr(b, f), "revision")
            for f in RESOURCE_FIELDS
            if _norm(getattr(a, f)) != _norm(getattr(b, f))
        ]
        if fields:
            changes.append(ResourceDelta(a, b, fields))
    return (
        [right[i] for i in sorted(remaining_right)],
        [left[i] for i in sorted(remaining_left)],
        changes,
    )


def _diff_calendars(left, right, warnings):
    from xercompare.model.calendars import resolve_calendar, definition_values

    values = []
    for side, schedule in [("Base", left), ("Revised", right)]:
        definitions = {}
        for cid, cal in schedule.calendars.items():
            definition = resolve_calendar(schedule, cid)
            definitions[cid] = definition_values(schedule, cid, definition)
            if not definition.available and cal.raw.get("clndr_data"):
                warnings.append(f"{side} calendar {cal.name}: {definition.note}")
        values.append(definitions)
    changes = []
    for code in sorted(set(left.activities) & set(right.activities)):
        a, b = left.activities[code], right.activities[code]
        before, after = values[0].get(a.clndr_id, {}), values[1].get(b.clndr_id, {})
        for key in sorted(set(before) | set(after)):
            if key == "Calendar":
                continue
            if _norm(before.get(key)) != _norm(after.get(key)):
                changes.append(
                    CalendarDelta(
                        code, key, before.get(key), after.get(key), b.calendar_name
                    )
                )
    return changes


def _diff_udfs(left: Schedule, right: Schedule) -> list[UDFDelta]:
    deltas = []
    for code in sorted(set(left.activities) | set(right.activities)):
        before = left.activities[code].udfs if code in left.activities else {}
        after = right.activities[code].udfs if code in right.activities else {}
        for name in sorted(set(before) | set(after)):
            if name not in before:
                status = "added"
            elif name not in after:
                status = "deleted"
            elif _norm(before[name]) != _norm(after[name]):
                status = "modified"
            else:
                continue
            deltas.append(
                UDFDelta(code, name, status, before.get(name), after.get(name))
            )
    return deltas
