"""Build synthetic XERs, including quoted cells and optional named tables."""

from __future__ import annotations

import csv
from io import StringIO


def _table(name: str, fields: list[str], rows: list[list[str]]) -> str:
    stream = StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(["%T", name])
    writer.writerow(["%F", *fields])
    for row in rows:
        writer.writerow(["%R", *row])
    return stream.getvalue().rstrip("\n")


def _dict_table(name: str, rows: list[dict], fields: list[str] = ()) -> str:
    fields = list(dict.fromkeys([*fields, *(key for row in rows for key in row)]))
    return _table(
        name,
        fields,
        [
            [
                str(row.get(key, "")) if row.get(key) is not None else ""
                for key in fields
            ]
            for row in rows
        ],
    )


def make_xer(
    project: str = "DEMO",
    data_date: str = "2024-02-01 00:00",
    activities: list[dict] | None = None,
    preds: list[dict] | None = None,
    calendars: list[dict] | None = None,
    resources: list[dict] | None = None,
    assignments: list[dict] | None = None,
    udf_types: list[dict] | None = None,
    udf_values: list[dict] | None = None,
    tables: dict[str, list[dict]] | None = None,
) -> str:
    aliases = {
        "dur_hr": "target_drtn_hr_cnt",
        "remain_hr": "remain_drtn_hr_cnt",
        "es": "early_start_date",
        "ef": "early_end_date",
        "ls": "late_start_date",
        "lf": "late_end_date",
        "act_start": "act_start_date",
        "act_end": "act_end_date",
        "tf_hr": "total_float_hr_cnt",
        "ff_hr": "free_float_hr_cnt",
        "pct": "phys_complete_pct",
    }
    tasks = []
    for i, activity in enumerate(activities or [], start=1):
        row = {
            "task_id": str(i),
            "proj_id": "1",
            "wbs_id": "10",
            "clndr_id": "1",
            "task_code": f"A{i:04d}",
            "task_name": f"Activity {i}",
            "task_type": "TT_Task",
            "status_code": "TK_NotStart",
            "target_drtn_hr_cnt": 40,
            "remain_drtn_hr_cnt": 40,
            "early_start_date": "2024-01-08 08:00",
            "early_end_date": "2024-01-12 17:00",
            "act_start_date": "",
            "act_end_date": "",
            "cstr_type": "",
            "cstr_date": "",
            "total_float_hr_cnt": 80,
            "phys_complete_pct": 0,
        }
        row.update({aliases.get(k, k): v for k, v in activity.items()})
        if "remain_hr" not in activity and "remain_drtn_hr_cnt" not in activity:
            row["remain_drtn_hr_cnt"] = row["target_drtn_hr_cnt"]
        tasks.append(row)
    relationships = []
    for i, pred in enumerate(preds or [], start=1):
        row = {
            "task_pred_id": str(i),
            "proj_id": "1",
            "pred_proj_id": "1",
            "pred_type": "PR_FS",
            "lag_hr_cnt": 0,
        }
        mapping = {
            "succ_id": "task_id",
            "pred_id": "pred_task_id",
            "type": "pred_type",
            "lag": "lag_hr_cnt",
        }
        row.update({mapping.get(k, k): v for k, v in pred.items()})
        relationships.append(row)
    data = {
        "PROJECT": [
            {
                "proj_id": "1",
                "proj_short_name": project,
                "plan_start_date": "2024-01-01 00:00",
                "plan_end_date": "2024-06-01 00:00",
                "last_recalc_date": data_date,
                "clndr_id": "1",
            }
        ],
        "CALENDAR": (
            calendars
            if calendars is not None
            else [
                {
                    "clndr_id": "1",
                    "clndr_name": "Standard 5x8",
                    "clndr_type": "CA_Base",
                    "day_hr_cnt": 8,
                }
            ]
        ),
        "PROJWBS": [
            {
                "wbs_id": "10",
                "proj_id": "1",
                "wbs_short_name": project,
                "wbs_name": "Root",
                "parent_wbs_id": "",
            }
        ],
        "TASK": tasks,
        "TASKPRED": relationships,
    }
    for name, rows in [
        ("RSRC", resources),
        ("TASKRSRC", assignments),
        ("UDFTYPE", udf_types),
        ("UDFVALUE", udf_values),
    ]:
        if rows is not None:
            data[name] = rows
    data.update(tables or {})
    header = (
        "ERMHDR\t20.12\t2024-02-01\tProject\tadmin\tadmin\tdb\tProject Management\tUSD"
    )
    return "\n".join(
        [header, *(_dict_table(name, rows) for name, rows in data.items()), "%E", ""]
    )


def calendar_data(week=None, exceptions=None):
    """Synthetic P6 calendar blob: Sunday=1; OLE date serials for exceptions."""

    def node(name, props="", children=""):
        return f"(0||{name}({props})({children}))"

    def shifts(values):
        return "".join(
            node(i, f"s|{start}|f|{finish}") for i, (start, finish) in enumerate(values)
        )

    children = node(
        "DaysOfWeek",
        children="".join(
            node(day, children=shifts(values)) for day, values in (week or {}).items()
        ),
    )
    children += node(
        "Exceptions",
        children="".join(
            node(i, f"d|{serial}", shifts(values))
            for i, (serial, values) in enumerate((exceptions or {}).items())
        ),
    )
    return node("CalendarData", children=children)
