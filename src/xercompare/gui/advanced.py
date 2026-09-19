"""Quality and profile screens for the existing native desktop app."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from xercompare.quality.profile import QualityProfile, RULES, load_profile, save_profile
from xercompare.reports.formatting import display_value


from xercompare.gui.history_page import HistoryPage


class AdvancedPages(HistoryPage):
    def _quality_page(self, page):
        ttk.Label(page, text="Schedule quality", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text="Select a check to see the affected activities and evidence. Custom settings are recorded in each report.",
            wraplength=760,
        ).pack(anchor="w", pady=(8, 18))
        columns = ("Check", "Base", "Revised", "Limit", "Result")
        frame = ttk.Frame(page)
        frame.pack(fill="both", expand=True)
        self.quality_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=15
        )
        for col in columns:
            self.quality_tree.heading(col, text=col)
            self.quality_tree.column(
                col, width=300 if col == "Check" else 100, stretch=col == "Check"
            )
        self.quality_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, command=self.quality_tree.yview)
        scroll.pack(side="right", fill="y")
        self.quality_tree.configure(yscrollcommand=scroll.set)
        self.quality_tree.tag_configure("flagged", foreground="#B83A42")
        self.quality_tree.bind("<Double-1>", lambda e: self.show_quality_findings())
        self.quality_note = tk.StringVar(self.root, value="Run a comparison first.")
        ttk.Label(page, textvariable=self.quality_note, wraplength=760).pack(
            anchor="w", pady=10
        )
        self.quality_tree.bind("<<TreeviewSelect>>", self._quality_selected)
        ttk.Button(
            page, text="Show affected activities", command=self.show_quality_findings
        ).pack(anchor="w", pady=10)

    def _quality_selected(self, event=None):
        selected = self.quality_tree.selection()
        if selected and self.result:
            result = next(r for r in self.result.checks if r.key == selected[0])
            self.quality_note.set(
                f"{result.affected} affected / {result.eligible} eligible. "
                + result.note
            )

    def show_quality_findings(self):
        selected = self.quality_tree.selection()
        if not selected or not self.result or self.busy:
            return
        self.report_filter = {"Check ID": selected[0]}
        self.report_query.set("")
        self.report_filter_label.set("Check: " + RULES[selected[0]][0])
        self.show_page("reports")
        self.report_tree.selection_set("Quality Findings")
        self.load_preview()

    def _fill_quality(self, result):
        self.quality_tree.delete(*self.quality_tree.get_children())
        base = {r.key: r for r in result.base_checks}
        for r in result.checks:
            state = (
                "Not assessed"
                if r.passed is None
                else "Pass" if r.passed else "Flagged"
            )
            self.quality_tree.insert(
                "",
                "end",
                iid=r.key,
                values=(
                    r.name,
                    display_value(base[r.key].value),
                    display_value(r.value),
                    ("0" if r.limit == 0 else "< " + display_value(r.limit))
                    + (" " + r.unit if r.unit == "count" else r.unit),
                    state,
                ),
                tags=("flagged",) if r.passed is False else (),
            )
        self.quality_note.set(
            "Select a check. Findings are stored values, not a CPM reschedule."
        )

    def _settings_page(self, page):
        ttk.Label(page, text="Quality settings", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            page,
            text="Applies to Quality Checks and history. The DCMA 14 sheet keeps conventional thresholds.",
            wraplength=700,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=12)
        self.profile_vars = {}
        for i, (key, label, value) in enumerate(
            [
                ("name", "Profile name", "Standard review"),
                (
                    "high_float_days",
                    "High float cutoff (activity-calendar days)",
                    "44.0",
                ),
                (
                    "high_duration_days",
                    "High duration cutoff (activity-calendar days)",
                    "44.0",
                ),
            ],
            2,
        ):
            self.profile_vars[key] = tk.StringVar(self.root, value=value)
            ttk.Label(page, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(page, textvariable=self.profile_vars[key], width=24).grid(
                row=i, column=1, sticky="w"
            )
        ttk.Label(
            page,
            text="Enable checks and set flag limits. Zero means no findings allowed; other values use “less than”.",
            wraplength=700,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=16)
        self.limit_vars = {}
        self.enabled_vars = {}
        for i, (key, (label, limit, unit)) in enumerate(RULES.items(), 6):
            self.limit_vars[key] = tk.StringVar(self.root, value=str(limit))
            self.enabled_vars[key] = tk.BooleanVar(self.root, value=True)
            ttk.Checkbutton(page, text=label, variable=self.enabled_vars[key]).grid(
                row=i, column=0, sticky="w", pady=3
            )
            ttk.Entry(page, textvariable=self.limit_vars[key], width=10).grid(
                row=i, column=1, sticky="w"
            )
            ttk.Label(page, text=unit).grid(row=i, column=2, sticky="w")
        buttons = ttk.Frame(page)
        buttons.grid(row=22, column=0, columnspan=3, sticky="w", pady=16)
        for title, command in [
            ("Apply settings", self.apply_profile),
            ("Save profile…", self.save_quality_profile),
            ("Load profile…", self.load_quality_profile),
            ("Reset defaults", lambda: self._set_profile(QualityProfile())),
        ]:
            ttk.Button(buttons, text=title, command=command).pack(
                side="left", padx=(0, 8)
            )
        self.profile_status = tk.StringVar(
            self.root, value="Current profile: Standard review"
        )
        ttk.Label(page, textvariable=self.profile_status, wraplength=700).grid(
            row=23, column=0, columnspan=3, sticky="w", pady=8
        )

    def _read_profile(self):
        return QualityProfile(
            name=self.profile_vars["name"].get().strip(),
            high_float_days=float(self.profile_vars["high_float_days"].get()),
            high_duration_days=float(self.profile_vars["high_duration_days"].get()),
            limits={k: float(v.get()) for k, v in self.limit_vars.items()},
            disabled=tuple(k for k, v in self.enabled_vars.items() if not v.get()),
        ).validate()

    def apply_profile(self):
        if self.busy:
            return False
        try:
            self.active_profile = self._read_profile()
        except ValueError as error:
            self.profile_status.set("Invalid settings: " + str(error))
            return False
        self.profile_status.set(
            "Applied: "
            + self.active_profile.name
            + ". Run again to use these settings."
        )
        return True

    def _set_profile(self, profile):
        if self.busy:
            return
        self.active_profile = profile
        for k, var in self.profile_vars.items():
            var.set(str(getattr(profile, k)))
        for k, var in self.limit_vars.items():
            var.set(str(profile.limit(k)))
        for k, var in self.enabled_vars.items():
            var.set(k not in profile.disabled)
        self.profile_status.set("Current profile: " + profile.name)

    def save_quality_profile(self):
        if not self.apply_profile():
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save quality profile",
            defaultextension=".json",
            filetypes=[("Quality profile", "*.json")],
        )
        if path:
            try:
                save_profile(self.active_profile, path)
                self.profile_status.set("Saved profile: " + path)
            except OSError as error:
                self.profile_status.set(str(error))

    def load_quality_profile(self):
        if self.busy:
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Load quality profile",
            filetypes=[("Quality profile", "*.json")],
        )
        if path:
            try:
                self._set_profile(load_profile(path))
            except (ValueError, OSError) as error:
                self.profile_status.set("Cannot load profile: " + str(error))

    def clear_report_filter(self):
        self.report_filter = {}
        self.report_query.set("")
        self.report_filter_label.set("All report rows")
        self.load_preview()
