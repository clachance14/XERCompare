"""Create an entirely synthetic pair exercising the Phase 3 report catalog."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.fixtures.make_xer import make_xer


def main():
    folder = ROOT / "demo" / "phase3"
    folder.mkdir(parents=True, exist_ok=True)
    base = [
        {
            "task_id": "1",
            "task_code": "A1000",
            "task_name": "Install rack piping",
            "dur_hr": 80,
            "remain_hr": 80,
            "tf_hr": 16,
            "ff_hr": 8,
            "ls": "2024-01-10 08:00",
            "lf": "2024-01-14 17:00",
        },
        {
            "task_id": "2",
            "task_code": "A2000",
            "task_name": "Pressure test",
            "tf_hr": 0,
        },
        {
            "task_id": "3",
            "task_code": "A3000",
            "task_name": "Restore insulation",
            "tf_hr": 0,
        },
        {"task_id": "4", "task_code": "A4000", "task_name": "Temporary bypass"},
    ]
    revised = [
        {
            **base[0],
            "task_id": "11",
            "task_name": "Install revised rack piping",
            "clndr_id": "2",
            "dur_hr": 100,
            "remain_hr": 40,
            "pct": 60,
            "status_code": "TK_Active",
            "act_start": "2024-01-08 08:00",
            "cstr_type": "CS_MSO",
            "cstr_date": "2024-01-08 08:00",
            "cstr_type2": "CS_FNLT",
            "cstr_date2": "2024-02-01 17:00",
            "tf_hr": -10,
            "ff_hr": 0,
            "es": "2024-01-15 08:00",
            "ef": "2024-01-26 17:00",
            "ls": "2024-01-14 08:00",
            "lf": "2024-01-25 17:00",
        },
        {**base[1], "task_id": "12", "tf_hr": 16},
        {**base[2], "task_id": "13"},
        {
            "task_id": "14",
            "task_code": "A5000",
            "task_name": "Additional inspection",
            "tf_hr": 0,
        },
    ]
    calendars = [
        {"clndr_id": "1", "clndr_name": "Standard 5x8", "day_hr_cnt": 8},
        {"clndr_id": "2", "clndr_name": "Extended 6x10", "day_hr_cnt": 10},
    ]
    udf_types = [
        {
            "udf_type_id": str(i),
            "udf_type_label": label,
            "table_name": "TASK",
            "logical_data_type": "FT_TEXT",
        }
        for i, label in enumerate(["Permit", "Legacy package", "Review status"], 1)
    ]
    common = {"project": "REPORT-DEMO", "calendars": calendars, "udf_types": udf_types}
    left = make_xer(
        **common,
        activities=base,
        preds=[{"pred_id": "1", "succ_id": "2"}, {"pred_id": "2", "succ_id": "3"}],
        resources=[
            {"rsrc_id": "1", "rsrc_name": "Pipe crew"},
            {"rsrc_id": "2", "rsrc_name": "Old crew"},
        ],
        assignments=[
            {"task_id": "1", "rsrc_id": "1", "target_qty": 80},
            {"task_id": "2", "rsrc_id": "2", "target_qty": 16},
        ],
        udf_values=[
            {"udf_type_id": "2", "fk_id": "1", "udf_text": "PKG-01"},
            {"udf_type_id": "3", "fk_id": "1", "udf_text": "Pending"},
        ]
    )
    right = make_xer(
        **common,
        activities=revised,
        data_date="2024-03-01 00:00",
        preds=[
            {"pred_id": "11", "succ_id": "12", "type": "PR_SS"},
            {"pred_id": "12", "succ_id": "13", "lag": 8},
        ],
        resources=[
            {"rsrc_id": "91", "rsrc_name": "Pipe crew"},
            {"rsrc_id": "92", "rsrc_name": "Test crew"},
        ],
        assignments=[
            {"task_id": "11", "rsrc_id": "91", "target_qty": 100},
            {"task_id": "12", "rsrc_id": "92", "target_qty": 24},
        ],
        udf_values=[
            {"udf_type_id": "1", "fk_id": "11", "udf_text": "Approved"},
            {"udf_type_id": "3", "fk_id": "11", "udf_text": "Reviewed"},
        ]
    )
    (folder / "base.xer").write_text(left, encoding="cp1252")
    (folder / "revised.xer").write_text(right, encoding="cp1252")
    print(folder)


if __name__ == "__main__":
    main()
