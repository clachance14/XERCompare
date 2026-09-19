"""Windowed entry point and an opt-in frozen-application verification journey."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import messagebox

from xercompare.gui.app import XERCompareApp


def main(argv=None):
    parser = argparse.ArgumentParser(description="XERCompare desktop")
    parser.add_argument("left", nargs="?")
    parser.add_argument("right", nargs="?")
    parser.add_argument("-o", "--out")
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.self_test and not all((args.left, args.right, args.out)):
        parser.error("Verification needs two XERs and an output folder.")
    root = tk.Tk()
    app = XERCompareApp(root)
    for key, value in [
        ("left", args.left),
        ("right", args.right),
        ("output", args.out),
    ]:
        if value:
            app.paths[key].set(str(Path(value).resolve()))
    outcome = {"code": 0}
    if args.self_test:
        _verify(app, Path(args.out).resolve(), outcome)
    root.mainloop()
    return outcome["code"]


def _verify(app, output, outcome):
    """Exercise the actual window, export worker, and report preview without a console."""
    import socket

    def no_network(*args, **kwargs):
        raise RuntimeError("Unexpected network connection during offline verification")

    socket.socket.connect = no_network
    socket.create_connection = no_network
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    stage = {
        "phase": "compare",
        "ready_at": None,
        "combined_rows": 0,
        "quality_rows": 0,
    }

    def capture(name):
        from PIL import ImageGrab

        app.root.update_idletasks()
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
            user32.GetAncestor.restype = wintypes.HWND
            window = user32.GetAncestor(app.root.winfo_id(), 2)
            ImageGrab.grab(window=window).save(output / name)
        else:
            x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
            ImageGrab.grab(
                bbox=(x, y, x + app.root.winfo_width(), y + app.root.winfo_height())
            ).save(output / name)

    def finish(error=None):
        import _tkinter
        import openpyxl
        import reportlab
        import xercompare

        modules = {
            m.__name__: str(m.__file__)
            for m in (_tkinter, openpyxl, reportlab, xercompare)
        }
        frozen = bool(getattr(sys, "frozen", False))
        bundle = str(getattr(sys, "_MEIPASS", ""))
        if frozen and not all(
            Path(path).is_relative_to(Path(bundle)) for path in modules.values()
        ):
            error = "A required module was loaded outside the EXE runtime."
        record = {
            "ok": error is None,
            "error": error,
            "frozen": frozen,
            "executable": sys.executable,
            "bundle": bundle,
            "modules": modules,
            "summary": app.result.summary if app.result else None,
            "reports": len(app.result.reports) if app.result else 0,
            "preview_rows": stage["combined_rows"],
            "quality_rows": stage["quality_rows"],
            "history_pairs": len(app.history_result.pairs) if app.history_result else 0,
            "history_folder": (
                str(app.history_result.folder) if app.history_result else None
            ),
            "profile_verified": True,
            "folder": str(app.result.folder) if app.result else None,
        }
        (output / "standalone-verification.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
        outcome["code"] = 1 if error else 0
        app.close()

    def inspect():
        try:
            if time.monotonic() - started > 300:
                finish("Timed out waiting for the desktop verification")
                return
            if app.last_error:
                finish(app.last_error)
                return
            phase = stage["phase"]
            if phase == "compare" and app.result and not app.busy:
                capture("desktop-comparison.png")
                app.show_page("reports")
                app.report_tree.selection_set("Changes Combined")
                app.load_preview()
                stage["phase"] = "combined"
            elif phase == "combined" and app.preview_status.get().startswith(
                "Showing "
            ):
                stage["combined_rows"] = len(app.preview_tree.get_children())
                capture("desktop-reports.png")
                app.show_page("quality")
                capture("desktop-quality.png")
                # Select a rule with evidence, allowing real exports with no open ends.
                rule = next((r for r in app.result.checks if r.findings), None)
                if rule is None:
                    raise AssertionError(
                        "Verification fixture must contain a quality finding"
                    )
                app.quality_tree.selection_set(rule.key)
                app.show_quality_findings()
                stage["phase"] = "findings"
            elif phase == "findings" and app.preview_status.get().startswith(
                "Showing "
            ):
                stage["quality_rows"] = len(app.preview_tree.get_children())
                assert stage["quality_rows"] > 0
                capture("desktop-findings.png")
                # Verify saved profiles and the actual Settings controls, then restore defaults.
                from xercompare.quality.profile import (
                    load_profile,
                    save_profile,
                    QualityProfile,
                )

                app.show_page("settings")
                app.profile_vars["high_duration_days"].set("12.0")
                assert (
                    app.apply_profile() and app.active_profile.high_duration_days == 12
                )
                save_profile(app.active_profile, output / "verification-profile.json")
                app._set_profile(load_profile(output / "verification-profile.json"))
                assert app.active_profile.high_duration_days == 12
                capture("desktop-settings.png")
                app._set_profile(QualityProfile())
                app.history_folder.set(str(Path(app.paths["left"].get()).parent))
                app.history_baseline.set(app.paths["left"].get())
                app.load_history()
                stage["phase"] = "history_scan"
            elif phase == "history_scan" and not app.busy:
                assert len(app.history_items) >= 2
                app.history_confirmed.set(True)
                app.start_history()
                stage["phase"] = "history"
            elif phase == "history" and app.history_result and not app.busy:
                assert app.history_result.excel.is_file()
                assert len(app.history_result.pairs) >= 2
                capture("desktop-history.png")
                finish()
                return
            if app.preview_status.get().startswith("Cannot preview"):
                finish(app.preview_status.get())
                return
        except Exception as error:
            finish(str(error) or type(error).__name__)
            return
        app.root.after(150, inspect)

    app.root.after(300, app.run_button.invoke)
    app.root.after(450, inspect)


def entrypoint():
    try:
        return main()
    except Exception as error:
        # Windowed builds have no stdout/stderr; startup errors must be visible.
        messagebox.showerror("XERCompare could not start", str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(entrypoint())
