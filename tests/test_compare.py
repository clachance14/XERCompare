from pathlib import Path

from xercompare.compare.engine import compare_schedules
from xercompare.model.schedule import build_schedule
from xercompare.parse.xer_parser import parse_xer
from xercompare.reports.excel import write_excel
from xercompare.reports.pdf import write_pdf

from tests.fixtures.make_xer import make_xer


def _sched(path: Path, **kwargs):
    path.write_text(make_xer(**kwargs), encoding="cp1252")
    return build_schedule(parse_xer(path))


def test_added_deleted_modified(tmp_path: Path):
    left = _sched(
        tmp_path / "left.xer",
        activities=[
            {"task_id": "1", "task_code": "A1000", "task_name": "Old name", "dur_hr": 40},
            {"task_id": "2", "task_code": "A2000", "task_name": "Gone", "dur_hr": 16},
        ],
        preds=[{"pred_id": "1", "succ_id": "2"}],
    )
    right = _sched(
        tmp_path / "right.xer",
        data_date="2024-03-01 00:00",
        activities=[
            {
                "task_id": "1",
                "task_code": "A1000",
                "task_name": "New name",
                "dur_hr": 48,
                "act_start": "2024-01-08 08:00",
                "remain_hr": 24,
                "status_code": "TK_Active",
            },
            {"task_id": "3", "task_code": "A3000", "task_name": "Added", "dur_hr": 8},
        ],
        preds=[],
    )
    c = compare_schedules(left, right)
    assert [d.task_code for d in c.added] == ["A3000"]
    assert [d.task_code for d in c.deleted] == ["A2000"]
    assert any(d.task_code == "A1000" for d in c.modified)
    a1000 = next(d for d in c.modified if d.task_code == "A1000")
    fields = {ch.field for ch in a1000.changes}
    assert "task_name" in fields
    assert "orig_dur_days" in fields
    assert "act_start" in fields
    assert a1000.klass == "both"
    assert len(c.logic_deleted) == 1

    xlsx = write_excel(c, tmp_path / "out.xlsx")
    pdf = write_pdf(c, tmp_path / "out.pdf")
    assert xlsx.exists() and xlsx.stat().st_size > 0
    assert pdf.exists() and pdf.stat().st_size > 0
