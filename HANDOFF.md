# XERCompare handoff — v0.3.0 advanced offline desktop

Continue the existing app. Read this file, AGENTS.md, docs/PHASES.md,
docs/SPEC.md, then docs/REPORTS.md. No rewrite or new runtime dependency.

## Public distribution

The user authorized publication to the public repository
https://github.com/clachance14/XERCompare with a v0.3.0 Public Beta release.
The README links directly to the versioned Windows ZIP and PDF guide. GitHub
issue forms collect bugs, feature requests, and beta feedback; Discussions is
the question/conversation channel. Feedback is public and voluntary. The app
still has no network calls or automatic uploads. PDF feedback links open only
when the reader chooses them.

Keep the release ZIP's five-file allowlist. Release assets also include a
standalone copy of the guide and SHA256SUMS.txt. Never publish ignored build
evidence or real fixtures. The reviewed README screenshot uses synthetic data.
Git commits use the account's GitHub noreply address. See CONTRIBUTING.md for
developer setup and docs/releases/v0.3.0.md for public release notes.

## Authorized scope and implementation

The user explicitly authorized building the proposed advanced features and asked
us to inspect the two XERs loaded in the running v0.2.1 EXE. The existing window
identified those two local files. They were copied only to the ignored
`tests/fixtures/real/` folder. Do not put real exports, generated real reports,
paths or screenshots into the shared release.

v0.3.0 adds:

- Effective inherited calendar workweek/exception changes for shared activities.
  The own calendar-tree reader handles exported DEL separators, property order,
  OLE exception dates, midnight finishes and parent calendars. Unsupported or
  cyclic definitions are unknown with reasons; no CPM is calculated.
- Matched resource quantity/cost/units changes, including overtime. Assignment
  GUIDs and exact-value rows reduce false changes for reordered duplicates;
  ambiguous remaining groups warn. New events enter Changes Combined.
- Shared quality results with eligible counts, activity/relationship evidence,
  N/A reasons and per-check thresholds. Conventional DCMA 9 now evaluates stored
  invalid dates; unresourced exports and empty populations are N/A. DCMA 11–14
  retain baseline/CPM limitations. Missed target finish is a separate explicit proxy.
- Quality Findings, Open Ends, Constraint Register, Milestone Slips, Out of
  Sequence, Date Review, Quality Checks and Check Settings. Together with the
  two new value reports these extend the catalog from 29 to **39 sheets**.
- Native Quality findings and Quality settings screens, local JSON profile
  save/load, and report search across all rows before the 200-row preview cap.
- Update history: review project identity/order, choose an optional baseline,
  generate trends and four Excel charts, and complete comparison workbooks/PDFs
  for consecutive pairs and baseline-to-update pairs. Equal data dates warn.
  Entire incomplete history sets are discarded on failure/cancellation.
- Owner PDF with counts, factual narrative, ranked finish slips, milestone
  counts, relationship edits and DCMA on both sides. The real pair fits two pages.
- A four-page START HERE.pdf covering the original simple workflow and new views.

Real-file performance testing exposed repeated body-style construction in
Excel. The exporter now registers body styles once per workbook and copies
independent style arrays, preserving numeric formats and revised-cell highlights.
A deterministic fixture test checks formatting setup does not grow per cell.

## Preserve

Own cp1252/csv.reader parser and %F name binding; task_code matching; first-project
scope with warnings; progress/revision/date/both classification; offline MIT;
working source CLI; original report inventory. No PyP6Xer or GPL/LGPL dependency.
Measurements display one decimal, costs two; counts/IDs and numeric precision stay
intact. Runtime remains openpyxl/reportlab and native Tk/ttk. No GUI framework change.

## Windows release and commands

The shared ZIP contains exactly the desktop XERCompare.exe, START HERE.pdf,
Documents/Licenses.pdf, and two synthetic examples. No CLI EXE or text docs ship.
The executable includes Python. The user's desktop shortcut points to
Downloads/XERCompare/XERCompare.exe. The loose Downloads EXE is kept in sync.

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\build_windows.py
.venv\Scripts\python.exe scripts\verify_windows.py
.venv\Scripts\python.exe scripts\package_windows.py
```

Build/verify default to GUI only. `--with-cli` is an optional developer build.
Verification exercises real native controls for compare, filtered findings,
profile roundtrip and history with socket connection attempts blocked. It checks
bundled module origins from an isolated Windows PATH and validates workbook counts.
Window-specific captures avoid grabbing unrelated foreground applications.
See docs/VERIFICATION.md for final results and evidence paths. A separate machine
without Python remains unavailable; do not mark that external check complete.

## Next work and boundaries

Follow fixture/test → implementation → pytest → phase checkbox. User-provided
real exports take priority for parser/integration issues. PHASES.md keeps remaining
WBS/code/resource dictionary work, expenses, nonactivity UDFs, notebooks/steps and
schedule options unchecked. No live P6 connection, MSP/XML, CPM recalculation,
Monte Carlo, or three-file MIP 3.4 has been authorized by this feature request.
