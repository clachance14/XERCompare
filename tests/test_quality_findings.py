from dataclasses import replace
import pytest
from openpyxl import load_workbook
from tests.test_reports import schedule, records, assert_grid
from xercompare.quality.checks import inspect_schedule
from xercompare.quality.profile import QualityProfile, load_profile, save_profile
from xercompare.compare.engine import compare_schedules
from xercompare.reports.excel import write_excel


def test_quality_evidence_and_resource_absence(tmp_path):
    s = schedule(
        tmp_path / "a.xer",
        data_date="2024-02-01 00:00",
        activities=[
            {
                "task_code": "P",
                "status_code": "TK_Active",
                "act_start": "2024-01-20 08:00",
            },
            {
                "task_code": "S",
                "status_code": "TK_Active",
                "act_start": "2024-02-02 08:00",
                "cstr_type2": "CS_MANDSTART",
                "dur_hr": 400,
                "tf_hr": 400,
                "target_end_date": "2024-01-25 17:00",
            },
            {"task_code": "M", "task_type": "TT_FinMile", "dur_hr": 0},
        ],
        preds=[{"pred_id": "1", "succ_id": "2", "type": "PR_FS", "lag": -8}],
    )
    results = {r.key: r for r in inspect_schedule(s)}
    assert results["missing_resources"].passed is None
    assert results["hard_constraints"].findings[0].task_code == "S"
    assert results["invalid_dates"].findings[0].rule == "invalid_dates"
    assert any(
        f.task_code == "S" and f.related == "P"
        for f in results["out_of_sequence"].findings
    )
    assert results["missed_finish"].eligible == 1
    assert results["missed_finish"].value == 100
    assert results["open_ends"].eligible == 2
    assert results["leads"].value == 100
    assert {f.task_code for f in results["high_duration"].findings} == {"S"}
    assert {
        r.key: r
        for r in inspect_schedule(s, replace(QualityProfile(), high_duration_days=60))
    }["high_duration"].value == 0


def test_relationship_types_do_not_create_false_fs_suspects(tmp_path):
    s = schedule(
        tmp_path / "a.xer",
        activities=[
            {
                "task_code": "P",
                "status_code": "TK_Active",
                "act_start": "2024-01-01 08:00",
            },
            {
                "task_code": "S",
                "status_code": "TK_Active",
                "act_start": "2024-01-03 08:00",
            },
        ],
        preds=[
            {"pred_id": "1", "succ_id": "2", "type": "PR_SS"},
            {"pred_id": "1", "succ_id": "2", "type": "PR_FF"},
        ],
    )
    results = {r.key: r for r in inspect_schedule(s)}
    assert not results["out_of_sequence"].findings


def test_empty_population_missing_dates_and_disabled_not_pass(tmp_path):
    empty = schedule(tmp_path / "empty.xer", data_date="", activities=[])
    assert all(r.passed is None for r in inspect_schedule(empty))
    s = schedule(
        tmp_path / "a.xer", data_date="broken", activities=[{"task_code": "A"}]
    )
    results = {
        r.key: r
        for r in inspect_schedule(
            s, replace(QualityProfile(), disabled=("high_duration",))
        )
    }
    assert results["invalid_dates"].passed is None
    assert results["high_duration"].passed is None
    assert "Disabled" in results["high_duration"].note


def test_profile_roundtrip_validation(tmp_path):
    p = replace(
        QualityProfile(),
        name="Owner standard",
        high_float_days=20,
        limits={"open_ends": 2.5},
    )
    path = tmp_path / "profile.json"
    save_profile(p, path)
    assert load_profile(path) == p
    path.write_text('{"name":"Bad","high_float_days":NaN}')
    with pytest.raises(ValueError):
        load_profile(path)
    path.write_text('{"disabled":["not_a_check"]}')
    with pytest.raises(ValueError):
        load_profile(path)


def test_quality_reports_and_milestone_slips(tmp_path):
    left = schedule(
        tmp_path / "l.xer",
        activities=[
            {
                "task_code": "M",
                "task_type": "TT_FinMile",
                "dur_hr": 0,
                "ef": "2024-02-01 12:00",
            }
        ],
    )
    right = schedule(
        tmp_path / "r.xer",
        activities=[
            {
                "task_code": "M",
                "task_type": "TT_FinMile",
                "dur_hr": 0,
                "ef": "2024-02-03 00:00",
            }
        ],
    )
    c = compare_schedules(left, right)
    wb = load_workbook(write_excel(c, tmp_path / "r.xlsx"))
    for name in [
        "Quality Checks",
        "Quality Findings",
        "Open Ends",
        "Constraint Register",
        "Milestone Slips",
        "Out of Sequence",
        "Date Review",
        "Check Settings",
    ]:
        assert_grid(wb[name])
    row = records(wb["Milestone Slips"])[0]
    assert row["Activity ID"] == "M" and row["Movement (elapsed days)"] == 1.5
    assert "calendar" not in row["Date basis"].lower()
