from tests.test_reports import schedule
from xercompare.compare.engine import compare_schedules
from xercompare.reports import pdf


def test_pdf_ranks_slips_and_includes_logic_and_quality(tmp_path, monkeypatch):
    left = schedule(
        tmp_path / "l.xer",
        activities=[
            {"task_code": "A", "ef": "2024-03-01 08:00"},
            {"task_code": "Z", "ef": "2024-03-01 08:00"},
        ],
    )
    right = schedule(
        tmp_path / "r.xer",
        activities=[
            {"task_code": "A", "ef": "2024-03-02 08:00"},
            {"task_code": "Z", "ef": "2024-03-10 08:00"},
        ],
        preds=[{"pred_id": "1", "succ_id": "2"}],
    )
    tables = []
    original = pdf.Table

    def capture(rows, *args, **kwargs):
        tables.append(rows)
        return original(rows, *args, **kwargs)

    monkeypatch.setattr(pdf, "Table", capture)
    path = pdf.write_pdf(compare_schedules(left, right), tmp_path / "report.pdf")
    slips = next(rows for rows in tables if rows[0][0] == "Activity ID")
    assert slips[1][0] == "Z" and slips[2][0] == "A"
    assert slips[1][-1] == "9.0"
    logic = next(rows for rows in tables if rows[0][0] == "Predecessor")
    assert logic[1][:3] == ["A", "Z", "FS"]
    assert path.read_bytes().startswith(b"%PDF-")
