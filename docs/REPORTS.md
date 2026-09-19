# Report catalog

Phase 3 implements the requested analysis catalog in XERCompare's own workbook.
The PDF remains a short cover report. All values come from the two local XERs;
there is no CPM recalculation or connection to P6.

## Excel workbook

| Sheet | Contents |
|---|---|
| Summary | File/project identities, data dates, P6 versions, change counts, grouped links to detail reports and row counts |
| Added Tasks | Activity IDs present only in the revised file |
| Deleted Tasks | Activity IDs present only in the base file |
| Actual Date Change | Actual start and finish |
| Progress Change | Remaining duration, physical percent, status, restart/re-end, suspend/resume |
| Duration Description Change | Original duration and task name |
| Calendar Change | Calendar assignment names; effective definitions appear separately |
| Constraint Change | Primary and secondary constraint types and dates |
| Float Change | Total and free float in activity-calendar days |
| Early Start Changes | Stored early start |
| Early Finish Changes | Stored early finish |
| Late Start Changes | Stored late start |
| Late Finish Changes | Stored late finish |
| Variances | One row per shared activity with date/duration/float movement: ES/EF/LS/LF, target/actual dates, total/free float, original/remaining duration; no row truncation |
| Added Relationships | Successor ID/name/WBS, predecessor, type and revised lag |
| Deleted Relationships | Successor ID/name/WBS, predecessor, type and base lag |
| Lag Change | Same predecessor/successor/type, changed lag hours |
| Driving Path Change | **Approximation from stored TF <= 0 hours**, including entered/left/retained members and added/deleted tasks; missing float is unknown |
| Added Resource Assignments | Added assignments, with stored quantity/cost context |
| Deleted Resource Assignments | Removed assignments, preserving duplicate assignment counts |
| Added UDF | Added activity UDF values |
| Deleted UDF | Removed activity UDF values |
| Revised UDF | Changed activity UDF values |
| Changes Combined | Task inventory, activity fields, relationships, resource inventory and UDF events; change type, field and class; UDF events appear once |
| DCMA 14 | Fourteen rows, base/revised results and reasons for unavailable checks |
| Warnings | Parser, duplicate-ID, project-identity, unresolved-reference and unsupported-UDF-scope warnings |
| Modified | Supplementary raw activity-field changes, including codes and UDFs |
| Logic | Supplementary union of added/deleted/lag-changed relationships |
| Legend | Classification and color explanations |

Excel prohibits `/` in sheet names, so the duration/description report is named
`Duration Description Change`.

## Grid and matching conventions

Activity reports start with `Activity ID | Name | WBS`, followed by paired
`Base <field> | Revised <field>` columns and any extra context. Shared activities
use revised name/WBS context; deletions use the base context. Only changed revised
cells are highlighted. Numbers remain numeric. Imported strings remain literal,
including strings beginning with `=`. Headers are on row 4, frozen above row 5;
AutoFilter covers every data row. Empty reports retain headers and no dummy rows.
Summary row counts count report records, which may exceed unique activity counts.

Measured values display one decimal place; costs display two. This includes
resource costs and activity UDFs exported as `FT_MONEY` or `FT_COST`, regardless
of their labels. Counts stay whole numbers, and IDs, dates and text are unchanged.
Excel retains the full numeric values and applies display formats; comparisons
still use the existing precision. Desktop previews use the same formats, and PDF
measurements use one decimal. Halfway values round away from zero, as in Excel.

- Activities match by `task_code`, never internal `task_id`. ID renames appear as
  delete/add. Field comparisons retain the existing four-decimal numeric tolerance.
- Days use each side's activity calendar hours/day, default 8. Calendar-name changes
  and any resulting duration/float conversion changes can appear together.
- Relationships match visible predecessor/successor/type; changing type is a
  deletion plus addition. Lag remains in stored hours. Unresolved endpoints are
  retained with internal IDs and a warning; such external links cannot be matched
  reliably when those IDs change.
- Assignments match activity/resource names, preferring equal IDs within equal
  names, then falling back to resource ID. Multiple identical assignments retain
  their multiplicity. Matched quantity/cost changes are included; resource dictionary edits remain deferred.
- Activity UDFs map `UDFTYPE` to `UDFVALUE.fk_id` within the selected project. Labels
  are the match key, falling back to type name, then ID. Numeric values are numeric;
  dates/text/code IDs retain their stored representations. Duplicate labels on an
  activity warn and use the last value. Non-TASK scopes are excluded with a warning.
  Type dictionaries and label renames are not independently reconciled.
- `Changes Combined` is the union of underlying events. Derived variance/path
  views do not add duplicate events. Raw `Modified` also includes UDF fields for
  compatibility. Network/resource-only edits have separate inventory counts and
  do not change the TASK-field modified count. Calendar-definition-only edits likewise have their own event rows.

## Advanced reports (v0.3.0)

The workbook now has **39 sheets**. These ten additions use the same header,
filter and freeze conventions:

| Sheet | Contents |
|---|---|
| Calendar Definitions | Effective inherited workweek/exception and hours-conversion changes for shared activities, with activity/WBS context |
| Resource Value Changes | Matched assignment quantities, regular/overtime costs, units per hour and cost per unit |
| Quality Checks | Base/revised values, populations, affected counts, pass/flag/not-assessed results and reasons |
| Quality Findings | Activity-level evidence on both sides, related activities and explanations |
| Open Ends | Missing predecessor/successor and dangling start/finish event findings |
| Constraint Register | All primary/secondary constraints, including unchanged ones |
| Milestone Slips | Stored early-start movement for start milestones and early-finish movement for finish/zero-duration milestones; ranked elapsed days |
| Out of Sequence | Relationship-type-aware actual-event order suspects |
| Date Review | Actuals after data date, unfinished early events before data date, riding the data date and missed target-finish proxy |
| Check Settings | Exact saved profile, cutoffs, enabled checks and limits used for this run |

Calendars decode the exported parenthesized tree, including DEL separators,
reordered shift attributes, midnight finishes and OLE exception-date serials.
Inherited days/exceptions are overridden individually. Malformed, missing or
cyclic definitions remain unknown with an explanation; they are never treated
as nonworking. Definitions compare the calendars used by each shared activity;
unused calendar inventory and CPM effects are not analyzed. Assignment name
changes stay in Calendar Change. Name/ID renumbering does not by itself imply
working-time changes.

Resource matching prefers assignment GUIDs within a visible activity, then
identical value rows, activity/resource name+ID+role, name+role, and finally
ID+role. Multiplicity is preserved. Remaining ambiguous duplicate groups warn
and are paired in export order. All new value changes enter Changes Combined.
Quantities and costs are exported units/currency; there is no currency conversion.

Quality Checks uses the selected local profile. DCMA 14 always uses conventional
thresholds. Zero limits allow zero findings; positive limits require values
strictly below the limit. Numeric tests use unrounded values. Empty populations,
missing data dates, an entirely unresourced export and disabled checks show not
assessed. Float/duration populations require those values. Percentages count
affected activities once, except relationship checks, which count relationships.
Incomplete duration tasks exclude completed activities and milestones.

Out-of-sequence checks follow the governed events for FS, SS, FF and SF links.
They do not calculate lag-calendar offsets or retained-logic/progress-override
behavior. Dangling-event and riding-date findings are review indicators, not
proof of an invalid schedule. The missed-finish check uses exported target dates
before the data date and flags missing or later actual finishes. It is a **proxy**,
not an approved-baseline DCMA 11 calculation.

## PDF

The owner report summarizes counts, the most frequently changed fields, custom
quality flag counts and milestone slip counts. It ranks up to 20 later stored
early finishes by elapsed 24-hour days, shows up to 20 relationship edits, and
reports conventional DCMA results for both files. Bounded warnings and limitations
remain visible. The real validation pair fits two pages; unusually long content
may require additional pages. Full detail remains in Excel. No narrative claims
that a particular edit caused completion-date movement.

## History

Update history loads a local folder (nonrecursive), orders by data date then
filename, and requires review of project identity/order. The user can reorder
rows and select an explicit optional baseline. Equal dates warn that chronology
is ambiguous. Different project names require acknowledgment.

The dated history folder contains history.xlsx/history.pdf plus a complete
39-sheet workbook and PDF for every consecutive comparison and every explicit
baseline-to-update comparison (excluding the baseline compared with itself).
The history workbook records the reviewed sequence, activity counts, latest
stored early finish, stored-TF<=0 counts, conventional DCMA flags/N/A counts and
profile flags/not-assessed counts. Four charts show counts and finish movement.
Relative links open the full comparison workbooks. Cancellation removes the
entire incomplete history set.

## DCMA availability

Conventional thresholds are retained for checks 1–10. These are stored-value
review indicators, not certification of schedule quality.

| # | Check | Target / availability |
|---|---|---|
| 1 | Missing predecessor/successor on incomplete duration tasks | < 5% |
| 2 | Leads | 0 |
| 3 | Positive lags | < 5% |
| 4 | Non-FS relationships | < 10% |
| 5 | Hard constraints | < 5% |
| 6 | High float (>44 activity-calendar days) | < 5% |
| 7 | Negative float | 0 |
| 8 | High original duration (>44 activity-calendar days) | < 5% |
| 9 | Invalid stored dates vs data date | 0; N/A if data date/population unavailable |
| 10 | Missing resources | 0 when resource-loaded; otherwise N/A |
| 11 | Missed tasks | N/A — approved baseline required; separate target-date proxy in Date Review |
| 12 | Critical-path test | N/A — requires CPM recalculation |
| 13 | CPLI | N/A — requires CPM recalculation |
| 14 | BEI | N/A — needs a defined baseline |

The driving-path sheet is a membership approximation using stored float. It does
not establish a connected or longest path, and is not a substitute for check 12.

## Deferred work

WBS/code/resource dictionaries, expenses, non-activity UDFs, notebooks/steps,
schedule-option comparison, CPM recalculation and three-file MIP 3.4 remain
outside this release. Only the first project in an export is modeled.

Visual references are recorded in DESIGN.md. No proprietary scores or vendor UI
are reproduced. The desktop previews up to 200 rows; search filters the entire
report before applying that limit. The workbook always contains all rows.
