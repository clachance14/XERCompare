"""Owner-facing PDF cover sheet."""

from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    PageBreak,
)

from xercompare.compare.engine import Comparison
from xercompare.quality.dcma import assess
from xercompare.reports.formatting import display_value
from xercompare.quality.checks import inspect_schedule, milestone_movements
from xercompare.quality.profile import QualityProfile


NAVY = colors.HexColor("#1B365D")
STEEL = colors.HexColor("#2E75B6")
GREEN = colors.HexColor("#C6EFCE")
RED = colors.HexColor("#FFC7CE")
GOLD = colors.HexColor("#FFE699")
BLUE = colors.HexColor("#BDD7EE")
ORANGE = colors.HexColor("#F8CBAD")
GRAY = colors.HexColor("#F2F2F2")
DK = colors.HexColor("#333333")


def write_pdf(comparison: Comparison, dest: str | Path) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "xc_title",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=18,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    sub = ParagraphStyle(
        "xc_sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=STEEL,
        spaceAfter=8,
    )
    h = ParagraphStyle(
        "xc_h",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "xc_body",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=DK,
    )
    small = ParagraphStyle(
        "xc_small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=DK,
    )

    doc = SimpleDocTemplate(
        str(dest),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="XERCompare summary",
        author="XERCompare",
    )
    s = comparison.summary
    klasses = Counter(d.klass for d in comparison.modified)

    story = [
        Paragraph("XERCOMPARE", title),
        Paragraph(
            "Primavera P6 schedule comparison  ·  stored XER fields  ·  not a CPM reschedule",
            sub,
        ),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8),
        Paragraph(
            f"<b>Left (older):</b> {escape(comparison.left.source.name)} &nbsp;&nbsp; "
            f"project {escape(comparison.left.project.short_name or '—')} &nbsp;&nbsp; "
            f"data date {escape(comparison.left.project.data_date or 'n/a')}",
            body,
        ),
        Paragraph(
            f"<b>Right (newer):</b> {escape(comparison.right.source.name)} &nbsp;&nbsp; "
            f"project {escape(comparison.right.project.short_name or '—')} &nbsp;&nbsp; "
            f"data date {escape(comparison.right.project.data_date or 'n/a')}",
            body,
        ),
        Paragraph("Change inventory", h),
    ]

    profile = comparison.profile or QualityProfile()
    before_checks = inspect_schedule(comparison.left, profile)
    after_checks = inspect_schedule(comparison.right, profile)
    before_flags = sum(r.passed is False for r in before_checks)
    after_flags = sum(r.passed is False for r in after_checks)
    story.append(
        Paragraph(
            f"The revised export contains <b>{s['right_activities']:,} activities</b>: "
            f"{s['added']:,} added, {s['deleted']:,} deleted, and {s['modified']:,} with changed stored fields. "
            f"There are {s['logic_added']:,} added relationships, {s['logic_deleted']:,} deleted relationships, "
            f"and {s['logic_modified']:,} lag edits. "
            f"Resource assignments: {len(comparison.resource_added):,} added, "
            f"{len(comparison.resource_deleted):,} deleted, {len(comparison.resource_modified):,} with value changes. "
            f"Activity UDFs: {len(comparison.udf_added):,} added, {len(comparison.udf_deleted):,} deleted, "
            f"{len(comparison.udf_modified):,} revised.",
            body,
        )
    )
    story.append(Spacer(1, 7))
    story.append(
        Paragraph(
            f"<b>Quality profile:</b> {escape(profile.name)}. Flagged checks: {before_flags} base / {after_flags} revised. "
            f"{sum(r.passed is None for r in after_checks)} revised checks could not be assessed or were disabled. "
            "See Quality Findings in Excel for activity-level evidence and Check Settings for the applied thresholds.",
            body,
        )
    )
    slips = [
        row
        for row in milestone_movements(comparison, False)
        if row[3] is not None and row[3] > 0
    ]
    milestones = [
        row
        for row in milestone_movements(comparison)
        if row[3] is not None and row[3] > 0
    ]
    story.append(
        Paragraph(
            f"<b>Stored-date movement:</b> {len(slips):,} shared activities finish later; "
            f"{len(milestones):,} milestone dates move later. These changes do not establish their cause.",
            body,
        )
    )
    fields = Counter(
        change.field for delta in comparison.modified for change in delta.changes
    )
    if fields:
        top = "; ".join(
            f"{escape(field)} ({count:,})" for field, count in fields.most_common(4)
        )
        story.append(
            Paragraph("<b>Most frequent field changes:</b> " + top + ".", small)
        )
    story.append(Paragraph("Largest stored finish slips (up to 20)", h))
    if slips:
        rows = [["Activity ID", "Name", "Base finish", "Revised finish", "Days later"]]
        for activity, before, after, delta, basis in slips[:20]:
            rows.append(
                [
                    _clip(activity.task_code, 18),
                    Paragraph(escape(_clip(activity.task_name, 52)), small),
                    before[:16],
                    after[:16],
                    display_value(float(delta)),
                ]
            )
        table = Table(rows, colWidths=[65, 210, 88, 88, 67], repeatRows=1)
        table.setStyle(_grid())
        story.append(table)
    else:
        story.append(
            Paragraph("No later stored early-finish dates on shared activities.", body)
        )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Movement uses elapsed 24-hour days, not working days. Start milestones use early start in the Milestone Slips sheet. "
            "The Excel workbook contains all changes and both sides of every quality finding.",
            small,
        )
    )
    story.append(PageBreak())
    story.append(Paragraph("Relationship edits (up to 20)", h))
    edits = (
        comparison.logic_added + comparison.logic_deleted + comparison.logic_modified
    )
    if edits:
        rows = [
            [
                "Predecessor",
                "Successor",
                "Type",
                "Change",
                "Base lag h",
                "Revised lag h",
            ]
        ]
        for d in edits[:20]:
            rows.append(
                [
                    _clip(d.pred_code, 22),
                    _clip(d.succ_code, 22),
                    d.rel_type,
                    d.status,
                    display_value(d.lag_before),
                    display_value(d.lag_after),
                ]
            )
        table = Table(rows, colWidths=[120, 120, 40, 78, 80, 80], repeatRows=1)
        table.setStyle(_grid())
        story.append(table)
    else:
        story.append(
            Paragraph("No added, deleted, or lag-changed relationships.", body)
        )

    left_m = assess(comparison.left)
    right_m = {m.number: m for m in assess(comparison.right)}
    dcma_rows = [["#", "Metric", "Left", "Right", "Threshold", "L", "R"]]
    for m in left_m:
        rm = right_m[m.number]
        dcma_rows.append(
            [
                str(m.number),
                _clip(m.name, 33),
                display_value(m.value),
                display_value(rm.value),
                m.threshold,
                _pass(m.passed),
                _pass(rm.passed),
            ]
        )
    t3 = Table(
        dcma_rows,
        colWidths=[
            0.35 * inch,
            2.3 * inch,
            0.9 * inch,
            0.9 * inch,
            1.3 * inch,
            0.5 * inch,
            0.5 * inch,
        ],
    )
    style_cmds = _grid_cmds()
    for i, m in enumerate(left_m, start=1):
        rm = right_m[m.number]
        if m.passed is False or rm.passed is False:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), RED))
        elif m.passed is True and rm.passed is True:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), GREEN))
        else:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), GRAY))
    t3.setStyle(TableStyle(style_cmds))
    story.append(KeepTogether([Paragraph("DCMA 14 both files", h), t3]))

    story.append(Paragraph("Limits", h))
    story.append(
        Paragraph(
            "Dates and float are snapshots from the last P6 schedule of each file. "
            "A renamed Activity ID appears as a delete plus an add. "
            "Invalid-date checks use the stored data date. Missed tasks and BEI require an approved baseline; "
            "the critical-path test and CPLI need CPM recalculation. "
            "Unavailable checks are N/A. "
            "The Excel workbook is the system of record; this PDF is the cover sheet.",
            small,
        )
    )
    if comparison.warnings:
        story.append(Paragraph("Warnings", h))
        for w in comparison.warnings[:3]:
            story.append(Paragraph(f"• {escape(_clip(w,180))}", small))

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 18, letter[0], 18, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(
            0.65 * inch, letter[1] - 13, "XERCompare  ·  air-gapped  ·  MIT"
        )
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, letter[0], 22, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.drawString(
            0.65 * inch,
            8,
            f"{comparison.left.source.name}  →  {comparison.right.source.name}",
        )
        canvas.drawRightString(letter[0] - 0.65 * inch, 8, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return dest


def _clip(text: str, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def _pass(v: bool | None) -> str:
    if v is True:
        return "P"
    if v is False:
        return "F"
    return "—"


def _grid_cmds():
    return [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9BB7D4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]


def _grid(extra=None):
    cmds = _grid_cmds()
    if extra:
        cmds.extend(extra)
    return TableStyle(cmds)
