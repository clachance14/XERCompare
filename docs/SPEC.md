# XERCompare technical spec

## Goal

A standalone Windows program that:

1. Reads two Primavera P6 `.xer` files from local disk.
2. Compares them with no P6 install and no network.
3. Writes Excel (full tables) and PDF (executive summary).

Version 0.3.0 includes a native desktop GUI, evidence-backed quality checks,
local saved profiles, and folder-of-updates history. Three-file progress-only
analysis remains outside this release.

This spec is for implementers. Product rules that must not drift live in `AGENTS.md`.

## Non-goals

- Recalculating the critical path
- Importing back into P6
- Viewing a Gantt
- Supporting `.xml` / `.mpp` in v1
- Cloning Claim Digger HTML, Change Inspector workbooks, Schedule Auditor Word files, or any other vendor template

## XER rules

```
ERMHDR <version> <date> ...
%T     TABLE_NAME
%F     col1    col2    col3
%R     v1      v2      v3
%E
```

- Encoding: `cp1252` first, then `utf-8-sig`.
- Parse with `csv.reader(..., delimiter="\t")`.
- Bind rows by header name, never by index.
- Stop at `%E`.
- Keep unknown tables in `XerFile.tables` even if the model ignores them.

### Tables we model

| Table | Role |
|---|---|
| PROJECT | id, short name, data date (`last_recalc_date`) |
| PROJWBS | WBS tree |
| TASK | activities |
| TASKPRED | relationships |
| CALENDAR | names + hours/day + raw definition |
| RSRC | resource dictionary |
| TASKRSRC | assignments |
| PROJCOST | expenses |
| ACTVTYPE / ACTVCODE / TASKACTV | activity codes |
| UDFTYPE / UDFVALUE | UDFs |
| SCHEDOPTIONS | record only |
| MEMOTYPE / TASKMEMO / TASKPROC | notebooks / steps |

### Fields that matter on TASK

`task_id`, `task_code`, `task_name`, `wbs_id`, `clndr_id`, `task_type`, `status_code`,
`target_drtn_hr_cnt`, `remain_drtn_hr_cnt`, `phys_complete_pct`, `complete_pct_type`,
`early_start_date`, `early_end_date`, `late_start_date`, `late_end_date`,
`target_start_date`, `target_end_date`, `act_start_date`, `act_end_date`,
`restart_date`, `reend_date`, `cstr_type`, `cstr_date`, `cstr_type2`, `cstr_date2`,
`total_float_hr_cnt`, `free_float_hr_cnt`.

Hours → days: `hours / calendar.day_hr_cnt` (default 8).

Relationship types: `PR_FS` `PR_SS` `PR_FF` `PR_SF`.

Status: `TK_NotStart` `TK_Active` `TK_Complete` `TK_NotStart` variants as exported.

## Matching

Primary key: `task_code`.

If two rows share a `task_code`, last row wins and a warning is recorded.

Relationships match on `(pred_code, succ_code, type)`. Lag is a field change, not identity.

Assignments prefer GUIDs within a visible activity, then identical value rows,
resource name/ID/role keys and name/ID fallbacks, preserving duplicate counts.
Ambiguous remaining groups warn; see REPORTS.md for the exact matching order. Activity UDFs match by label (falling back to type name/ID);
values are mapped to visible Activity IDs through `UDFVALUE.fk_id`.

## Comparison output object

`Comparison` holds:

- `added` / `deleted` / `modified` activity deltas
- logic added / deleted / lag-changed
- resource assignment added/deleted and activity UDF added/deleted/revised
- matched resource quantity/cost/units and effective calendar-definition deltas
- selected QualityProfile metadata; remaining expense/code/WBS dictionaries are deferred
- `warnings`

Every modified activity has a `klass` of `progress`, `revision`, `date`, or `both`. Rules are in `AGENTS.md`.

## Reports

See `docs/REPORTS.md`. Excel is the system of record. PDF is a cover sheet.

## CLI

```
xercompare LEFT.xer RIGHT.xer
xercompare LEFT.xer RIGHT.xer -o C:\out
xercompare LEFT.xer RIGHT.xer --excel report.xlsx --pdf summary.pdf
```

Exit codes: `0` ok, `2` bad file, `1` unexpected.

## Packaging

- Python 3.11+
- Runtime deps: `openpyxl`, `reportlab`; native `tkinter`/`ttk` from Windows Python
- PyInstaller `--onefile`: windowed `XERCompare.exe`; optional developer console build via `--with-cli`
- Shared release: one desktop EXE, four-page `START HERE.pdf`, complete license PDF, optional synthetic examples
- Bundled Python runtime, required libraries, Tcl/Tk, Vera fonts and license notices
- Native Windows builds only; build and verification scripts use local packages
- No hidden network libraries

The desktop runs comparison/export on a worker thread. It publishes both reports
into a new dated output subfolder only after both succeed. Cancellation is
checked between stages and discards incomplete reports. UI previews cap at 200
rows; the workbook remains complete. Source CLI behavior stays unchanged.

## Security / government-sensitive XERs

- Read only the two (or N) paths the user passed
- Write only to the chosen output folder (or explicit CLI `--excel`/`--pdf` paths)
  and the process temp dir
- Do not copy XERs into logs
- Do not include sample real XERs in the public repo
- Tests use synthetic files from `tests/fixtures/make_xer.py`

## Known limits (document on Summary and PDF)

1. Dates and float are whatever P6 stored at last schedule. Different schedule options → incomparable float.
2. Calendar definitions are compared for shared activities; unused calendar inventory and CPM effects are not calculated.
3. DCMA 9 uses stored dates. DCMA 11/14 need an approved baseline; 12/13 need CPM recalculation. A separate missed-target-finish proxy is labeled clearly.
4. Renamed activity IDs look like delete + add. There is no fuzzy name match in v1. Add an optional mapping file later if needed.
5. Multi-project XERs: first project only.
