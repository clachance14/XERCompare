"""Typed schedule objects built from raw XER tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from xercompare.parse.xer_parser import XerFile, as_float, hours_to_days


@dataclass
class Relationship:
    pred_task_id: str
    succ_task_id: str
    pred_code: str = ""
    succ_code: str = ""
    pred_type: str = "PR_FS"  # PR_FS, PR_SS, PR_FF, PR_SF
    lag_hr: float = 0.0

    @property
    def type_label(self) -> str:
        return {
            "PR_FS": "FS",
            "PR_SS": "SS",
            "PR_FF": "FF",
            "PR_SF": "SF",
        }.get(self.pred_type, self.pred_type or "FS")

    @property
    def key(self) -> tuple[str, str, str]:
        # Match on visible IDs + type. Lag is a field, not identity.
        return (self.pred_code, self.succ_code, self.type_label)


@dataclass
class ResourceAssignment:
    task_id: str
    task_code: str
    rsrc_id: str
    rsrc_name: str
    target_qty: float | None = None
    remain_qty: float | None = None
    act_reg_qty: float | None = None
    target_cost: float | None = None
    remain_cost: float | None = None
    act_reg_cost: float | None = None
    target_qty_per_hr: float | None = None
    remain_qty_per_hr: float | None = None
    act_ot_qty: float | None = None
    act_ot_cost: float | None = None
    cost_per_qty: float | None = None
    guid: str = ""
    role_id: str = ""


@dataclass
class Activity:
    task_id: str
    task_code: str
    task_name: str
    wbs_id: str = ""
    wbs_path: str = ""
    clndr_id: str = ""
    calendar_name: str = ""
    task_type: str = ""
    status_code: str = ""
    orig_dur_hr: float | None = None
    remain_dur_hr: float | None = None
    target_start: str = ""
    target_end: str = ""
    early_start: str = ""
    early_end: str = ""
    late_start: str = ""
    late_end: str = ""
    act_start: str = ""
    act_end: str = ""
    restart: str = ""
    reend: str = ""
    cstr_type: str = ""
    cstr_date: str = ""
    cstr_type2: str = ""
    cstr_date2: str = ""
    total_float_hr: float | None = None
    free_float_hr: float | None = None
    phys_complete_pct: float | None = None
    complete_pct_type: str = ""
    suspend: str = ""
    resume: str = ""
    hours_per_day: float = 8.0
    activity_codes: dict[str, str] = field(default_factory=dict)
    udfs: dict[str, str | float] = field(default_factory=dict)
    udf_types: dict[str, str] = field(default_factory=dict)

    @property
    def orig_dur_days(self) -> float | None:
        return hours_to_days(self.orig_dur_hr, self.hours_per_day)

    @property
    def remain_dur_days(self) -> float | None:
        return hours_to_days(self.remain_dur_hr, self.hours_per_day)

    @property
    def total_float_days(self) -> float | None:
        return hours_to_days(self.total_float_hr, self.hours_per_day)

    @property
    def free_float_days(self) -> float | None:
        return hours_to_days(self.free_float_hr, self.hours_per_day)

    @property
    def is_critical(self) -> bool:
        tf = self.total_float_hr
        return tf is not None and tf <= 0

    @property
    def is_milestone(self) -> bool:
        return self.task_type in {"TT_Mile", "TT_FinMile"} or (
            self.orig_dur_hr is not None and self.orig_dur_hr == 0
        )


@dataclass
class Calendar:
    clndr_id: str
    name: str
    clndr_type: str = ""
    day_hr_cnt: float = 8.0
    raw: dict[str, str] = field(default_factory=dict)


@dataclass
class WBSNode:
    wbs_id: str
    short_name: str
    name: str
    parent_wbs_id: str = ""
    proj_id: str = ""


@dataclass
class ProjectInfo:
    proj_id: str
    short_name: str
    name: str = ""
    plan_start: str = ""
    plan_end: str = ""
    data_date: str = ""
    clndr_id: str = ""


@dataclass
class Schedule:
    source: Path
    p6_version: str | None
    project: ProjectInfo
    activities: dict[str, Activity]  # keyed by task_code
    activities_by_id: dict[str, Activity]
    relationships: list[Relationship]
    calendars: dict[str, Calendar]
    wbs: dict[str, WBSNode]
    assignments: list[ResourceAssignment]
    resources: dict[str, dict[str, str]]
    warnings: list[str] = field(default_factory=list)
    raw: XerFile | None = None

    @property
    def activity_count(self) -> int:
        return len(self.activities)


def build_schedule(xer: XerFile) -> Schedule:
    projects = xer.table("PROJECT")
    if not projects:
        raise ValueError(f"{xer.path.name}: no PROJECT table")
    if len(projects) > 1:
        xer.warnings.append(
            f"{len(projects)} projects in file; using first ({projects[0].get('proj_short_name')})"
        )
    prow = projects[0]
    proj_id = prow.get("proj_id", "")
    project = ProjectInfo(
        proj_id=proj_id,
        short_name=prow.get("proj_short_name", xer.path.stem),
        name=prow.get("proj_short_name", ""),
        plan_start=prow.get("plan_start_date", ""),
        plan_end=prow.get("plan_end_date", ""),
        data_date=prow.get("last_recalc_date", "") or prow.get("scd_end_date", ""),
        clndr_id=prow.get("clndr_id", ""),
    )

    calendars: dict[str, Calendar] = {}
    for row in xer.table("CALENDAR"):
        cid = row.get("clndr_id", "")
        hours = as_float(row.get("day_hr_cnt"), 8.0) or 8.0
        calendars[cid] = Calendar(
            clndr_id=cid,
            name=row.get("clndr_name", ""),
            clndr_type=row.get("clndr_type", ""),
            day_hr_cnt=hours,
            raw=row,
        )

    wbs: dict[str, WBSNode] = {}
    for row in xer.table("PROJWBS"):
        wid = row.get("wbs_id", "")
        wbs[wid] = WBSNode(
            wbs_id=wid,
            short_name=row.get("wbs_short_name", ""),
            name=row.get("wbs_name", ""),
            parent_wbs_id=row.get("parent_wbs_id", ""),
            proj_id=row.get("proj_id", ""),
        )

    def wbs_path(wid: str) -> str:
        parts: list[str] = []
        seen: set[str] = set()
        cur = wid
        while cur and cur in wbs and cur not in seen:
            seen.add(cur)
            node = wbs[cur]
            parts.append(node.short_name or node.name)
            cur = node.parent_wbs_id
        return " / ".join(reversed(parts))

    code_types = {
        r.get("actv_code_type_id", ""): r.get(
            "actv_code_type", r.get("actv_code_name", "")
        )
        for r in xer.table("ACTVTYPE")
    }
    code_values = {r.get("actv_code_id", ""): r for r in xer.table("ACTVCODE")}
    assignments_by_task: dict[str, dict[str, str]] = {}
    for row in xer.table("TASKACTV"):
        tid = row.get("task_id", "")
        cid = row.get("actv_code_id", "")
        cv = code_values.get(cid, {})
        type_id = cv.get("actv_code_type_id", "")
        type_name = code_types.get(type_id, type_id)
        value = cv.get("short_name") or cv.get("actv_code_name") or ""
        assignments_by_task.setdefault(tid, {})[type_name or cid] = value

    activities_by_id: dict[str, Activity] = {}
    activities: dict[str, Activity] = {}
    for row in xer.table("TASK"):
        if proj_id and row.get("proj_id") and row.get("proj_id") != proj_id:
            continue
        tid = row.get("task_id", "")
        code = row.get("task_code", tid)
        cal = calendars.get(row.get("clndr_id", ""), None)
        act = Activity(
            task_id=tid,
            task_code=code,
            task_name=row.get("task_name", ""),
            wbs_id=row.get("wbs_id", ""),
            wbs_path=wbs_path(row.get("wbs_id", "")),
            clndr_id=row.get("clndr_id", ""),
            calendar_name=cal.name if cal else "",
            task_type=row.get("task_type", ""),
            status_code=row.get("status_code", ""),
            orig_dur_hr=as_float(row.get("target_drtn_hr_cnt")),
            remain_dur_hr=as_float(row.get("remain_drtn_hr_cnt")),
            target_start=row.get("target_start_date", ""),
            target_end=row.get("target_end_date", ""),
            early_start=row.get("early_start_date", ""),
            early_end=row.get("early_end_date", ""),
            late_start=row.get("late_start_date", ""),
            late_end=row.get("late_end_date", ""),
            act_start=row.get("act_start_date", ""),
            act_end=row.get("act_end_date", ""),
            suspend=row.get("suspend_date", ""),
            resume=row.get("resume_date", ""),
            restart=row.get("restart_date", ""),
            reend=row.get("reend_date", ""),
            cstr_type=row.get("cstr_type", ""),
            cstr_date=row.get("cstr_date", ""),
            cstr_type2=row.get("cstr_type2", ""),
            cstr_date2=row.get("cstr_date2", ""),
            total_float_hr=as_float(row.get("total_float_hr_cnt")),
            free_float_hr=as_float(row.get("free_float_hr_cnt")),
            phys_complete_pct=as_float(row.get("phys_complete_pct")),
            complete_pct_type=row.get("complete_pct_type", ""),
            hours_per_day=cal.day_hr_cnt if cal else 8.0,
            activity_codes=assignments_by_task.get(tid, {}),
        )
        activities_by_id[tid] = act
        if code in activities:
            xer.warnings.append(f"Duplicate activity ID {code}; last row wins")
        activities[code] = act

    relationships: list[Relationship] = []
    for row in xer.table("TASKPRED"):
        if row.get("proj_id") and row["proj_id"] != proj_id:
            continue
        pred_id = row.get("pred_task_id", "")
        succ_id = row.get("task_id", "")
        pred = activities_by_id.get(pred_id)
        succ = activities_by_id.get(succ_id)
        if pred is None or succ is None:
            xer.warnings.append(
                f"Relationship {pred_id} -> {succ_id} has an unresolved endpoint; "
                "stored internal ID used for that endpoint (external or missing activity)"
            )
        relationships.append(
            Relationship(
                pred_task_id=pred_id,
                succ_task_id=succ_id,
                pred_code=pred.task_code if pred else pred_id,
                succ_code=succ.task_code if succ else succ_id,
                pred_type=row.get("pred_type", "PR_FS"),
                lag_hr=as_float(row.get("lag_hr_cnt"), 0.0) or 0.0,
            )
        )

    resources = {r.get("rsrc_id", ""): r for r in xer.table("RSRC")}
    assignments: list[ResourceAssignment] = []
    for row in xer.table("TASKRSRC"):
        if row.get("proj_id") and row["proj_id"] != proj_id:
            continue
        tid = row.get("task_id", "")
        act = activities_by_id.get(tid)
        if act is None:
            xer.warnings.append(
                f"Resource assignment references unknown task_id {tid}; skipped"
            )
            continue
        if activities.get(act.task_code) is not act:
            continue
        rid = row.get("rsrc_id", "")
        rsrc = resources.get(rid, {})
        assignments.append(
            ResourceAssignment(
                task_id=tid,
                task_code=act.task_code if act else tid,
                rsrc_id=rid,
                rsrc_name=rsrc.get("rsrc_name", rid),
                target_qty=as_float(row.get("target_qty")),
                remain_qty=as_float(row.get("remain_qty")),
                act_reg_qty=as_float(row.get("act_reg_qty")),
                target_cost=as_float(row.get("target_cost")),
                remain_cost=as_float(row.get("remain_cost")),
                act_reg_cost=as_float(row.get("act_reg_cost")),
                target_qty_per_hr=as_float(row.get("target_qty_per_hr")),
                remain_qty_per_hr=as_float(row.get("remain_qty_per_hr")),
                act_ot_qty=as_float(row.get("act_ot_qty")),
                act_ot_cost=as_float(row.get("act_ot_cost")),
                cost_per_qty=as_float(row.get("cost_per_qty")),
                guid=row.get("guid", ""),
                role_id=row.get("role_id", ""),
            )
        )

    _attach_activity_udfs(xer, proj_id, activities, activities_by_id)

    return Schedule(
        source=xer.path,
        p6_version=xer.version,
        project=project,
        activities=activities,
        activities_by_id=activities_by_id,
        relationships=relationships,
        calendars=calendars,
        wbs=wbs,
        assignments=assignments,
        resources=resources,
        warnings=list(xer.warnings),
        raw=xer,
    )


def _attach_activity_udfs(xer, proj_id, activities, activities_by_id):
    definitions = {row.get("udf_type_id", ""): row for row in xer.table("UDFTYPE")}
    value_fields = {
        "FT_TEXT": "udf_text",
        "FT_DATE": "udf_date",
        "FT_START_DATE": "udf_date",
        "FT_END_DATE": "udf_date",
        "FT_FLOAT": "udf_number",
        "FT_INT": "udf_number",
        "FT_MONEY": "udf_number",
        "FT_COST": "udf_number",
        "FT_CODE": "udf_code_id",
    }
    ignored_scopes = set()
    for row in xer.table("UDFVALUE"):
        if row.get("proj_id") and row["proj_id"] != proj_id:
            continue
        type_id = row.get("udf_type_id", "")
        definition = definitions.get(type_id)
        if definition is None:
            xer.warnings.append(
                f"UDFVALUE references unknown udf_type_id {type_id}; skipped"
            )
            continue
        scope = definition.get("table_name", "").upper()
        if scope != "TASK":
            ignored_scopes.add(scope or "unspecified")
            continue
        activity = activities_by_id.get(row.get("fk_id", ""))
        if activity is None:
            xer.warnings.append(
                f"Activity UDF {type_id} references unknown task_id {row.get('fk_id')}; skipped"
            )
            continue
        if activities.get(activity.task_code) is not activity:
            continue
        name = (
            definition.get("udf_type_label")
            or definition.get("udf_type_name")
            or f"UDF {type_id}"
        )
        value_field = value_fields.get(definition.get("logical_data_type", ""))
        if value_field is None:
            value_field = next(
                (
                    f
                    for f in ("udf_text", "udf_number", "udf_date", "udf_code_id")
                    if row.get(f, "") != ""
                ),
                "udf_text",
            )
        value = row.get(value_field, "")
        if value_field == "udf_number" and value != "":
            numeric = as_float(value)
            if numeric is None:
                xer.warnings.append(
                    f"Invalid numeric UDF {name!r} on {activity.task_code}; kept as text"
                )
            else:
                value = numeric
        if name in activity.udfs:
            xer.warnings.append(
                f"Duplicate UDF label {name!r} on {activity.task_code}; last row wins"
            )
        activity.udfs[name] = value
        activity.udf_types[name] = definition.get("logical_data_type", "").upper()
    for scope in sorted(ignored_scopes):
        xer.warnings.append(
            f"UDF scope {scope} is not compared; only activity (TASK) UDFs are supported"
        )
