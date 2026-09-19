# Phases

Check boxes in PRs. Do not start phase N+1 until phase N tests pass.

2026-09-16 scope update: after Phase 3, the user explicitly requested the full
EXE. Phase 6 and Phase 8 were brought forward; the other unchecked analyses stay
deferred. Native Tk/ttk replaces the planned customtkinter dependency so the
desktop and build use packages already available offline.

2026-09-18 scope update: the user authorized advanced quality findings, calendar
workweeks/exceptions, matched assignment quantity/cost changes, custom profiles,
update history and richer owner PDFs. Implement these in the existing offline
EXE. Other deferred data dictionaries and CPM/risk/three-file workflows remain
outside this release.

## Phase 0 — Parser + fixtures  ✅ in tree

- [x] XER state machine (`ERMHDR` `%T` `%F` `%R` `%E`)
- [x] `cp1252` decode with utf-8 fallback
- [x] Typed `Schedule` / `Activity` / `Relationship`
- [x] Synthetic XER builder
- [x] pytest for parse + duration hours→days

## Phase 1 — Two-file compare core  ✅ in tree

- [x] Match on `task_code`
- [x] Added / deleted / modified activities
- [x] Field-level before/after
- [x] Progress vs revision vs date classification
- [x] Relationship add / delete / lag change

## Phase 2 — Excel + PDF  ✅ in tree

- [x] Summary, Added, Deleted, Modified, Logic, DCMA 14, Warnings
- [x] Color coding
- [x] PDF executive counts
- [x] CLI `xercompare left.xer right.xer -o outdir`

## Phase 3 — Report catalog split

Acceptance scope supplied with the handoff. Each item is checked only after a
synthetic fixture test and a green full pytest run.

- [x] Summary, Added Tasks, Deleted Tasks (retain counts; add WBS and base/revised columns)
- [x] Actual Date Change
- [x] Progress Change
- [x] Duration Description Change
- [x] Calendar Change (assignment only)
- [x] Constraint Change (primary and secondary)
- [x] Float Change (total and free float)
- [x] Early Start Changes
- [x] Early Finish Changes
- [x] Late Start Changes
- [x] Late Finish Changes
- [x] Variances (stored date/duration/float pairs, all matching activities with movement)
- [x] Added Relationships
- [x] Deleted Relationships
- [x] Lag Change
- [x] Driving Path Change (stored TF <= 0 approximation; no CPM)
- [x] Added Resource Assignments
- [x] Deleted Resource Assignments
- [x] Added UDF
- [x] Deleted UDF
- [x] Revised UDF
- [x] Changes Combined (activity, logic, resource, and UDF union)
- [x] DCMA 14 and Warnings retained, unavailable metrics labeled N/A
- [x] Revised-cell highlighting, full-range AutoFilter, frozen headers, empty-sheet coverage
- [x] CLI Excel + short PDF verification; guarded real-XER test (skips until two files arrive)
- [x] v0.2.1 display precision: one decimal for measurements, two for costs (including monetary UDFs), consistent desktop previews/PDF; preserve comparison precision and IDs/counts

### Deferred data model work (outside this report split)

- [x] Calendar *definition* diff (workweek + exceptions), not just assignment
- [ ] WBS add/delete/rename/move
- [ ] Activity code type/value add/delete + assignment changes (sheet of its own)
- [ ] Resource dictionary changes
- [x] Matched `TASKRSRC` quantity/cost/units changes (including overtime)
- [ ] Expenses (`PROJCOST`)
- [ ] Non-activity UDFs (project, resource, WBS, assignment scopes)
- [ ] Notebooks / steps if present
- [ ] Schedule options (`SCHEDOPTIONS`) recorded on Summary (not compared as activity data)

## Phase 4 — Quality + review lenses

- [x] Stored target/planned-finish review vs data date (explicit proxy; DCMA 11 stays N/A without an approved baseline)
- [x] Open ends list (the actual activities, not just %)
- [x] Constraint register (all constrained activities, both files)
- [x] Stored TF <= 0 membership approximation — delivered in Phase 3; not a calculated longest path
- [x] Milestone slip table
- [x] Out-of-sequence suspects: actual start with remaining predecessor not complete (best-effort from status flags)
- [x] Riding the data date / actuals after data date

### Advanced quality and saved profiles

- [x] Shared evidence-backed results for dashboard, Excel and PDF
- [x] Invalid dates, dangling start/finish events, resource absence as not assessed
- [x] Enable/disable checks; float/duration cutoffs and per-check limits
- [x] Save/load portable local JSON profiles; record settings in every workbook
- [x] Quality screen, drill-down findings and complete-report text search

## Phase 5 — PDF that an owner will read

- [x] Two-page narrative: what changed in counts, top 20 date slips, top 20 logic edits, DCMA pass/fail both sides
- [x] No raw 200-page dump in the PDF. That stays in Excel.

## Phase 6 — GUI

- [x] Two file pickers, output folder, Run
- [x] Progress text, cancellation, error recovery, open-output buttons
- [x] Still works fully from CLI
- [x] Native Tk/ttk, no webview, no network
- [x] Dashboard counts, 29-report catalog, 200-row previews, warnings and licenses
- [x] Worker thread and dated output folders; incomplete runs cleaned up
- [x] Native window tests for selection/run/preview/error/cancel and shorter screens

## Phase 7 — History (change over time)

- [x] Input: a folder of XERs + optional baseline
- [x] Sort by `last_recalc_date` then filename
- [x] Pairwise consecutive compares + baseline-vs-each
- [x] Trend sheet: activity count, finish date, critical count, DCMA fails per update

## Phase 8 — Windows EXE

- [x] PyInstaller onefile console (CLI) + onefile windowed (GUI)
- [x] Isolated Windows smoke: Python removed from PATH, bundled module origins checked, GUI/CLI reports verified
- [x] Version/icon, bundled third-party notices, MIT license, ZIP with synthetic demos
- [x] Simplified distribution: one desktop EXE, three-page PDF guide, full license PDF, optional examples; CLI excluded from the shared package
- [ ] Smoke test on a machine with no Python
- [x] Document offline operation, chosen output folder (or explicit CLI report paths), and `%TEMP%` runtime extraction

The separate Python-free-machine check remains pending: no clean VM was available.
The isolated runtime check passed on the current Windows host; it does not claim
to substitute for that separate-machine check.

## Phase 9 — Three-file AACE RP 29R MIP 3.4

- [ ] baseline.xer + progress-only.xer + update.xer
- [ ] Non-progress modifications (baseline → progress-only)
- [ ] Progress modifications (progress-only → update)
- [ ] Do not start this until a user supplies the three files and a definition of "progress-only" they actually use

## v0.3.0 verification

- [x] Native Windows suite: 84 passed, including the supplied real-XER pair
- [x] Packaged offline compare, quality drill-down, profile roundtrip and history journey
- [x] Real-pair 39-sheet workbook, two-page owner PDF and calendar/resource diagnostics
- [x] Workbook body-style reuse regression; independent highlights and cost formats retained
- [x] Four-page PDF instructions; release allowlist excludes all real data and CLI binaries
