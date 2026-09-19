"""Command-line entry point.

xercompare left.xer right.xer
xercompare left.xer right.xer -o out_dir
xercompare left.xer right.xer --excel only.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from xercompare import __version__
from xercompare.compare.engine import compare_schedules
from xercompare.model.schedule import build_schedule
from xercompare.parse.xer_parser import ParseError, parse_xer
from xercompare.reports.excel import write_excel
from xercompare.reports.pdf import write_pdf


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="xercompare",
        description="Compare two Primavera P6 XER files. Offline. No P6 license.",
    )
    p.add_argument("left", help="Older / baseline XER")
    p.add_argument("right", help="Newer / update XER")
    p.add_argument("-o", "--out", default=".", help="Output directory")
    p.add_argument("--excel", help="Excel path (default: <out>/compare.xlsx)")
    p.add_argument("--pdf", help="PDF path (default: <out>/compare.pdf)")
    p.add_argument("--no-pdf", action="store_true")
    p.add_argument("--no-excel", action="store_true")
    p.add_argument("--version", action="version", version=f"xercompare {__version__}")
    args = p.parse_args(argv)

    left_path = Path(args.left)
    right_path = Path(args.right)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    try:
        left = build_schedule(parse_xer(left_path))
        right = build_schedule(parse_xer(right_path))
    except ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    comparison = compare_schedules(left, right)
    s = comparison.summary
    print(
        f"{left_path.name} ({s['left_activities']} act) -> "
        f"{right_path.name} ({s['right_activities']} act)"
    )
    print(
        f"  added {s['added']}  deleted {s['deleted']}  "
        f"modified {s['modified']}  unchanged {s['unchanged']}"
    )
    print(
        f"  logic +{s['logic_added']} / -{s['logic_deleted']} / lag {s['logic_modified']}"
    )
    print(
        f"  resource +{len(comparison.resource_added)} / -{len(comparison.resource_deleted)}; "
        f"UDF +{len(comparison.udf_added)} / -{len(comparison.udf_deleted)} / "
        f"revised {len(comparison.udf_modified)}"
    )
    for w in comparison.warnings:
        print(f"  warning: {w}")

    if not args.no_excel:
        excel_path = Path(args.excel) if args.excel else out / "compare.xlsx"
        write_excel(comparison, excel_path)
        print(f"  excel: {excel_path}")
    if not args.no_pdf:
        pdf_path = Path(args.pdf) if args.pdf else out / "compare.pdf"
        write_pdf(comparison, pdf_path)
        print(f"  pdf:   {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
