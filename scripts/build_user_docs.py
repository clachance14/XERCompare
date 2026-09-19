"""Build readable PDF instructions and the complete, locally supplied notices."""

from pathlib import Path
import tomllib

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#16324F")
BLUE = colors.HexColor("#2563A6")
INK = colors.HexColor("#172B42")
MUTED = colors.HexColor("#526579")
PALE = colors.HexColor("#EEF4FA")
WIDTH = letter[0] - 96


def build_user_docs(root: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "Documents").mkdir(exist_ok=True)
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    fonts = Path(reportlab.__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("Guide", str(fonts / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("GuideBold", str(fonts / "VeraBd.ttf")))
    pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="GuideBold")
    styles = {
        "body": ParagraphStyle(
            "Body",
            fontName="Guide",
            fontSize=10.5,
            leading=15,
            textColor=INK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            fontName="Guide",
            fontSize=9,
            leading=13,
            textColor=MUTED,
            spaceAfter=6,
        ),
        "title": ParagraphStyle(
            "Title",
            fontName="GuideBold",
            fontSize=27,
            leading=33,
            textColor=NAVY,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "Heading",
            fontName="GuideBold",
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=13,
            spaceAfter=8,
        ),
        "step": ParagraphStyle(
            "Step",
            fontName="GuideBold",
            fontSize=12,
            leading=17,
            textColor=BLUE,
            spaceAfter=3,
        ),
        "number": ParagraphStyle(
            "Number", fontName="GuideBold", fontSize=21, leading=27, textColor=BLUE
        ),
    }

    def p(text, kind="body"):
        return Paragraph(text, styles[kind])

    def callout(title, body):
        table = Table([[p(title, "step")], [p(body)]], colWidths=[WIDTH])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 14),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                    ("TOPPADDING", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
                ]
            )
        )
        return KeepTogether([table, Spacer(1, 10)])

    def step(number, title, body):
        table = Table(
            [[p(str(number), "number"), [p(title, "step"), p(body)]]],
            colWidths=[34, WIDTH - 34],
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            )
        )
        return table

    def grid(rows, first_width=142):
        table = Table(
            [[p(a, "step"), p(b)] for a, b in rows],
            colWidths=[first_width, WIDTH - first_width],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PALE, colors.white]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 27, letter[0], 27, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("GuideBold", 9)
        canvas.drawString(48, letter[1] - 18, "XERCOMPARE")
        canvas.setFont("Guide", 8)
        canvas.drawRightString(
            letter[0] - 48, letter[1] - 18, "LOCAL FILES  |  OFFLINE"
        )
        canvas.setStrokeColor(colors.HexColor("#D8E1EB"))
        canvas.line(48, 38, letter[0] - 48, 38)
        canvas.setFillColor(MUTED)
        canvas.drawString(48, 25, f"XERCompare {version}  |  Windows")
        canvas.drawRightString(letter[0] - 48, 25, str(doc.page))
        canvas.restoreState()

    guide = destination / "START HERE.pdf"
    story = [
        p("Start here", "title"),
        p(
            "Compare two Primavera P6 exports.<br/>Get an Excel workbook and a short PDF summary."
        ),
        callout(
            "The file to open: XERCompare.exe",
            "Double-click the app. There is no installer and no command to type. "
            "Allow a few moments for the window to appear.",
        ),
        step(
            1,
            "Extract the ZIP",
            "Right-click <b>XERCompare-Windows.zip</b> and choose "
            "<b>Extract All</b>. Open the extracted folder. Do this once; afterward, open the app from that folder.",
        ),
        step(
            2,
            "Open XERCompare.exe",
            "Double-click <b>XERCompare.exe</b>. "
            "If Windows hides file extensions, it may appear as <b>XERCompare</b> with type <b>Application</b>.",
        ),
        step(
            3,
            "Choose your two XER files",
            "Next to <b>Older / baseline XER</b>, click <b>Browse...</b> "
            "and choose the earlier export. Next to <b>Revised / update XER</b>, choose the later export.",
        ),
        step(
            4,
            "Choose a folder and compare",
            "Choose an <b>Output folder</b>, then click "
            "<b>Compare schedules</b>. Watch the progress message. When it finishes, click <b>Open Excel</b> or <b>Open PDF</b>.",
        ),
        p("What you need", "heading"),
        p(
            "<b>64-bit Windows and two .xer files.</b> Python, Primavera P6, an account, "
            "and an internet connection are not needed to run XERCompare."
        ),
        p(
            "First try? Use the two sample exports in <b>Example files</b>. See page 4.",
            "small",
        ),
        PageBreak(),
        p("Read your results", "title"),
        p(
            "Each run creates a new dated folder inside the output folder you chose. "
            "Your earlier reports and original XER files are kept."
        ),
        grid(
            [
                (
                    "Open Excel",
                    "Opens <b>compare.xlsx</b>: the full set of 39 worksheets, with filters and changed revised cells highlighted.",
                ),
                (
                    "Open PDF",
                    "Opens <b>compare.pdf</b>: a short summary of counts, early-finish movement, quality checks and warnings.",
                ),
                (
                    "Open folder",
                    "Shows the saved reports in File Explorer so you can find, copy or share them.",
                ),
                (
                    "Report catalog",
                    "Previews up to 200 rows per worksheet inside the app. The Excel workbook contains every row.",
                ),
                (
                    "Warnings",
                    "Shows file-reading and comparison issues that may affect your interpretation.",
                ),
            ]
        ),
        p("Where to look first", "heading"),
        p(
            "Start with <b>Summary</b>, then <b>Changes Combined</b>. Use the separate sheets "
            "for added/deleted tasks, dates, progress, durations, calendars, constraints, float, "
            "relationships, resources and user-defined fields (UDFs)."
        ),
        p("What the change labels mean", "heading"),
        grid(
            [
                (
                    "Progress",
                    "Actual dates, remaining duration, percent complete or status changed.",
                ),
                (
                    "Revision",
                    "A description, original duration, calendar, constraint or other planned field changed.",
                ),
                ("Date", "Stored schedule dates or float changed."),
                ("Both", "The same activity has progress and revision changes."),
            ],
            first_width=95,
        ),
        p(
            "Numbers: <b>one decimal</b> for measurements and <b>two decimals</b> for costs. "
            "Counts stay whole numbers. Excel keeps the underlying precision; a small change can "
            "still be highlighted when both displayed values round to the same number.",
            "small",
        ),
        PageBreak(),
        p("Advanced review", "title"),
        p("See the activities behind a quality flag", "heading"),
        p(
            "After comparing, open <b>Quality findings</b>. Select a check and click <b>Show affected activities</b>. "
            "The report lists base and revised values, the related activity where relevant, and an explanation. "
            "Use <b>Search report</b> to find an Activity ID or text. Search covers the complete report; previews show up to 200 matching rows."
        ),
        p("Choose your own check limits", "heading"),
        p(
            "Open <b>Quality settings</b>, name your profile, change the cutoffs or disable checks, then click <b>Apply settings</b>. "
            "Run the comparison again. <b>Save profile</b> keeps a local JSON file you can reload or share; "
            "<b>Load profile</b> applies a saved profile. Settings do not change old reports. "
            "The <b>DCMA 14</b> sheet always uses conventional thresholds; custom results are in <b>Quality Checks</b>."
        ),
        p("Compare several updates", "heading"),
        step(
            1,
            "Open Update history",
            "Choose a folder containing the exports you want to compare. Choose an optional baseline and an output folder.",
        ),
        step(
            2,
            "Load exports and review",
            "Check the project names, data dates and order. Use <b>Move earlier</b> or <b>Move later</b> when needed. "
            "Equal data dates cannot establish chronology. Check the confirmation box after reviewing.",
        ),
        step(
            3,
            "Build history reports",
            "Open <b>trends and charts</b> for the history workbook. The <b>Comparisons</b> sheet links to each full comparison. "
            "Every comparison folder includes Excel and PDF. The optional baseline is compared with each other export.",
        ),
        callout(
            "Read these as review findings",
            "Out-of-sequence and dangling-event flags need review. Calendar comparison reads exported workweeks and exceptions; "
            "it does not reschedule. Milestone movement uses elapsed 24-hour days. Missed planned finish is a stored-target-date proxy, not a baseline certification.",
        ),
        PageBreak(),
        p("Try it &amp; get help", "title"),
        p("Try the included example", "heading"),
        p(
            "In <b>Example files</b>, use <b>base.xer</b> as the older file and <b>revised.xer</b> "
            "as the update. Choose an output folder and compare. These are synthetic examples, "
            "not real project data. You should see <b>1 added, 1 deleted, 2 modified and 1 unchanged activity</b>."
        ),
        p("Quick answers", "heading"),
        grid(
            [
                (
                    "Can't see the output buttons?",
                    "Scroll down on the comparison page, or make the window taller.",
                ),
                (
                    "Comparison won't start?",
                    "Choose two existing .xer files and an output folder you can write to. Read the message below the progress bar.",
                ),
                (
                    "Need to stop?",
                    "Click <b>Cancel</b>. It stops after the current processing step and removes unfinished reports.",
                ),
                (
                    "Report won't open?",
                    "Use <b>Open folder</b>. Opening an Excel or PDF file needs a compatible viewer. The app's report preview works without Excel.",
                ),
                (
                    "Want a desktop shortcut?",
                    "Right-click XERCompare.exe, choose <b>Show more options</b> if shown, then <b>Send to &gt; Desktop (create shortcut)</b>.",
                ),
            ],
            first_width=159,
        ),
        p("How the comparison works", "heading"),
        p(
            "XERCompare reads both local files, matches activities by their visible Activity ID, "
            "compares stored values, then saves the reports. It does not upload your files or recalculate the schedule."
        ),
        p(
            "Only the first project in each XER is compared. A renamed Activity ID appears as a deletion "
            "and an addition. Driving Path Change uses stored total float at or below zero as an approximation. "
            "Unavailable DCMA quality checks show N/A with a reason.",
            "small",
        ),
        p(
            'Feedback: <link href="https://github.com/clachance14/XERCompare/issues/new/choose" color="#2563A6"><b>Report a problem or suggest a feature</b></link> '
            'or <link href="https://github.com/clachance14/XERCompare/discussions" color="#2563A6"><b>ask a question</b></link>. '
            "GitHub feedback is public and needs an account. Include your app and Windows versions; "
            "keep confidential XERs, reports and identifying screenshots private.",
            "small",
        ),
        p(
            'Share the complete ZIP or visit <link href="https://github.com/clachance14/XERCompare" color="#2563A6">github.com/clachance14/XERCompare</link>. '
            "License notices are in <b>Documents / Licenses.pdf</b>. Feedback links use your browser; the app runs offline.",
            "small",
        ),
    ]
    doc = SimpleDocTemplate(
        str(guide),
        pagesize=letter,
        leftMargin=48,
        rightMargin=48,
        topMargin=49,
        bottomMargin=50,
        title="XERCompare - Start Here",
        author="XERCompare",
        pageCompression=1,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    notices = (root / "dist/THIRD_PARTY_NOTICES.txt").read_text(encoding="utf-8")
    licenses = destination / "Documents/Licenses.pdf"
    legal_style = ParagraphStyle(
        "License text", fontName="Courier", fontSize=8.2, leading=10.5, textColor=INK
    )
    legal_story = [
        p("Licenses &amp; notices", "title"),
        p("XERCompare and the software included with it", "heading"),
        p(
            "The following pages preserve the complete license and copyright notices "
            "supplied with this build. Only line wrapping and page layout have changed."
        ),
        p("For everyday instructions, open START HERE.pdf.", "small"),
        Spacer(1, 12),
        Preformatted(notices, legal_style, maxLineLength=100),
    ]
    doc = SimpleDocTemplate(
        str(licenses),
        pagesize=letter,
        leftMargin=48,
        rightMargin=48,
        topMargin=49,
        bottomMargin=50,
        title="XERCompare - Licenses and Notices",
        author="XERCompare",
        pageCompression=1,
    )
    doc.build(legal_story, onFirstPage=footer, onLaterPages=footer)
    return guide, licenses


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    for document in build_user_docs(root, root / "dist/release"):
        print(document)
