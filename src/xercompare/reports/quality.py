"""Quality report views, all based on the shared diagnostic results."""

from xercompare.quality.checks import inspect_schedule, milestone_movements
from xercompare.quality.profile import QualityProfile, RULES
from xercompare.model.schedule import Activity


def quality_sheets(wb, c):
    from xercompare.reports.excel import (
        _paired_sheet,
        _banner,
        _style_header_row,
        _paint_row,
        ZEBRA,
        WHITE,
    )

    profile = c.profile or QualityProfile()
    left = {r.key: r for r in inspect_schedule(c.left, profile)}
    right = {r.key: r for r in inspect_schedule(c.right, profile)}

    def grid(name, headers, rows, note=""):
        ws = wb.create_sheet(name)
        _banner(ws, name + (" · " + note if note else ""), len(headers))
        _style_header_row(ws, headers)
        for i, values in enumerate(rows, 5):
            for col, value in enumerate(values, 1):
                ws.cell(i, col, value)
            _paint_row(ws, i, len(headers), ZEBRA if i % 2 else WHITE)
        return ws

    def state(r):
        return "Not assessed" if r.passed is None else "Pass" if r.passed else "Flagged"

    grid(
        "Quality Checks",
        [
            "Check",
            "Base value",
            "Revised value",
            "Unit",
            "Limit (strictly below unless zero)",
            "Base eligible",
            "Revised eligible",
            "Base affected",
            "Revised affected",
            "Base result",
            "Revised result",
            "Note",
        ],
        [
            [
                left[k].name,
                left[k].value,
                right[k].value,
                right[k].unit,
                right[k].limit,
                left[k].eligible,
                right[k].eligible,
                left[k].affected,
                right[k].affected,
                state(left[k]),
                state(right[k]),
                f"Base: {left[k].note} Revised: {right[k].note}",
            ]
            for k in RULES
        ],
        profile.name,
    )
    lf = {f.key: f for r in left.values() for f in r.findings}
    rf = {f.key: f for r in right.values() for f in r.findings}
    rows = []
    for key in sorted(lf.keys() | rf.keys()):
        a, b = lf.get(key), rf.get(key)
        f = b or a
        activity = (
            c.right.activities.get(f.task_code)
            or c.left.activities.get(f.task_code)
            or Activity("", f.task_code, "Unresolved activity")
        )
        rows.append(
            (
                activity,
                [(a.observed if a else None, b.observed if b else None)],
                [
                    f.rule,
                    f.field,
                    f.related,
                    a.reason if a else "",
                    b.reason if b else "",
                ],
            )
        )
    headers = ["Check ID", "Field", "Related activity", "Base reason", "Revised reason"]
    for name, keys in [
        ("Quality Findings", set(RULES)),
        ("Open Ends", {"open_ends", "dangling_start", "dangling_finish"}),
        ("Out of Sequence", {"out_of_sequence"}),
        ("Date Review", {"invalid_dates", "riding_date", "missed_finish"}),
    ]:
        ws = _paired_sheet(
            wb,
            name,
            ["Finding"],
            [r for r in rows if r[2][0] in keys],
            headers,
            "Review evidence; absence of a finding is not proof of a valid schedule",
        )
        ws.column_dimensions["I"].width = 60
        ws.column_dimensions["J"].width = 60
    rows = []
    for code in sorted(c.left.activities.keys() | c.right.activities.keys()):
        a, b = c.left.activities.get(code), c.right.activities.get(code)
        fields = ["cstr_type", "cstr_date", "cstr_type2", "cstr_date2"]
        pairs = [(getattr(a, f, None), getattr(b, f, None)) for f in fields]
        if any(x or y for x, y in pairs):
            rows.append((b or a, pairs, []))
    _paired_sheet(
        wb,
        "Constraint Register",
        ["Constraint", "Constraint date", "Secondary constraint", "Secondary date"],
        rows,
    )
    rows = [
        (a, [(before, after)], [delta, basis])
        for a, before, after, delta, basis in milestone_movements(c)
    ]
    _paired_sheet(
        wb,
        "Milestone Slips",
        ["Stored date"],
        rows,
        ["Movement (elapsed days)", "Date basis"],
        "Positive = later; negative = earlier; elapsed 24-hour days, no CPM",
    )
    grid(
        "Check Settings",
        ["Setting", "Value", "Meaning"],
        [
            [
                "Profile",
                profile.name,
                "Applies to Quality Checks; conventional DCMA thresholds remain separate.",
            ],
            ["High float days", profile.high_float_days, "Activity-calendar days"],
            [
                "High duration days",
                profile.high_duration_days,
                "Activity-calendar days",
            ],
            *[
                [
                    k,
                    profile.limit(k),
                    (
                        "Disabled"
                        if k in profile.disabled
                        else RULES[k][0] + "; " + RULES[k][2]
                    ),
                ]
                for k in RULES
            ],
        ],
    )
