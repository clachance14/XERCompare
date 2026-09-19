import gc
import os
import time
import tkinter as tk
from pathlib import Path

import pytest

from tests.fixtures.make_xer import make_xer
from xercompare.gui.app import XERCompareApp


@pytest.fixture(scope="module")
def tk_session():
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        pytest.skip("Desktop tests require a display")
    root = tk.Tk()
    root.withdraw()
    yield root
    # Finalize the window/variable cycles on this thread while Tcl is alive.
    gc.collect()
    root.destroy()
    gc.collect()


@pytest.fixture
def app(tk_session):
    # Keep one Tcl interpreter alive; isolate each test in its own native window.
    # Finalize earlier Tk objects here, before an export worker can trigger GC.
    gc.collect()
    root = tk.Toplevel(tk_session)
    root.withdraw()
    window = XERCompareApp(root)
    yield window
    window.close()
    assert window.destroyed


def wait_for(app, condition, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.root.update()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError(app.status.get())


def test_choose_files_run_and_preview_from_window(app, tmp_path, monkeypatch):
    from xercompare.gui import app as ui

    left, right = tmp_path / "base.xer", tmp_path / "revised.xer"
    left.write_text(
        make_xer(activities=[{"task_code": "A1", "task_name": "Old"}]),
        encoding="cp1252",
    )
    right.write_text(
        make_xer(
            activities=[{"task_code": "A1", "task_name": "New"}, {"task_code": "A2"}]
        ),
        encoding="cp1252",
    )
    choices = iter([str(left), str(right)])
    monkeypatch.setattr(
        ui.filedialog, "askopenfilename", lambda **kwargs: next(choices)
    )
    monkeypatch.setattr(
        ui.filedialog, "askdirectory", lambda **kwargs: str(tmp_path / "reports")
    )
    app.browse_buttons["left"].invoke()
    app.browse_buttons["right"].invoke()
    app.browse_buttons["output"].invoke()
    app.run_button.invoke()
    assert app.busy
    wait_for(app, lambda: not app.busy)
    assert app.last_error is None
    assert app.result.excel.exists() and app.result.pdf.exists()
    assert app.cards["added"].get() == "1"
    assert app.cards["modified"].get() == "1"
    assert len(app.report_tree.get_children()) == 39
    app.show_page("reports")
    app.report_tree.selection_set("Added Tasks")
    app.report_tree.event_generate("<<TreeviewSelect>>")
    wait_for(app, lambda: bool(app.preview_tree.get_children()))
    assert (
        app.preview_tree.item(app.preview_tree.get_children()[0], "values")[0] == "A2"
    )
    opened = []
    monkeypatch.setattr(ui, "open_local", lambda path: opened.append(Path(path)))
    app.open_excel_button.invoke()
    assert opened == [app.result.excel]


def test_invalid_inputs_stay_in_window_and_allow_retry(app):
    app.run_button.invoke()
    assert not app.busy
    assert app.last_error
    assert "older" in app.status.get().lower()
    assert str(app.run_button["state"]) == "normal"


def test_worker_failure_is_visible_and_controls_recover(app, tmp_path):
    invalid = tmp_path / "bad.xer"
    invalid.write_text("Not an XER", encoding="cp1252")
    app.paths["left"].set(str(invalid))
    app.paths["right"].set(str(invalid))
    app.paths["output"].set(str(tmp_path / "reports"))
    app.run_button.invoke()
    wait_for(app, lambda: not app.busy)
    assert "PROJECT" in app.last_error
    assert str(app.run_button["state"]) == "normal"
    assert app.result is None


def test_cancel_button_stops_after_current_stage(app, tmp_path, monkeypatch):
    from xercompare.gui import app as ui
    from xercompare.gui.service import Cancelled

    def wait_until_cancelled(request, progress, cancel):
        assert cancel.wait(10)
        raise Cancelled()

    monkeypatch.setattr(ui, "run_comparison", wait_until_cancelled)
    path = tmp_path / "test.xer"
    path.write_text(make_xer(), encoding="cp1252")
    for key in ["left", "right"]:
        app.paths[key].set(str(path))
    app.paths["output"].set(str(tmp_path / "reports"))
    app.run_button.invoke()
    app.cancel_button.invoke()
    wait_for(app, lambda: not app.busy)
    assert "Cancelled" in app.status.get()
    assert app.result is None


def test_output_controls_remain_accessible_in_short_window(app):
    app.root.deiconify()
    app.root.geometry("1040x700+40+40")
    app.root.update()
    app.root.event_generate("<MouseWheel>", delta=-1200)
    app.root.update()
    button = app.open_excel_button
    bottom = button.winfo_rooty() + button.winfo_height()
    assert bottom <= app.root.winfo_rooty() + app.root.winfo_height()


def test_report_window_formats_numbers_and_costs(app, tmp_path):
    from tests.test_number_display import decimal_pair

    for key, options in zip(("left", "right"), decimal_pair()):
        path = tmp_path / f"{key}.xer"
        path.write_text(make_xer(**options), encoding="cp1252")
        app.paths[key].set(str(path))
    app.paths["output"].set(str(tmp_path / "reports"))
    app.run_button.invoke()
    wait_for(app, lambda: not app.busy)
    assert app.last_error is None
    app.show_page("reports")
    app.report_tree.selection_set("Added Resource Assignments")
    app.report_tree.event_generate("<<TreeviewSelect>>")
    wait_for(app, lambda: bool(app.preview_tree.get_children()))
    headers = [
        app.preview_tree.heading(col, "text") for col in app.preview_tree["columns"]
    ]
    values = app.preview_tree.item(app.preview_tree.get_children()[0], "values")
    row = dict(zip(headers, values))
    assert row["Revised Target quantity"] == "12.3"
    assert row["Revised Target cost"] == "1200.46"
    assert row["Revised Actual regular cost"] == "0.00"
    assert row["Activity ID"] == "00100"


def test_quality_profile_and_findings_drilldown(app, tmp_path):
    app.profile_vars["high_duration_days"].set("2")
    app.profile_vars["name"].set("Short tasks")
    app.apply_profile()
    assert app.active_profile.high_duration_days == 2
    path = tmp_path / "a.xer"
    path.write_text(
        make_xer(activities=[{"task_code": "LONG", "dur_hr": 40}]), encoding="cp1252"
    )
    for key in ("left", "right"):
        app.paths[key].set(str(path))
    app.paths["output"].set(str(tmp_path / "reports"))
    app.start()
    wait_for(app, lambda: not app.busy)
    assert app.last_error is None
    assert app.result.checks[7].affected == 1
    app.show_page("quality")
    app.quality_tree.selection_set("high_duration")
    app.show_quality_findings()
    wait_for(app, lambda: app.preview_status.get().startswith("Showing "))
    assert app.report_filter == {"Check ID": "high_duration"}
    assert (
        app.preview_tree.item(app.preview_tree.get_children()[0], "values")[0] == "LONG"
    )


def test_history_review_order_and_run_from_window(app, tmp_path):
    folder = tmp_path / "updates"
    folder.mkdir()
    for i in range(2):
        (folder / f"{i}.xer").write_text(
            make_xer(
                data_date=f"2024-0{i+1}-01 00:00",
                activities=[{"task_code": "A", "dur_hr": 40 + i * 8}],
            ),
            encoding="cp1252",
        )
    app.history_folder.set(str(folder))
    app.paths["output"].set(str(tmp_path / "out"))
    app.load_history()
    wait_for(app, lambda: not app.busy)
    assert len(app.history_items) == 2
    app.start_history()
    assert not app.busy and "review" in app.history_note.get().lower()
    app.history_confirmed.set(True)
    app.start_history()
    wait_for(app, lambda: not app.busy, timeout=60)
    assert app.last_error is None
    assert app.history_result.excel.exists()
    assert app.history_trend_tree.get_children()
