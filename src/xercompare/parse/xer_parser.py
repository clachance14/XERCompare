"""Parse a Primavera P6 XER file into raw tables.

XER is tab-delimited text with a tiny state machine:

    ERMHDR   export header (not a table)
    %T NAME  start table
    %F cols  column names for current table
    %R vals  data row
    %E       end of file

Encoding is Windows-1252. Field order varies by P6 version, so rows are
always zipped to header names, never accessed by column index.
"""

from __future__ import annotations

import csv
from io import StringIO
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ParseError(Exception):
    """Raised when an XER cannot be read as a valid export."""


# Tables the rest of the product actually uses. Unknown tables are still
# captured so later phases can turn them on without a parser change.
WANTED_TABLES = {
    "PROJECT",
    "PROJWBS",
    "TASK",
    "TASKPRED",
    "CALENDAR",
    "RSRC",
    "TASKRSRC",
    "PROJCOST",
    "ACTVTYPE",
    "ACTVCODE",
    "TASKACTV",
    "UDFTYPE",
    "UDFVALUE",
    "SCHEDOPTIONS",
    "MEMOTYPE",
    "TASKMEMO",
    "TASKPROC",
    "NONWORK",
}


@dataclass
class XerFile:
    path: Path
    version: str | None
    header: list[str]
    tables: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def table(self, name: str) -> list[dict[str, str]]:
        return self.tables.get(name, [])


def parse_xer(path: str | Path) -> XerFile:
    path = Path(path)
    if not path.exists():
        raise ParseError(f"File not found: {path}")

    # cp1252 is what P6 writes. utf-8-sig is a fallback for hand-edited fixtures.
    raw = path.read_bytes()
    text = _decode(raw)

    version: str | None = None
    header: list[str] = []
    tables: dict[str, list[dict[str, str]]] = {}
    warnings: list[str] = []

    current_table: str | None = None
    current_fields: list[str] = []

    if not text:
        raise ParseError(f"Empty file: {path}")

    # Keep quoted newlines, normalized across Windows CRLF and Unix LF exports.
    reader = csv.reader(StringIO(text, newline=None), delimiter="\t")
    for cells in reader:
        row_num = reader.line_num
        if not cells:
            continue
        marker = cells[0]

        if marker == "ERMHDR":
            header = cells
            if len(cells) > 1:
                version = cells[1]
            continue

        if marker == "%T":
            if len(cells) < 2 or not cells[1]:
                warnings.append(f"Line {row_num}: %T with no table name")
                current_table = None
                current_fields = []
                continue
            current_table = cells[1].strip()
            current_fields = []
            tables.setdefault(current_table, [])
            continue

        if marker == "%F":
            current_fields = [c.strip() for c in cells[1:]]
            continue

        if marker == "%R":
            if current_table is None:
                warnings.append(f"Line {row_num}: %R before any %T")
                continue
            values = cells[1:]
            if current_fields and len(values) != len(current_fields):
                warnings.append(
                    f"Line {row_num}: {current_table} row has {len(values)} values, "
                    f"{len(current_fields)} fields"
                )
            row: dict[str, str] = {}
            for i, name in enumerate(current_fields):
                row[name] = values[i] if i < len(values) else ""
            tables[current_table].append(row)
            continue

        if marker == "%E":
            break

    if "TASK" not in tables:
        warnings.append("No TASK table found — file may not be a project XER")

    return XerFile(
        path=path,
        version=version,
        header=header,
        tables=tables,
        warnings=warnings,
    )


def _decode(raw: bytes) -> str:
    for enc in ("cp1252", "utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace")


def as_int(value: str | None, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def as_float(value: str | None, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def hours_to_days(hours: float | None, hours_per_day: float = 8.0) -> float | None:
    if hours is None:
        return None
    if hours_per_day <= 0:
        hours_per_day = 8.0
    return hours / hours_per_day
