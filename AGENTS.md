# Instructions for AI agents working on XERCompare

Read this file before writing code. Then read `docs/SPEC.md` and `docs/REPORTS.md`.

## What this is

An offline, open-source, no-network Windows EXE that takes two Primavera P6 `.xer` files and writes an Excel workbook plus a PDF summary of everything that changed.

It is not a P6 clone. It does not reschedule. It compares stored fields.

## Constraints that do not move

- Air-gapped. No HTTP. No telemetry. No license server. No "phone home."
- MIT license. Do not add LGPL/GPL dependencies (do **not** add PyP6Xer).
- One project per XER. If a file has more than one `PROJECT` row, use the first and warn.
- Match activities by `task_code` (the Activity ID humans see), never by internal `task_id`.
- Decode XER as `cp1252`. Never `str.split("\t")` — use `csv.reader`.
- Do not copy another vendor's report layout, sheet names, logos, or wording. Recreate the *analyses*.
- Do not invent CPM results. If a metric needs a live engine, mark it `N/A` and say why.

## How to work

1. Pick the next unchecked item in `docs/PHASES.md`.
2. Write or extend a test first using `tests/fixtures/make_xer.py`. When real XERs arrive, put them in `tests/fixtures/real/` (gitignored if sensitive) and add a guarded test.
3. Keep parsers generic: zip `%R` values to `%F` names. P6 column order changes by version.
4. Durations and float in XER are hours (`*_hr_cnt`). Convert to days with the activity calendar's `day_hr_cnt`, default 8.
5. Run `pytest` before you stop.
6. Do not expand scope sideways. Finish the current phase's report sheets before starting a new analysis family.

## Layout

```
src/xercompare/parse/       XER state machine
src/xercompare/model/       typed Schedule / Activity / Relationship
src/xercompare/compare/     two-file diff + classification
src/xercompare/quality/     DCMA 14 (stored-value)
src/xercompare/reports/     Excel + PDF
src/xercompare/gui/         Phase 6
src/xercompare/cli.py       entry point
```

## Classification rules

On a modified activity:

- `progress`: actual start/finish, remaining duration, physical %, status, resume/suspend
- `revision`: name, original duration, calendar, constraints, WBS, activity codes, task type
- `date`: early/late/target dates and total float (effects, not intent)
- `both`: progress + revision on the same activity

Logic add/delete/type change is always `revision`. Lag-only change is `revision`.

## Out of scope until a later phase

- Recalculating CPM
- Microsoft Project / P6 XML
- Multi-project XERs as first-class
- Uploading files anywhere
- Three-file AACE MIP 3.4 (baseline / progress-only / update) — Phase 9
- Folder-of-XERs trend history — Phase 7
