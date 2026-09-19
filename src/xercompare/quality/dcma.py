"""DCMA 14-point assessment on stored XER fields.

This is a stored-value implementation. Unevaluated checks and checks requiring
a CPM engine or a defined baseline remain N/A with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass

from xercompare.model.schedule import Schedule


HARD_CONSTRAINTS = {
    "CS_MANDSTART",
    "CS_MANDFIN",
    "CS_START",  # SNLT in some exports
    "CS_FINISH",  # FNLT
    "CS_MEO",
    "CS_MSO",
    "CS_MFO",
    "CS_SNET",
    "CS_FNET",
    "CS_SNLT",
    "CS_FNLT",
}

# DCMA hard set is usually MSO, MFO, SNLT, FNLT
STRICT_HARD = {
    "CS_MANDSTART",
    "CS_MANDFIN",
    "CS_MSO",
    "CS_MFO",
    "CS_SNLT",
    "CS_FNLT",
    "CS_START",
    "CS_FINISH",
}


@dataclass
class Metric:
    number: int
    name: str
    value: float | str
    threshold: str
    passed: bool | None
    unit: str
    note: str = ""


def _incomplete(schedule: Schedule):
    return [
        a
        for a in schedule.activities.values()
        if a.status_code != "TK_Complete" and not a.is_milestone
    ]


def assess(schedule: Schedule) -> list[Metric]:
    from xercompare.quality.checks import inspect_schedule

    results = {r.key: r for r in inspect_schedule(schedule)}
    keys = [
        "open_ends",
        "leads",
        "lags",
        "non_fs",
        "hard_constraints",
        "high_float",
        "negative_float",
        "high_duration",
        "invalid_dates",
        "missing_resources",
    ]
    metrics = []
    for number, key in enumerate(keys, 1):
        r = results[key]
        threshold = "0" if r.limit == 0 else f"< {r.limit:g}{r.unit}"
        metrics.append(
            Metric(number, r.name, r.value, threshold, r.passed, r.unit, r.note)
        )
    metrics.extend(
        [
            Metric(
                11,
                "Missed tasks",
                "N/A",
                "< 5%",
                None,
                "",
                "Requires an approved baseline; stored target-date proxy is in Date Review.",
            ),
            Metric(
                12,
                "Critical path test",
                "N/A",
                "Pass",
                None,
                "",
                "Requires CPM recalculation",
            ),
            Metric(
                13, "CPLI", "N/A", ">= 0.95", None, "", "Requires CPM recalculation"
            ),
            Metric(14, "BEI", "N/A", ">= 0.95", None, "", "Needs a defined baseline"),
        ]
    )
    return metrics
