"""Native desktop front end. All Tk calls stay on the main thread."""

from __future__ import annotations

import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
from threading import Event, Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from xercompare import __version__
from xercompare.gui.service import (
    Cancelled,
    CompareRequest,
    RunResult,
    read_preview,
    run_comparison,
)

NAVY = "#16324F"
BLUE = "#2563A6"
BG = "#F3F6FA"
INK = "#172B42"
MUTED = "#526579"
GREEN = "#147D54"
RED = "#B83A42"
GOLD = "#A36B00"


def open_local(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"This output has been moved or deleted: {path}")
    if os.name == "nt":
        os.startfile(str(path))
    else:
        subprocess.Popen(
            ["open" if sys.platform == "darwin" else "xdg-open", str(path)]
        )


from xercompare.gui.advanced import AdvancedPages
from xercompare.quality.profile import QualityProfile


class XERCompareApp(AdvancedPages):
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"XERCompare {__version__}")
        width = min(1280, self.root.winfo_screenwidth() - 60)
        height = min(860, self.root.winfo_screenheight() - 100)
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2 - 25)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1040, 620)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.report_callback_exception = self._callback_error
        self.active_profile = QualityProfile()
        self.report_filter = {}
        self.report_query = tk.StringVar(root)
        self.report_filter_label = tk.StringVar(root, value="All report rows")
        self.busy = False
        self.closing = False
        self.destroyed = False
        self.result: RunResult | None = None
        self.last_error: str | None = None
        self.events = Queue()
        self.cancel_event = Event()
        self.preview_token = 0
        self.paths = {key: tk.StringVar(root) for key in ("left", "right", "output")}
        self.paths["output"].set(str(Path.home() / "Documents" / "XERCompare reports"))
        self.status = tk.StringVar(
            root, "Choose the older file, revised file, and output folder to begin."
        )
        self.progress = tk.DoubleVar(root, 0)
        self.context = tk.StringVar(
            root, "Activity IDs match across snapshots, even when internal IDs change."
        )
        self.quality_text = tk.StringVar(
            root, "Stored-value quality checks appear after comparison."
        )
        self.preview_status = tk.StringVar(
            root, "Run a comparison to browse the report catalog."
        )
        self.cards = {
            key: tk.StringVar(root, "\u2014")
            for key in ("added", "deleted", "modified", "logic", "resources", "udfs")
        }
        self.entries = []
        self.browse_buttons = {}
        self.output_buttons = []
        self.pages = {}
        self.scroll_canvases = {}
        self.nav_buttons = {}
        self._styles()
        self._layout()
        self.show_page("compare")
        self.poll_id = self.root.after(80, self._poll)
        self.root.bind("<Control-Return>", lambda event: self.start())
        self.root.bind("<MouseWheel>", self._scroll_wheel)

    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=BG, foreground=INK)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("TLabelframe", background=BG, bordercolor="#D8E1EB")
        style.configure(
            "TLabelframe.Label", font=("Segoe UI", 11, "bold"), foreground=INK
        )
        style.configure("TButton", padding=(12, 8), background="#E4EBF3", borderwidth=0)
        style.map(
            "TButton",
            background=[("active", "#D4E2F1")],
            foreground=[("disabled", "#8391A1")],
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 11, "bold"),
            background=BLUE,
            foreground="white",
            padding=(20, 10),
        )
        style.map(
            "Primary.TButton",
            background=[("disabled", "#9BAEC3"), ("active", "#194C80")],
            foreground=[("disabled", "white")],
        )
        style.configure("TEntry", padding=7, fieldbackground="white", foreground=INK)
        style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            rowheight=27,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#E5EDF5",
            foreground=INK,
            font=("Segoe UI", 10, "bold"),
            padding=(8, 7),
        )
        style.map(
            "Treeview",
            background=[("selected", BLUE)],
            foreground=[("selected", "white")],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=BLUE,
            troughcolor="#E1E8F0",
            borderwidth=0,
        )
        self.icon = tk.PhotoImage(width=32, height=32)
        self.icon.put(NAVY, to=(0, 0, 32, 32))
        for x1, y1, x2, y2, color in [
            (6, 7, 21, 11, "#FFFFFF"),
            (11, 14, 26, 18, "#71C9B4"),
            (6, 21, 21, 25, "#FFFFFF"),
        ]:
            self.icon.put(color, to=(x1, y1, x2, y2))
        self.root.iconphoto(True, self.icon)

    def _layout(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        rail = tk.Frame(self.root, bg=NAVY, width=190)
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_propagate(False)
        tk.Label(
            rail, text="XERCOMPARE", bg=NAVY, fg="white", font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", padx=20, pady=(30, 3))
        tk.Label(
            rail,
            text="Schedule comparison",
            bg=NAVY,
            fg="#B4C9DC",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=20, pady=(0, 35))
        for key, title in [
            ("compare", "Compare schedules"),
            ("reports", "Report catalog"),
            ("quality", "Quality findings"),
            ("settings", "Quality settings"),
            ("history", "Update history"),
            ("about", "About XERCompare"),
        ]:
            button = tk.Button(
                rail,
                text=title,
                anchor="w",
                command=lambda key=key: self.show_page(key),
                bg=NAVY,
                fg="white",
                activebackground="#264B70",
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=14,
                font=("Segoe UI", 10),
                cursor="hand2",
            )
            button.pack(fill="x", pady=2)
            self.nav_buttons[key] = button
        tk.Label(
            rail,
            text=f"LOCAL FILES ONLY\n\nOffline  ·  MIT\nVersion {__version__}",
            justify="left",
            bg=NAVY,
            fg="#B4C9DC",
            font=("Segoe UI", 9),
        ).pack(side="bottom", anchor="w", padx=20, pady=25)
        main = ttk.Frame(self.root, padding=(26, 22))
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        for key in ("compare", "reports", "quality", "settings", "history", "about"):
            page = ttk.Frame(main)
            page.grid(row=0, column=0, sticky="nsew")
            page.columnconfigure(0, weight=1)
            self.pages[key] = page
        self._compare_page(self._scroll_page(self.pages["compare"], "compare"))
        self._reports_page(self.pages["reports"])
        self._quality_page(self.pages["quality"])
        self._history_page(self._scroll_page(self.pages["history"], "history"))
        self._settings_page(self._scroll_page(self.pages["settings"], "settings"))
        self._about_page(self._scroll_page(self.pages["about"], "about"))

    def _scroll_page(self, container, key):
        container.rowconfigure(0, weight=1)
        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        inner = ttk.Frame(canvas, padding=(0, 0, 8, 0))
        inner.columnconfigure(0, weight=1)
        item = canvas.create_window((0, 0), window=inner, anchor="nw")

        def resize(event):
            canvas.itemconfigure(
                item,
                width=event.width,
                height=max(event.height, inner.winfo_reqheight()),
            )
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize)
        inner.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        self.scroll_canvases[key] = canvas
        return inner

    def _scroll_wheel(self, event):
        canvas = self.scroll_canvases.get(self.current_page)
        if canvas and canvas.bbox("all")[3] > canvas.winfo_height():
            canvas.yview_scroll(-int(event.delta / 120), "units")

    def _compare_page(self, page):
        ttk.Label(page, text="Compare your schedules", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            page,
            text="Two P6 exports. A clear record of what changed.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(5, 18))
        files = ttk.LabelFrame(page, text="Schedule files", padding=(16, 10))
        files.grid(row=2, column=0, sticky="ew")
        files.columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(
            [
                ("left", "Older / baseline XER"),
                ("right", "Revised / update XER"),
                ("output", "Output folder"),
            ]
        ):
            ttk.Label(files, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=6
            )
            entry = ttk.Entry(files, textvariable=self.paths[key])
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            self.entries.append(entry)
            button = ttk.Button(
                files, text="Browse...", command=lambda key=key: self.browse(key)
            )
            button.grid(row=row, column=2, padx=(10, 0), pady=6)
            self.browse_buttons[key] = button
        ttk.Label(
            files,
            text="Each run creates a dated folder with Excel and PDF reports. Earlier reports are kept.",
            style="Muted.TLabel",
            wraplength=620,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 3))
        actions = ttk.Frame(page)
        actions.grid(row=3, column=0, sticky="ew", pady=(14, 18))
        self.run_button = ttk.Button(
            actions,
            text="Compare schedules",
            style="Primary.TButton",
            command=self.start,
        )
        self.run_button.pack(side="left")
        self.cancel_button = ttk.Button(
            actions, text="Cancel", command=self.cancel, state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10)
        ttk.Label(actions, text="Excel + PDF included", style="Muted.TLabel").pack(
            side="right"
        )
        ttk.Label(page, text="Change overview", style="Heading.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 8)
        )
        cards = ttk.Frame(page)
        cards.grid(row=5, column=0, sticky="ew")
        for col in range(3):
            cards.columnconfigure(col, weight=1, uniform="cards")
        for index, (key, label, detail, color) in enumerate(
            [
                ("added", "Added activities", "New in the revised file", GREEN),
                ("deleted", "Deleted activities", "Removed since the older file", RED),
                (
                    "modified",
                    "Modified activities",
                    "Stored activity fields changed",
                    GOLD,
                ),
                ("logic", "Relationship edits", "Added, deleted, or changed lag", BLUE),
                (
                    "resources",
                    "Assignment edits",
                    "Resource assignments added / deleted",
                    BLUE,
                ),
                (
                    "udfs",
                    "UDF edits",
                    "Activity values added / deleted / revised",
                    BLUE,
                ),
            ]
        ):
            card = tk.Frame(
                cards, bg="white", highlightbackground="#DCE5EE", highlightthickness=1
            )
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="nsew",
                padx=(0 if index % 3 == 0 else 8, 0),
                pady=(0, 8),
            )
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            tk.Label(
                card, text=label, bg="white", fg=MUTED, font=("Segoe UI", 10)
            ).pack(anchor="w", padx=12, pady=(7, 0))
            tk.Label(
                card,
                textvariable=self.cards[key],
                bg="white",
                fg=color,
                font=("Segoe UI", 26, "bold"),
            ).pack(anchor="w", padx=12)
        ttk.Label(
            page, textvariable=self.context, style="Muted.TLabel", wraplength=650
        ).grid(row=6, column=0, sticky="w", pady=(0, 6))
        self.quality_label = ttk.Label(
            page, textvariable=self.quality_text, wraplength=650
        )
        self.quality_label.grid(row=7, column=0, sticky="w", pady=(0, 12))
        ttk.Progressbar(page, variable=self.progress, maximum=100).grid(
            row=8, column=0, sticky="ew", pady=(0, 8)
        )
        self.status_label = ttk.Label(page, textvariable=self.status, wraplength=650)
        self.status_label.grid(row=9, column=0, sticky="w")
        result_actions = ttk.Frame(page)
        result_actions.grid(row=10, column=0, sticky="ew", pady=(14, 0))
        self.open_excel_button = self._output_button(
            result_actions, "Open Excel", lambda: self.open_result("excel")
        )
        self._output_button(result_actions, "Open PDF", lambda: self.open_result("pdf"))
        self._output_button(
            result_actions, "Open folder", lambda: self.open_result("folder")
        )
        self._output_button(result_actions, "Warnings", self.show_warnings)
        page.rowconfigure(11, weight=1)
        ttk.Label(
            page,
            text="Stored-field comparison. No CPM recalculation or file uploads.",
            style="Muted.TLabel",
        ).grid(row=12, column=0, sticky="w", pady=(10, 0))

    def _output_button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=command, state="disabled")
        button.pack(side="left", padx=(0, 8))
        self.output_buttons.append(button)
        return button

    def _reports_page(self, page):
        ttk.Label(page, text="Report catalog", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            page,
            text="Select a report to preview its rows. The workbook contains the complete data.",
            style="Muted.TLabel",
            wraplength=650,
        ).grid(row=1, column=0, sticky="w", pady=(7, 18))
        pane = ttk.Panedwindow(page, orient="horizontal")
        pane.grid(row=2, column=0, sticky="nsew")
        page.rowconfigure(2, weight=1)
        catalog = ttk.Frame(pane, width=285)
        catalog.rowconfigure(0, weight=1)
        catalog.columnconfigure(0, weight=1)
        self.report_tree = ttk.Treeview(
            catalog, columns=("name", "rows"), show="headings", selectmode="browse"
        )
        self.report_tree.heading("name", text="Report")
        self.report_tree.heading("rows", text="Rows")
        self.report_tree.column("name", width=230, minwidth=170)
        self.report_tree.column(
            "rows", width=55, minwidth=45, anchor="e", stretch=False
        )
        self.report_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            catalog, orient="vertical", command=self.report_tree.yview
        )
        scroll.grid(row=0, column=1, sticky="ns")
        self.report_tree.configure(yscrollcommand=scroll.set)
        self.report_tree.bind("<<TreeviewSelect>>", self.load_preview)
        self.report_tree.bind("<Double-1>", lambda event: self.open_result("excel"))
        pane.add(catalog, weight=0)
        preview = ttk.Frame(pane, padding=(12, 0, 0, 0))
        preview.rowconfigure(0, weight=1)
        preview.columnconfigure(0, weight=1)
        self.preview_tree = ttk.Treeview(preview, show="headings")
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(
            preview, orient="vertical", command=self.preview_tree.yview
        )
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(
            preview, orient="horizontal", command=self.preview_tree.xview
        )
        horizontal.grid(row=1, column=0, sticky="ew")
        self.preview_tree.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set
        )
        pane.add(preview, weight=1)
        ttk.Label(
            page, textvariable=self.preview_status, style="Muted.TLabel", wraplength=650
        ).grid(row=3, column=0, sticky="w", pady=12)
        search = ttk.Frame(page)
        search.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(search, text="Search report:").pack(side="left")
        entry = ttk.Entry(search, textvariable=self.report_query, width=24)
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", self.load_preview)
        ttk.Button(search, text="Search", command=self.load_preview).pack(side="left")
        ttk.Button(search, text="Clear", command=self.clear_report_filter).pack(
            side="left", padx=8
        )
        ttk.Label(search, textvariable=self.report_filter_label).pack(side="left")
        buttons = ttk.Frame(page)
        buttons.grid(row=5, column=0, sticky="w")
        self._output_button(
            buttons, "Open full workbook", lambda: self.open_result("excel")
        )
        self._output_button(
            buttons, "Open PDF summary", lambda: self.open_result("pdf")
        )

    def _about_page(self, page):
        ttk.Label(page, text="XERCompare", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            page,
            text=f"Version {__version__}  ·  Offline schedule comparison",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(8, 24))
        sections = [
            (
                "Your files stay here",
                "XERCompare reads two local Primavera P6 .xer files and writes Excel and PDF reports to your chosen output folder. It has no uploads, telemetry, sign-in, or connection to P6.",
            ),
            (
                "Stored values, clearly labeled",
                "Activity IDs match the two schedules. Progress, revision, and date changes are kept distinct. Driving-path membership uses stored total float <= 0 and is only an approximation; no critical path is recalculated.",
            ),
            (
                "A complete report catalog",
                "Review all workbook sheets in the Report catalog, with previews of up to 200 rows. Excel keeps every exported row. Quality checks that cannot be evaluated show N/A with a reason.",
            ),
            (
                "No Python or P6 installation needed",
                "The Windows EXE includes its runtime. Double-click it, choose the two XERs, and compare. Reports open in your installed spreadsheet or PDF viewer; previews are available here.",
            ),
        ]
        for index, (title, text) in enumerate(sections):
            ttk.Label(page, text=title, style="Heading.TLabel").grid(
                row=2 + index * 2, column=0, sticky="w", pady=(0, 7)
            )
            ttk.Label(page, text=text, wraplength=650, justify="left").grid(
                row=3 + index * 2, column=0, sticky="w", pady=(0, 24)
            )
        ttk.Button(
            page, text="License and third-party notices", command=self.show_licenses
        ).grid(row=10, column=0, sticky="w")

    def show_page(self, key):
        self.current_page = key
        for name, page in self.pages.items():
            if name == key:
                page.grid()
            else:
                page.grid_remove()
            self.nav_buttons[name].configure(bg="#264B70" if name == key else NAVY)

    def browse(self, key):
        if self.busy:
            return
        if key == "output":
            chosen = filedialog.askdirectory(
                parent=self.root, title="Choose an output folder", mustexist=False
            )
        else:
            chosen = filedialog.askopenfilename(
                parent=self.root,
                title=(
                    "Choose the older XER"
                    if key == "left"
                    else "Choose the revised XER"
                ),
                filetypes=[
                    ("Primavera P6 export", "*.xer *.XER"),
                    ("All files", "*.*"),
                ],
            )
        if chosen:
            self.paths[key].set(chosen)

    def _set_busy(self, busy):
        self.busy = busy
        self._set_history_busy(busy)
        for widget in [*self.entries, *self.browse_buttons.values(), self.run_button]:
            widget.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")
        for button in self.output_buttons:
            button.configure(state="normal" if self.result and not busy else "disabled")

    def start(self):
        if self.busy:
            return
        self.last_error = None
        try:
            values = {}
            for key, label in [
                ("left", "older XER"),
                ("right", "revised XER"),
                ("output", "output folder"),
            ]:
                text = self.paths[key].get().strip().strip('"')
                if not text:
                    raise ValueError(f"Choose the {label} before comparing.")
                values[key] = Path(text).expanduser().resolve()
            request = CompareRequest(
                values["left"], values["right"], values["output"], self.active_profile
            )
            request.validate()
        except (ValueError, OSError) as error:
            self._show_error(str(error))
            return
        self.show_page("compare")
        self.preview_token += 1
        self.cancel_event = Event()
        self.progress.set(0)
        self.status_label.configure(foreground=INK)
        self.status.set("Starting comparison...")
        self._set_busy(True)

        def worker():
            try:
                result = run_comparison(
                    request,
                    lambda value, text: self.events.put(("progress", (value, text))),
                    self.cancel_event,
                )
                self.events.put(("complete", result))
            except Cancelled:
                self.events.put(("cancelled", None))
            except Exception as error:
                self.events.put(("error", str(error) or type(error).__name__))

        Thread(target=worker, name="xercompare-export", daemon=True).start()

    def cancel(self):
        if self.busy:
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self.status.set(
                "Stopping after the current step. Unfinished reports will be removed."
            )

    def _poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "progress":
                    self.progress.set(data[0])
                    if not self.cancel_event.is_set():
                        self.status.set(data[1])
                elif kind == "history_loaded":
                    self._history_loaded(data)
                elif kind == "history_complete":
                    self._history_complete(data)
                elif kind == "complete":
                    self._complete(data)
                elif kind == "cancelled":
                    self._set_busy(False)
                    self.progress.set(0)
                    self.status.set("Cancelled. No unfinished report set was saved.")
                elif kind == "error":
                    self._set_busy(False)
                    self.progress.set(0)
                    self._show_error(data)
                elif kind == "preview":
                    token, preview = data
                    if token == self.preview_token:
                        self._show_preview(preview)
                elif kind == "preview_error":
                    token, message = data
                    if token == self.preview_token:
                        self.preview_status.set(
                            f"Cannot preview this report: {message}"
                        )
        except Empty:
            pass
        if self.closing and not self.busy:
            self.close()
        if not self.destroyed:
            self.poll_id = self.root.after(80, self._poll)

    def _complete(self, result):
        self.result = result
        self._fill_quality(result)
        self._set_busy(False)
        self.last_error = None
        self.progress.set(100)
        summary = result.summary
        values = {key: summary[key] for key in ("added", "deleted", "modified")}
        values.update(
            logic=sum(
                summary[key]
                for key in ("logic_added", "logic_deleted", "logic_modified")
            ),
            resources=result.resource_added
            + result.resource_deleted
            + result.resource_modified,
            udfs=result.udf_added + result.udf_deleted + result.udf_modified,
        )
        for key, value in values.items():
            self.cards[key].set(f"{value:,}")
        self.context.set(
            f"{summary['left_activities']:,} older activities  |  {summary['right_activities']:,} revised activities  |  {summary['unchanged']:,} unchanged\nData dates: {result.left_date or 'not stored'}  →  {result.right_date or 'not stored'}"
        )
        passed = sum(metric.passed is True for metric in result.quality)
        failed = sum(metric.passed is False for metric in result.quality)
        unavailable = sum(metric.passed is None for metric in result.quality)
        self.quality_text.set(
            f"Revised quality checks: {passed} pass  ·  {failed} flagged  ·  {unavailable} N/A  |  {len(result.warnings)} warnings"
        )
        self.quality_label.configure(foreground=RED if failed else INK)
        self.status_label.configure(foreground=GREEN)
        self.status.set(
            "Comparison complete. Excel and PDF are ready in the new output folder."
        )
        self.report_tree.delete(*self.report_tree.get_children())
        self.preview_tree.delete(*self.preview_tree.get_children())
        for report in result.reports:
            self.report_tree.insert(
                "",
                "end",
                iid=report.name,
                values=(
                    report.name,
                    "—" if report.rows is None else f"{report.rows:,}",
                ),
            )
        self.preview_status.set(
            "Select a report. Previews show up to 200 rows; the workbook contains every row."
        )

    def load_preview(self, event=None):
        selected = self.report_tree.selection()
        if not selected or not self.result or self.busy:
            return
        self.report_tree.see(selected[0])
        self.preview_token += 1
        token, path, sheet = self.preview_token, self.result.excel, selected[0]
        if sheet != "Quality Findings":
            self.report_filter = {}
            self.report_filter_label.set("All report rows")
        filters, query = dict(self.report_filter), self.report_query.get().strip()
        self.preview_status.set(f"Loading {sheet}...")
        self.preview_tree.delete(*self.preview_tree.get_children())

        def worker():
            try:
                self.events.put(
                    (
                        "preview",
                        (
                            token,
                            read_preview(path, sheet, filters=filters, query=query),
                        ),
                    )
                )
            except Exception as error:
                self.events.put(("preview_error", (token, str(error))))

        Thread(target=worker, name="xercompare-preview", daemon=True).start()

    def _show_preview(self, preview):
        columns = [str(i) for i in range(len(preview.headers))]
        self.preview_tree.configure(columns=columns)
        for col, title in zip(columns, preview.headers):
            self.preview_tree.heading(col, text=title)
            self.preview_tree.column(
                col,
                width=(
                    220
                    if title in ("Warning", "Meaning")
                    else (
                        180
                        if title == "Name"
                        else 110 if title in ("Activity ID", "WBS") else 150
                    )
                ),
                minwidth=80,
                stretch=False,
            )
        for row in preview.rows:
            self.preview_tree.insert(
                "", "end", values=["" if value is None else str(value) for value in row]
            )
        self.preview_status.set(
            f"Showing {len(preview.rows):,} of {preview.total:,} rows. Open Excel for all rows and revised-cell highlighting."
        )

    def _show_error(self, message):
        self.last_error = message
        self.status_label.configure(foreground=RED)
        self.status.set(f"Unable to run: {message}")

    def open_result(self, kind):
        if self.result:
            try:
                open_local(getattr(self.result, kind))
            except OSError as error:
                messagebox.showerror(
                    "Cannot open the report",
                    f"{error}\n\nUse Open folder to find the saved reports.",
                    parent=self.root,
                )

    def _text_window(self, title, text):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("820x520")
        window.transient(self.root)
        area = tk.Text(
            window,
            wrap="word",
            font=("Segoe UI", 10),
            padx=18,
            pady=18,
            background="white",
            foreground=INK,
        )
        scroll = ttk.Scrollbar(window, command=area.yview)
        scroll.pack(side="right", fill="y")
        area.pack(fill="both", expand=True)
        area.configure(yscrollcommand=scroll.set)
        area.insert("1.0", text)
        area.configure(state="disabled")

    def show_warnings(self):
        if self.result:
            self._text_window(
                "Comparison warnings",
                "\n\n".join(self.result.warnings)
                or "No parser or comparison warnings.",
            )

    def show_licenses(self):
        notice = Path(__file__).parent / "assets" / "THIRD_PARTY_NOTICES.txt"
        if notice.exists():
            text = notice.read_text(encoding="utf-8")
        else:
            text = "XERCompare is MIT licensed. See LICENSE in the source distribution.\n\nThird-party notices are included in the standalone Windows EXE."
        self._text_window("License and third-party notices", text)

    def _callback_error(self, kind, value, traceback):
        messagebox.showerror(
            "XERCompare", f"An interface action failed: {value}", parent=self.root
        )

    def close(self):
        if self.destroyed:
            return
        if self.busy:
            self.closing = True
            self.cancel()
            return
        self.destroyed = True
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    XERCompareApp(root)
    root.mainloop()
    return 0
