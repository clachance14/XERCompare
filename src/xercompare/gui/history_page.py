"""Reviewable folder history workflow; exports run on the existing worker queue."""

from pathlib import Path
from threading import Thread, Event
import tkinter as tk
from tkinter import ttk, filedialog
from xercompare.history import discover_history, HistoryRequest, run_history
from xercompare.gui.service import Cancelled


class HistoryPage:
    def _history_page(self, page):
        self.history_items = []
        self.history_result = None
        self.history_folder = tk.StringVar(self.root)
        self.history_baseline = tk.StringVar(self.root)
        self.history_confirmed = tk.BooleanVar(self.root, value=False)
        self.history_note = tk.StringVar(
            self.root,
            value="Choose a folder, load its exports, then review the project and order.",
        )
        ttk.Label(page, text="Update history", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text="Trend a sequence of local exports. Each pair also gets a full Excel workbook and PDF.",
            wraplength=760,
        ).pack(anchor="w", pady=8)
        self.history_controls = []
        for title, var, kind in [
            ("Folder of XERs", self.history_folder, "folder"),
            ("Baseline (optional)", self.history_baseline, "baseline"),
        ]:
            row = ttk.Frame(page)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=title, width=20).pack(side="left")
            entry = ttk.Entry(row, textvariable=var)
            entry.pack(side="left", fill="x", expand=True)
            button = ttk.Button(
                row, text="Browse…", command=lambda k=kind: self._browse_history(k)
            )
            button.pack(side="left", padx=8)
            self.history_controls.extend([entry, button])
        output = ttk.Frame(page)
        output.pack(fill="x", pady=4)
        ttk.Label(output, text="Output folder", width=20).pack(side="left")
        entry = ttk.Entry(output, textvariable=self.paths["output"])
        entry.pack(side="left", fill="x", expand=True)
        button = ttk.Button(
            output, text="Browse…", command=lambda: self.browse("output")
        )
        button.pack(side="left", padx=8)
        self.history_controls.extend([entry, button])
        buttons = ttk.Frame(page)
        buttons.pack(anchor="w", pady=10)
        for label, cmd in [
            ("Load exports", self.load_history),
            ("Move earlier", lambda: self.move_history(-1)),
            ("Move later", lambda: self.move_history(1)),
        ]:
            button = ttk.Button(buttons, text=label, command=cmd)
            button.pack(side="left", padx=(0, 8))
            self.history_controls.append(button)
        columns = ("File", "Project", "Data date", "Activities")
        frame = ttk.Frame(page)
        frame.pack(fill="both", expand=True)
        self.history_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=6, selectmode="browse"
        )
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(
                col, width=250 if col == "File" else 160, stretch=True
            )
        self.history_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, command=self.history_tree.yview)
        scroll.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=scroll.set)
        ttk.Label(page, textvariable=self.history_note, wraplength=760).pack(
            anchor="w", pady=8
        )
        confirm = ttk.Checkbutton(
            page,
            text="I reviewed this order and confirm these exports and the optional baseline belong to the same project.",
            variable=self.history_confirmed,
        )
        confirm.pack(anchor="w", pady=4)
        self.history_controls.append(confirm)
        row = ttk.Frame(page)
        row.pack(anchor="w", pady=8)
        self.history_run_button = ttk.Button(
            row,
            text="Build history reports",
            command=self.start_history,
            style="Primary.TButton",
        )
        self.history_run_button.pack(side="left")
        self.history_controls.append(self.history_run_button)
        self.history_cancel_button = ttk.Button(
            row, text="Cancel", command=self.cancel, state="disabled"
        )
        self.history_cancel_button.pack(side="left", padx=8)
        ttk.Label(page, textvariable=self.status, wraplength=760).pack(
            anchor="w", pady=4
        )
        ttk.Progressbar(page, variable=self.progress, maximum=100).pack(
            fill="x", pady=8
        )
        columns = (
            "Update",
            "Activities",
            "Latest early finish",
            "TF <= 0",
            "DCMA flags",
            "Profile flags",
        )
        self.history_trend_tree = ttk.Treeview(
            page, columns=columns, show="headings", height=5
        )
        for col in columns:
            self.history_trend_tree.heading(col, text=col)
            self.history_trend_tree.column(col, width=140, stretch=True)
        self.history_trend_tree.pack(fill="both", expand=True, pady=8)
        row = ttk.Frame(page)
        row.pack(anchor="w", pady=8)
        self.history_open_buttons = []
        for label, kind in [
            ("Open trends and charts", "excel"),
            ("Open history PDF", "pdf"),
            ("Open history folder", "folder"),
        ]:
            button = ttk.Button(
                row,
                text=label,
                command=lambda k=kind: self.open_history(k),
                state="disabled",
            )
            button.pack(side="left", padx=(0, 8))
            self.history_open_buttons.append(button)
        self.history_folder.trace_add("write", lambda *args: self._invalidate_history())
        self.history_baseline.trace_add(
            "write", lambda *args: self.history_confirmed.set(False)
        )

    def _invalidate_history(self):
        self.history_items = []
        self.history_confirmed.set(False)
        self.history_tree.delete(*self.history_tree.get_children())
        self.history_note.set(
            "Folder changed. Load exports and review the order again."
        )

    def _browse_history(self, kind):
        if self.busy:
            return
        path = (
            filedialog.askdirectory(parent=self.root, title="Folder of XER updates")
            if kind == "folder"
            else filedialog.askopenfilename(
                parent=self.root,
                title="Choose the explicit baseline",
                filetypes=[("P6 XER", "*.xer *.XER")],
            )
        )
        if path:
            (self.history_folder if kind == "folder" else self.history_baseline).set(
                path
            )

    def _set_history_busy(self, busy):
        for widget in self.history_controls:
            widget.configure(state="disabled" if busy else "normal")
        self.history_cancel_button.configure(state="normal" if busy else "disabled")
        for widget in self.history_open_buttons:
            widget.configure(
                state="normal" if self.history_result and not busy else "disabled"
            )

    def load_history(self):
        if self.busy:
            return
        folder = self.history_folder.get().strip()
        self.last_error = None
        self.show_page("history")
        self._set_busy(True)
        self.status.set("Reading the folder’s XER exports…")
        self.progress.set(0)
        self.cancel_event = Event()

        def worker():
            try:
                items = discover_history(folder)
                if self.cancel_event.is_set():
                    raise Cancelled()
                self.events.put(("history_loaded", items))
            except Cancelled:
                self.events.put(("cancelled", None))
            except Exception as error:
                self.events.put(("error", str(error)))

        Thread(target=worker, name="xercompare-history-scan", daemon=True).start()

    def _history_loaded(self, items):
        self.history_items = items
        self.history_confirmed.set(False)
        self._set_busy(False)
        self._fill_history_order()
        self.status.set(
            "Review the project names and update order before building history."
        )
        same = len({s.data_date for s in items}) < len(items)
        self.history_note.set(
            f"{len(items)} exports. Sorted by data date, then filename. "
            + (
                "Some dates match; filenames do not establish chronology. Adjust the order if needed."
                if same
                else "Use Move earlier/later to change the order."
            )
        )

    def _fill_history_order(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for i, s in enumerate(self.history_items):
            self.history_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(s.path.name, s.project, s.data_date, s.activity_count),
            )

    def move_history(self, direction):
        if self.busy:
            return
        selection = self.history_tree.selection()
        if not selection:
            return
        old = int(selection[0])
        new = old + direction
        if 0 <= new < len(self.history_items):
            self.history_items[old], self.history_items[new] = (
                self.history_items[new],
                self.history_items[old],
            )
            self.history_confirmed.set(False)
            self._fill_history_order()
            self.history_tree.selection_set(str(new))

    def start_history(self):
        if self.busy:
            return
        if not self.history_confirmed.get():
            self.history_note.set(
                "Review the order and confirm the project before building history."
            )
            return
        try:
            output = self.paths["output"].get().strip()
            if not output:
                raise ValueError("Choose an output folder.")
            baseline = self.history_baseline.get().strip()
            request = HistoryRequest(
                tuple(s.path for s in self.history_items),
                Path(output),
                Path(baseline) if baseline else None,
                self.active_profile,
                True,
            )
            request.validate()
        except (ValueError, OSError) as error:
            self.history_note.set(str(error))
            return
        self.last_error = None
        self.show_page("history")
        self.cancel_event = Event()
        self.progress.set(0)
        self._set_busy(True)

        def worker():
            try:
                result = run_history(
                    request,
                    lambda value, text: self.events.put(("progress", (value, text))),
                    self.cancel_event,
                )
                self.events.put(("history_complete", result))
            except Cancelled:
                self.events.put(("cancelled", None))
            except Exception as error:
                self.events.put(("error", str(error)))

        Thread(target=worker, name="xercompare-history", daemon=True).start()

    def _history_complete(self, result):
        self.history_result = result
        self._set_busy(False)
        self.progress.set(100)
        self.history_trend_tree.delete(*self.history_trend_tree.get_children())
        for r in result.trends:
            self.history_trend_tree.insert(
                "", "end", values=(r[0], r[3], r[4], r[5], r[6], r[8])
            )
        self.history_note.set(
            f"{len(result.pairs)} complete comparison sets. "
            + (
                " ".join(result.warnings[:2])
                if result.warnings
                else "No history warnings."
            )
        )
        self.status.set(
            "History complete. Open trends and charts or the history folder below."
        )

    def open_history(self, kind):
        if self.history_result:
            from xercompare.gui.app import open_local

            try:
                open_local(getattr(self.history_result, kind))
            except OSError as error:
                self.history_note.set(str(error))
