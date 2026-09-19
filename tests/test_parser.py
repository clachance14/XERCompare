from pathlib import Path

from xercompare.model.schedule import build_schedule
from xercompare.parse.xer_parser import parse_xer

from tests.fixtures.make_xer import make_xer


def test_parse_minimal(tmp_path: Path):
    p = tmp_path / "a.xer"
    p.write_text(
        make_xer(
            activities=[
                {
                    "task_id": "1",
                    "task_code": "A1000",
                    "task_name": "Start",
                    "dur_hr": 0,
                    "task_type": "TT_Mile",
                },
                {
                    "task_id": "2",
                    "task_code": "A2000",
                    "task_name": "Work",
                    "dur_hr": 80,
                },
            ],
            preds=[{"pred_id": "1", "succ_id": "2"}],
        ),
        encoding="cp1252",
    )
    xer = parse_xer(p)
    assert "TASK" in xer.tables
    assert len(xer.table("TASK")) == 2
    sched = build_schedule(xer)
    assert sched.activity_count == 2
    assert "A2000" in sched.activities
    assert sched.activities["A2000"].orig_dur_days == 10
    assert len(sched.relationships) == 1
    assert sched.relationships[0].type_label == "FS"


def test_named_columns_quoted_cp1252_and_project_scope(tmp_path):
    p = tmp_path / "reordered.xer"
    task = {
        "task_name": 'Café\t"pipe"\nnext line',
        "task_code": "A1",
        "clndr_id": "2",
        "target_drtn_hr_cnt": 50,
        "task_id": "20",
        "proj_id": "1",
        "wbs_id": "10",
    }
    p.write_text(
        make_xer(
            activities=[task, {"task_id": "30", "proj_id": "2", "task_code": "OTHER"}],
            calendars=[{"day_hr_cnt": 10, "clndr_name": "Ten hours", "clndr_id": "2"}],
            preds=[
                {"pred_id": "20", "succ_id": "20", "proj_id": "1"},
                {"pred_id": "30", "succ_id": "30", "proj_id": "2", "pred_proj_id": "2"},
            ],
            tables={
                "PROJECT": [
                    {"proj_id": "1", "proj_short_name": "FIRST"},
                    {"proj_id": "2", "proj_short_name": "SECOND"},
                ],
                "TASK": [task, {"task_id": "30", "proj_id": "2", "task_code": "OTHER"}],
                "UNKNOWN": [{"memo": "Keep this table"}],
            },
        ),
        encoding="cp1252",
    )
    raw = parse_xer(p)
    schedule = build_schedule(raw)
    assert raw.table("UNKNOWN") == [{"memo": "Keep this table"}]
    assert schedule.activities["A1"].task_name == task["task_name"]
    assert schedule.activities["A1"].orig_dur_days == 5
    assert set(schedule.activities) == {"A1"}
    assert len(schedule.relationships) == 1
    assert any("2 projects" in warning for warning in schedule.warnings)


def test_quoted_text_is_stable_across_line_endings(tmp_path):
    text = make_xer(activities=[{"task_code": "A1", "task_name": "Line one\nLine two"}])
    lf, crlf = tmp_path / "lf.xer", tmp_path / "crlf.xer"
    lf.write_bytes(text.encode("cp1252"))
    crlf.write_bytes(text.replace("\n", "\r\n").encode("cp1252"))
    before = build_schedule(parse_xer(lf))
    after = build_schedule(parse_xer(crlf))
    assert (
        before.activities["A1"].task_name
        == after.activities["A1"].task_name
        == "Line one\nLine two"
    )
