"""Evidence-backed diagnostics using exported values; no CPM engine."""

from dataclasses import dataclass, field
from datetime import datetime
from xercompare.quality.profile import QualityProfile, RULES

HARD = {
    "CS_MANDSTART",
    "CS_MANDFIN",
    "CS_MSO",
    "CS_MFO",
    "CS_SNLT",
    "CS_FNLT",
    "CS_START",
    "CS_FINISH",
}


def parsed_date(text):
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.strip())
    except (ValueError, TypeError, AttributeError):
        return None


@dataclass
class Finding:
    rule: str
    task_code: str
    field: str
    observed: object
    reason: str
    related: str = ""

    @property
    def key(self):
        return (self.rule, self.task_code, self.field, self.related)


@dataclass
class RuleResult:
    key: str
    name: str
    eligible: int
    affected: int
    value: float | int | str
    unit: str
    limit: float
    passed: bool | None
    note: str
    findings: list[Finding] = field(default_factory=list)


def inspect_schedule(schedule, profile=None):
    profile = (profile or QualityProfile()).validate()
    acts = list(schedule.activities.values())
    incomplete = [
        a for a in acts if a.status_code != "TK_Complete" and not a.is_milestone
    ]
    inc = {a.task_code for a in incomplete}
    rels = schedule.relationships
    preds = {a.task_code: [] for a in acts}
    succs = {a.task_code: [] for a in acts}
    findings = {k: [] for k in RULES}
    eligible = {k: len(incomplete) for k in RULES}
    notes = {k: "" for k in RULES}
    date = parsed_date(schedule.project.data_date)

    def add(key, a, field, value, reason, related=""):
        findings[key].append(
            Finding(
                key,
                a.task_code if hasattr(a, "task_code") else a,
                field,
                value,
                reason,
                related,
            )
        )

    for r in rels:
        preds.setdefault(r.succ_code, []).append(r)
        succs.setdefault(r.pred_code, []).append(r)
        for key, condition in [
            ("leads", r.lag_hr < 0),
            ("lags", r.lag_hr > 0),
            ("non_fs", r.type_label != "FS"),
        ]:
            if condition:
                add(
                    key,
                    r.succ_code,
                    f"{r.type_label} lag (hours)",
                    r.lag_hr,
                    f"{r.pred_code} -> {r.succ_code}: {r.type_label} relationship",
                    r.pred_code,
                )
        pred = schedule.activities.get(r.pred_code)
        succ = schedule.activities.get(r.succ_code)
        if not pred or not succ:
            continue
        # Test the actual event governed by each relationship, not all links as FS.
        pred_event = "act_end" if r.type_label in {"FS", "FF"} else "act_start"
        succ_event = "act_start" if r.type_label in {"FS", "SS"} else "act_end"
        pd, sd = parsed_date(getattr(pred, pred_event)), parsed_date(
            getattr(succ, succ_event)
        )
        if sd and (not pd or pd > sd):
            add(
                "out_of_sequence",
                succ,
                f"{r.type_label} {succ_event}",
                getattr(succ, succ_event),
                f"Actual successor event precedes predecessor {pred_event}, or predecessor actual is absent. "
                "Suspect only: lag calendars and scheduling options are not recalculated.",
                r.pred_code,
            )
    for key in ["leads", "lags", "non_fs"]:
        eligible[key] = len(rels)
    assigned = {a.task_code for a in schedule.assignments}
    if not assigned:
        notes["missing_resources"] = (
            "Not assessed: no resource assignments were exported."
        )
    for a in incomplete:
        incoming, outgoing = preds[a.task_code], succs[a.task_code]
        if not incoming or not outgoing:
            missing = "/".join(
                x
                for x, test in [
                    ("predecessor", not incoming),
                    ("successor", not outgoing),
                ]
                if test
            )
            add(
                "open_ends",
                a,
                "Missing logic",
                missing,
                "Incomplete duration activity lacks " + missing + ".",
            )
        if not any(r.type_label in {"FS", "SS"} for r in incoming):
            add(
                "dangling_start",
                a,
                "Start logic",
                "No FS/SS predecessor",
                "No incoming relationship constrains the start event.",
            )
        if not any(r.type_label in {"FS", "FF"} for r in outgoing):
            add(
                "dangling_finish",
                a,
                "Finish logic",
                "No FS/FF successor",
                "No outgoing relationship uses the finish event.",
            )
        for label, value in [
            ("Primary constraint", a.cstr_type),
            ("Secondary constraint", a.cstr_type2),
        ]:
            if value in HARD:
                add(
                    "hard_constraints",
                    a,
                    label,
                    value,
                    "Hard constraint on an incomplete duration activity.",
                )
        for key, value, limit, label in [
            (
                "high_float",
                a.total_float_days,
                profile.high_float_days,
                "Total float (days)",
            ),
            (
                "high_duration",
                a.orig_dur_days,
                profile.high_duration_days,
                "Original duration (days)",
            ),
        ]:
            if value is not None and value > limit:
                add(
                    key, a, label, value, f"Exceeds {limit:.1f} activity-calendar days."
                )
        if a.total_float_hr is not None and a.total_float_hr < 0:
            add(
                "negative_float",
                a,
                "Total float (days)",
                a.total_float_days,
                "Stored total float is negative.",
            )
        if assigned and (a.orig_dur_hr or 0) > 0 and a.task_code not in assigned:
            add(
                "missing_resources",
                a,
                "Assignments",
                0,
                "Resource-loaded schedule; this activity has no assignment.",
            )
    for key, attr in [
        ("high_float", "total_float_days"),
        ("negative_float", "total_float_hr"),
        ("high_duration", "orig_dur_days"),
    ]:
        eligible[key] = sum(getattr(a, attr) is not None for a in incomplete)
    eligible["out_of_sequence"] = len(rels)
    eligible["invalid_dates"] = len(acts)
    eligible["riding_date"] = len(incomplete)
    due = [
        a
        for a in acts
        if date and parsed_date(a.target_end) and parsed_date(a.target_end) < date
    ]
    eligible["missed_finish"] = len(due)
    notes["missed_finish"] = (
        "Stored target finish proxy; not an approved-baseline DCMA result."
    )
    for a in due:
        actual = parsed_date(a.act_end)
        if not actual or actual > parsed_date(a.target_end):
            add(
                "missed_finish",
                a,
                "Target finish",
                a.target_end,
                "Target finish before data date; no actual finish or actual finish later than target.",
            )
    for a in acts:
        if date:
            for attr in ["act_start", "act_end"]:
                value = parsed_date(getattr(a, attr))
                if value and value > date:
                    add(
                        "invalid_dates",
                        a,
                        attr,
                        getattr(a, attr),
                        "Actual date is after the stored data date.",
                    )
                elif getattr(a, attr) and value is None:
                    add(
                        "invalid_dates",
                        a,
                        attr,
                        getattr(a, attr),
                        "Stored actual date cannot be read.",
                    )
            for attr, applies in [
                ("early_start", a.status_code == "TK_NotStart"),
                ("early_end", a.status_code != "TK_Complete"),
            ]:
                value = parsed_date(getattr(a, attr))
                if applies and value and value < date:
                    add(
                        "invalid_dates",
                        a,
                        attr,
                        getattr(a, attr),
                        "Unfinished event is before the stored data date.",
                    )
            if a.task_code in inc:
                remaining = parsed_date(a.restart or a.early_start)
                if remaining and remaining.date() == date.date():
                    add(
                        "riding_date",
                        a,
                        "Remaining start",
                        a.restart or a.early_start,
                        "Remaining start falls on the data-date day; review indicator, not necessarily an error.",
                    )
    results = []
    for key, (label, _, unit) in RULES.items():
        rows = findings[key]
        affected = (
            len(rows)
            if key in {"leads", "lags", "non_fs", "out_of_sequence"}
            else len({f.task_code for f in rows})
        )
        n = eligible[key]
        limit = profile.limit(key)
        note = notes[key]
        unavailable = not n or (key == "missing_resources" and not assigned)
        if key in {"invalid_dates", "missed_finish", "riding_date"} and date is None:
            unavailable = True
            note = "Not assessed: a valid stored data date is required."
        if not n:
            note = (
                note + " " if note else ""
            ) + "Not assessed: no eligible records with the required values."
        if key in profile.disabled:
            unavailable = True
            note = "Disabled in profile."
            rows = []
            affected = 0
        value = 100.0 * affected / n if unit == "%" and n else affected
        passed = None if unavailable else (value == 0 if limit == 0 else value < limit)
        results.append(
            RuleResult(
                key,
                label,
                n,
                affected,
                "N/A" if unavailable else value,
                unit,
                limit,
                passed,
                note,
                rows,
            )
        )
    return results


def milestone_movements(comparison, milestones_only=True):
    rows = []
    for code in sorted(
        set(comparison.left.activities) & set(comparison.right.activities)
    ):
        a, b = comparison.left.activities[code], comparison.right.activities[code]
        if milestones_only and not (a.is_milestone or b.is_milestone):
            continue
        field = (
            "early_start"
            if milestones_only and b.task_type == "TT_Mile"
            else "early_end"
        )
        before, after = getattr(a, field), getattr(b, field)
        if before == after:
            continue
        ld, rd = parsed_date(before), parsed_date(after)
        movement = (rd - ld).total_seconds() / 86400 if ld and rd else None
        rows.append((b, before, after, movement, field.replace("_", " ")))
    return sorted(
        rows, key=lambda row: (row[3] is None, -(row[3] or 0), row[0].task_code)
    )
