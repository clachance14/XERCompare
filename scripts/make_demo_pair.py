"""Write a small industrial-style XER pair that looks like a monthly update."""

from pathlib import Path

from tests.fixtures.make_xer import make_xer


def main(out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)

    left_acts = [
        {"task_id": "1", "task_code": "A1000", "task_name": "Project Start Milestone", "dur_hr": 0, "task_type": "TT_Mile", "es": "2026-01-05 08:00", "ef": "2026-01-05 08:00", "tf_hr": 0},
        {"task_id": "2", "task_code": "A1100", "task_name": "Issue IFC Pipe Rack Drawings", "dur_hr": 80, "es": "2026-01-05 08:00", "ef": "2026-01-16 17:00", "tf_hr": 16},
        {"task_id": "3", "task_code": "A1200", "task_name": "Procure Structural Steel – Rack 4", "dur_hr": 160, "es": "2026-01-19 08:00", "ef": "2026-02-13 17:00", "tf_hr": 16},
        {"task_id": "4", "task_code": "A1300", "task_name": "Site Mobilization & Temp Facilities", "dur_hr": 80, "es": "2026-01-05 08:00", "ef": "2026-01-16 17:00", "tf_hr": 40},
        {"task_id": "5", "task_code": "A2100", "task_name": "Set Rack 4 Steel", "dur_hr": 120, "es": "2026-02-16 08:00", "ef": "2026-03-06 17:00", "tf_hr": 16},
        {"task_id": "6", "task_code": "A2200", "task_name": "Install 12\" P-1401 Header", "dur_hr": 80, "es": "2026-03-09 08:00", "ef": "2026-03-20 17:00", "tf_hr": 16, "cstr_type": "CS_MSO", "cstr_date": "2026-03-09 08:00"},
        {"task_id": "7", "task_code": "A2300", "task_name": "Hydrotest P-1401 Header", "dur_hr": 24, "es": "2026-03-23 08:00", "ef": "2026-03-25 17:00", "tf_hr": 16},
        {"task_id": "8", "task_code": "A3100", "task_name": "Tie-in to Existing Unit 14", "dur_hr": 40, "es": "2026-03-26 08:00", "ef": "2026-04-01 17:00", "tf_hr": 0},
        {"task_id": "9", "task_code": "A9000", "task_name": "Mechanical Completion", "dur_hr": 0, "task_type": "TT_FinMile", "es": "2026-04-02 17:00", "ef": "2026-04-02 17:00", "tf_hr": 0},
        {"task_id": "10", "task_code": "A4100", "task_name": "Old Scaffold Package (to be removed)", "dur_hr": 32, "es": "2026-01-19 08:00", "ef": "2026-01-23 17:00", "tf_hr": 200},
    ]
    left_preds = [
        {"pred_id": "1", "succ_id": "2"},
        {"pred_id": "1", "succ_id": "4"},
        {"pred_id": "2", "succ_id": "3"},
        {"pred_id": "3", "succ_id": "5"},
        {"pred_id": "4", "succ_id": "5"},
        {"pred_id": "5", "succ_id": "6"},
        {"pred_id": "6", "succ_id": "7"},
        {"pred_id": "7", "succ_id": "8"},
        {"pred_id": "8", "succ_id": "9"},
        {"pred_id": "4", "succ_id": "10"},
    ]

    right_acts = [
        {"task_id": "1", "task_code": "A1000", "task_name": "Project Start Milestone", "dur_hr": 0, "task_type": "TT_Mile", "es": "2026-01-05 08:00", "ef": "2026-01-05 08:00", "tf_hr": 0, "status_code": "TK_Complete", "act_start": "2026-01-05 08:00", "act_end": "2026-01-05 08:00", "remain_hr": 0, "pct": 100},
        {"task_id": "2", "task_code": "A1100", "task_name": "Issue IFC Pipe Rack Drawings", "dur_hr": 80, "es": "2026-01-05 08:00", "ef": "2026-01-16 17:00", "tf_hr": 0, "status_code": "TK_Complete", "act_start": "2026-01-05 08:00", "act_end": "2026-01-20 17:00", "remain_hr": 0, "pct": 100},
        {"task_id": "3", "task_code": "A1200", "task_name": "Procure Structural Steel – Rack 4", "dur_hr": 200, "es": "2026-01-21 08:00", "ef": "2026-02-27 17:00", "tf_hr": 0, "status_code": "TK_Active", "act_start": "2026-01-22 08:00", "remain_hr": 80, "pct": 55},
        {"task_id": "4", "task_code": "A1300", "task_name": "Site Mobilization & Temp Facilities", "dur_hr": 80, "es": "2026-01-05 08:00", "ef": "2026-01-16 17:00", "tf_hr": 24, "status_code": "TK_Complete", "act_start": "2026-01-05 08:00", "act_end": "2026-01-16 17:00", "remain_hr": 0, "pct": 100},
        {"task_id": "5", "task_code": "A2100", "task_name": "Set Rack 4 Steel", "dur_hr": 120, "es": "2026-03-02 08:00", "ef": "2026-03-20 17:00", "tf_hr": 0},
        {"task_id": "6", "task_code": "A2200", "task_name": "Install 12\" P-1401 Header", "dur_hr": 80, "es": "2026-03-23 08:00", "ef": "2026-04-03 17:00", "tf_hr": 0, "cstr_type": "", "cstr_date": ""},
        {"task_id": "7", "task_code": "A2300", "task_name": "Hydrotest P-1401 Header", "dur_hr": 24, "es": "2026-04-06 08:00", "ef": "2026-04-08 17:00", "tf_hr": 0},
        {"task_id": "8", "task_code": "A3100", "task_name": "Tie-in to Existing Unit 14", "dur_hr": 56, "es": "2026-04-09 08:00", "ef": "2026-04-17 17:00", "tf_hr": 0},
        {"task_id": "9", "task_code": "A9000", "task_name": "Mechanical Completion", "dur_hr": 0, "task_type": "TT_FinMile", "es": "2026-04-17 17:00", "ef": "2026-04-17 17:00", "tf_hr": 0},
        {"task_id": "11", "task_code": "A2210", "task_name": "Install 8\" P-1402 Branch (added)", "dur_hr": 40, "es": "2026-03-23 08:00", "ef": "2026-03-27 17:00", "tf_hr": 80},
    ]
    right_preds = [
        {"pred_id": "1", "succ_id": "2"},
        {"pred_id": "1", "succ_id": "4"},
        {"pred_id": "2", "succ_id": "3"},
        {"pred_id": "3", "succ_id": "5"},
        {"pred_id": "4", "succ_id": "5"},
        {"pred_id": "5", "succ_id": "6", "lag": 16},
        {"pred_id": "6", "succ_id": "7"},
        {"pred_id": "7", "succ_id": "8"},
        {"pred_id": "8", "succ_id": "9"},
        {"pred_id": "5", "succ_id": "11"},
        {"pred_id": "11", "succ_id": "7", "type": "PR_SS", "lag": 8},
    ]

    left = out / "U14_RACK4_BL.xer"
    right = out / "U14_RACK4_UPD_31MAR26.xer"
    left.write_text(make_xer("U14-RACK4", "2026-01-31 00:00", left_acts, left_preds), encoding="cp1252")
    right.write_text(make_xer("U14-RACK4", "2026-03-31 00:00", right_acts, right_preds), encoding="cp1252")
    return left, right


if __name__ == "__main__":
    from pathlib import Path
    print(main(Path("demo")))
