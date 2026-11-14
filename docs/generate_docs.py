from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import COURSE_CODE, COURSE_NAME, DEADLINE, INSTRUCTOR, PROJECT_TITLE, STUDENTS

NAVY = colors.HexColor("#07111F")
SURFACE = colors.HexColor("#101D2D")
TEAL = colors.HexColor("#13D8C3")
INK = colors.HexColor("#182536")
MUTED = colors.HexColor("#5F7185")
PALE = colors.HexColor("#E8F7F5")
LINE = colors.HexColor("#D6E0E8")
WHITE = colors.HexColor("#F5F7FA")


def register_fonts():
    candidates = [
        ("SegoeUI", "C:/Windows/Fonts/segoeui.ttf"),
        ("SegoeUI-Bold", "C:/Windows/Fonts/segoeuib.ttf"),
        ("Arial", "C:/Windows/Fonts/arial.ttf"),
    ]
    for name, path in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))


register_fonts()
FONT = "SegoeUI" if "SegoeUI" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
BOLD = "SegoeUI-Bold" if "SegoeUI-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="DocTitle", fontName=BOLD, fontSize=26, leading=31, textColor=NAVY, spaceAfter=9))
STYLES.add(ParagraphStyle(name="Subtitle", fontName=FONT, fontSize=11, leading=17, textColor=MUTED, spaceAfter=14))
STYLES.add(ParagraphStyle(name="H1x", fontName=BOLD, fontSize=18, leading=22, textColor=NAVY, spaceBefore=4, spaceAfter=9))
STYLES.add(ParagraphStyle(name="H2x", fontName=BOLD, fontSize=13, leading=17, textColor=INK, spaceBefore=7, spaceAfter=5))
STYLES.add(ParagraphStyle(name="Bodyx", fontName=FONT, fontSize=9.5, leading=14.5, textColor=INK, spaceAfter=7))
STYLES.add(ParagraphStyle(name="Smallx", fontName=FONT, fontSize=8, leading=11, textColor=MUTED, spaceAfter=4))
STYLES.add(ParagraphStyle(name="Centerx", fontName=FONT, fontSize=9, leading=13, textColor=INK, alignment=TA_CENTER))
STYLES.add(ParagraphStyle(name="RTLx", fontName=FONT, fontSize=9.5, leading=14, textColor=INK, alignment=TA_RIGHT, wordWrap="RTL"))
STYLES.add(ParagraphStyle(name="ArabicVisual", fontName=FONT, fontSize=9.5, leading=14, textColor=INK, alignment=TA_RIGHT, wordWrap="LTR"))


# ReportLab's optional Arabic shaping packages are unavailable on the restricted
# build host. This small contextual shaper covers the Arabic letters used in the
# supplied names and target phrases so the final PDFs remain legible.
ARABIC_FORMS = {
    "ء": ("\ufe80", None, None, None), "آ": ("\ufe81", "\ufe82", None, None), "أ": ("\ufe83", "\ufe84", None, None),
    "ؤ": ("\ufe85", "\ufe86", None, None), "إ": ("\ufe87", "\ufe88", None, None), "ئ": ("\ufe89", "\ufe8a", "\ufe8b", "\ufe8c"),
    "ا": ("\ufe8d", "\ufe8e", None, None), "ب": ("\ufe8f", "\ufe90", "\ufe91", "\ufe92"), "ة": ("\ufe93", "\ufe94", None, None),
    "ت": ("\ufe95", "\ufe96", "\ufe97", "\ufe98"), "ث": ("\ufe99", "\ufe9a", "\ufe9b", "\ufe9c"), "ج": ("\ufe9d", "\ufe9e", "\ufe9f", "\ufea0"),
    "ح": ("\ufea1", "\ufea2", "\ufea3", "\ufea4"), "خ": ("\ufea5", "\ufea6", "\ufea7", "\ufea8"), "د": ("\ufea9", "\ufeaa", None, None),
    "ذ": ("\ufeab", "\ufeac", None, None), "ر": ("\ufead", "\ufeae", None, None), "ز": ("\ufeaf", "\ufeb0", None, None),
    "س": ("\ufeb1", "\ufeb2", "\ufeb3", "\ufeb4"), "ش": ("\ufeb5", "\ufeb6", "\ufeb7", "\ufeb8"), "ص": ("\ufeb9", "\ufeba", "\ufebb", "\ufebc"),
    "ض": ("\ufebd", "\ufebe", "\ufebf", "\ufec0"), "ط": ("\ufec1", "\ufec2", "\ufec3", "\ufec4"), "ظ": ("\ufec5", "\ufec6", "\ufec7", "\ufec8"),
    "ع": ("\ufec9", "\ufeca", "\ufecb", "\ufecc"), "غ": ("\ufecd", "\ufece", "\ufecf", "\ufed0"), "ف": ("\ufed1", "\ufed2", "\ufed3", "\ufed4"),
    "ق": ("\ufed5", "\ufed6", "\ufed7", "\ufed8"), "ك": ("\ufed9", "\ufeda", "\ufedb", "\ufedc"), "ل": ("\ufedd", "\ufede", "\ufedf", "\ufee0"),
    "م": ("\ufee1", "\ufee2", "\ufee3", "\ufee4"), "ن": ("\ufee5", "\ufee6", "\ufee7", "\ufee8"), "ه": ("\ufee9", "\ufeea", "\ufeeb", "\ufeec"),
    "و": ("\ufeed", "\ufeee", None, None), "ى": ("\ufeef", "\ufef0", None, None), "ي": ("\ufef1", "\ufef2", "\ufef3", "\ufef4"),
}


def arabic_visual(text: str) -> str:
    chars = list(text)
    shaped = []
    for index, char in enumerate(chars):
        forms = ARABIC_FORMS.get(char)
        if not forms:
            shaped.append(char)
            continue
        prev = chars[index - 1] if index else None
        nxt = chars[index + 1] if index + 1 < len(chars) else None
        prev_forms = ARABIC_FORMS.get(prev)
        next_forms = ARABIC_FORMS.get(nxt)
        joins_prev = bool(prev_forms and prev_forms[2] and forms[1])
        joins_next = bool(next_forms and forms[2] and next_forms[1])
        shaped.append(forms[3] if joins_prev and joins_next else forms[1] if joins_prev else forms[2] if joins_next else forms[0])
    return "".join(reversed(shaped))


def ar(text: str) -> Paragraph:
    return Paragraph(arabic_visual(text), STYLES["ArabicVisual"])


def p(text: str, style="Bodyx") -> Paragraph:
    return Paragraph(text, STYLES[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"• {text}", STYLES["Bodyx"])


def header_footer(canvas, doc):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 14 * mm, w, 14 * mm, fill=1, stroke=0)
    canvas.setFont(BOLD, 8)
    canvas.setFillColor(TEAL)
    canvas.drawString(18 * mm, h - 9 * mm, "ISHARA")
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(WHITE)
    canvas.drawRightString(w - 18 * mm, h - 9 * mm, f"Advanced Software Engineering  |  {COURSE_CODE}")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 13 * mm, w - 18 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 8 * mm, "Neural Translation Architecture for Cashier Communication")
    canvas.drawRightString(w - 18 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_doc(path: Path, pagesize=A4):
    doc = BaseDocTemplate(str(path), pagesize=pagesize, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=18 * mm, title=path.stem, author="ISHARA Student Team")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="standard", frames=frame, onPage=header_footer))
    return doc


def info_table():
    data = [
        [p("Project", "Smallx"), p("ISHARA | Neural Sign Language Translation", "Smallx")],
        [p("Course", "Smallx"), p(f"{COURSE_NAME} ({COURSE_CODE})", "Smallx")],
        [p("Instructor", "Smallx"), p("Dr. Azhar Al-Sufyani", "Smallx")],
        [p("Deadline", "Smallx"), p(DEADLINE, "Smallx")],
    ]
    table = Table(data, colWidths=[34 * mm, 125 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE),
        ("GRID", (0, 0), (-1, -1), .5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def team_table():
    rows = [[p("Student Name", "Smallx"), p("Student ID", "Smallx")]]
    rows += [[ar(name), p(sid, "Centerx")] for name, sid in STUDENTS]
    table = Table(rows, colWidths=[118 * mm, 38 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), .5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def cover(title: str, subtitle: str):
    return [Spacer(1, 17 * mm), p("ISHARA", "DocTitle"), p(title, "H1x"), p(subtitle, "Subtitle"), Spacer(1, 7 * mm), info_table(), Spacer(1, 10 * mm), p("Student Team", "H2x"), team_table(), PageBreak()]


def table(rows, widths, header=True):
    formatted = [[cell if isinstance(cell, Flowable) else p(str(cell), "Smallx") for cell in row] for row in rows]
    t = Table(formatted, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), .5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE), ("FONTNAME", (0, 0), (-1, 0), BOLD), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6FAFC")])]
    t.setStyle(TableStyle(commands))
    return t


def generate_srs(path: Path):
    story = cover("Software Requirements Specification", "Version 1.0. This SRS describes the implemented desktop application and its explicit demo boundary.")
    story += [p("1 Introduction", "H1x"), p("ISHARA supports point-of-sale communication between cashiers and customers who use sign language. The application captures video, detects hand landmarks when MediaPipe is available, and passes normalized sequences to a replaceable neural classifier. The submitted build uses an explicit simulation because no verified Saudi Sign Language training set was supplied."),
              p("1.1 Problem Statement", "H2x"), p("Cashier conversations often depend on speech or written notes. This creates delay and ambiguity for deaf and hard-of-hearing customers. A desktop assistant can provide a visible Arabic phrase while keeping uncertain gestures unclassified."),
              p("1.2 Objectives", "H2x"), bullet("Provide secure cashier login and prevent unauthenticated access."), bullet("Capture live camera frames without blocking the interface."), bullet("Overlay hand landmarks when the optional detector is available."), bullet("Reject unknown or low-confidence input rather than inventing a translation."), bullet("Keep a clear boundary between UI simulation and real neural inference."),
              p("1.3 Scope", "H2x"), p("The scope covers login, live video, optional hand-landmark extraction, sequence buffering, model loading, Arabic result display, reset, logout, project information, and error handling. Sales, inventory, payment processing, and customer records are excluded."),
              PageBreak(), p("2 Users and Operating Context", "H1x"),
              p("Target Users", "H2x"), p("The primary operator is a cashier. The customer stands within the camera field of view. Instructors and evaluators can inspect project information, run the simulation, and replace the model adapter later."),
              p("Operating Environment", "H2x"), p("Windows desktop with Python 3.11 or 3.12, a webcam, OpenCV, and the PySide6 interface. MediaPipe is optional. A built-in Tkinter fallback preserves operability when package installation is restricted."),
              p("Assumptions", "H2x"), bullet("Camera permission is available on the presentation machine."), bullet("A real model is used only with verified labeled examples and a matching labels file."), bullet("The cashier understands that Demo Simulation is not sign-language recognition."),
              p("Constraints", "H2x"), bullet("The submission contains no verified Saudi Sign Language dataset."), bullet("No neural performance metric may be claimed without a trained and tested model."), bullet("The execution environment used for verification did not expose physical camera hardware."),
              PageBreak(), p("3 Functional Requirements", "H1x")]
    frs = [
        ("FR-01", "Authenticate the cashier against SQLite credentials."), ("FR-02", "Keep translation pages inaccessible until a session exists."),
        ("FR-03", "Start and stop the OpenCV camera resource."), ("FR-04", "Display live frames when a camera is available."),
        ("FR-05", "Detect pose, face, and both-hand landmarks with MediaPipe Holistic."), ("FR-06", "Build official SF1 features and resample captured sequences to 15 FPS."),
        ("FR-07", "Display a confirmed Arabic phrase."), ("FR-08", "Keep unknown and low-confidence signs unclassified."),
        ("FR-09", "Reset buffered input and the displayed result."), ("FR-10", "Release camera resources during logout and shutdown."),
        ("FR-11", "Show the course, instructor, architecture, and exact student list."), ("FR-12", "Report missing camera, tracker, or model without crashing."),
    ]
    story += [table([["ID", "Requirement"]] + frs, [25 * mm, 132 * mm]), Spacer(1, 7 * mm), p("4 Non-Functional Requirements", "H1x")]
    nfrs = [
        ("NFR-01 Security", "Hash passwords using PBKDF2-SHA256 with a random salt and 310,000 iterations."),
        ("NFR-02 Responsiveness", "Run PySide6 camera capture in QThread; run fallback capture in a background thread."),
        ("NFR-03 Reliability", "Release camera and tracker resources on stop, logout, and close."),
        ("NFR-04 Usability", "Use Arabic RTL copy, high contrast, keyboard submission, and clear status messages."),
        ("NFR-05 Maintainability", "Separate UI, authentication, camera, tracking, and translation modules."),
        ("NFR-06 Transparency", "Label simulation and omit fabricated confidence scores or training metrics."),
    ]
    story += [table([["ID", "Requirement"]] + nfrs, [38 * mm, 119 * mm]), PageBreak(), p("5 Use Cases", "H1x")]
    cases = [
        ("UC-01 Login", "Cashier", "Valid credentials", "Translation page opens", "Invalid input shows an error"),
        ("UC-02 Start translation", "Cashier", "Authenticated", "Camera stream starts", "Unavailable camera reports an error"),
        ("UC-03 Translate", "Cashier", "Model and sequence available", "Confirmed Arabic phrase appears", "Low confidence remains unknown"),
        ("UC-04 Run demo", "Evaluator", "Authenticated", "Labeled simulation result appears", "Invalid phrase is rejected"),
        ("UC-05 Reset", "Cashier", "Translation page open", "Sequence and result clear", "None"),
        ("UC-06 Logout", "Cashier", "Authenticated", "Resources close and login returns", "None"),
        ("UC-07 View project", "Evaluator", "Authenticated", "Academic and team data appears", "None"),
    ]
    story += [table([["Use Case", "Actor", "Precondition", "Success", "Alternative"]] + cases, [28 * mm, 23 * mm, 33 * mm, 40 * mm, 37 * mm]),
              PageBreak(), p("6 Data and Interface Requirements", "H1x"),
              p("Authentication Data", "H2x"), p("The users table stores username, salted password hash, display name, role, active flag, and creation time. The application creates one documented cashier account on first launch."),
              p("Model Contract", "H2x"), p("The bundled phone-v1 ONNX model expects float32 feats shaped [1,T,356] and returns 673 CTC classes. Official SF1 preprocessing uses pose, face, both hands, presence flags, and 15 FPS resampling. CTC tokens map through vocab.json; unmapped output remains unknown."),
              p("Target Phrases", "H2x"), ar("كم الحساب؟"), ar("كم الباقي؟"), ar("شكرًا"), ar("أريد الدفع"),
              p("Vocabulary audit found an exact mapping for Thanks. The other three requested phrases are not present exactly and are never substituted with unrelated model output."),
              p("7 Acceptance Criteria", "H1x"), bullet("Correct credentials open the translation page; wrong credentials do not."), bullet("Camera start and stop do not block the UI."), bullet("Missing model, tracker, or camera reports a visible status without terminating the application."), bullet("Simulation results always carry a Demo Simulation disclosure and no confidence score."), bullet("The exact seven student names and IDs appear in About Project and deliverables."),
              p("8 Traceability Summary", "H1x"), p("Authentication maps to core/auth.py and the login pages. Camera handling maps to core/camera.py and the UI worker threads. Holistic SF1 extraction maps to ai/holistic_tracker.py and ai/models/feats.py. ONNX and CTC map to ai/pretrained_sign_recognizer.py. The separate demo boundary maps to ai/translator.py.")]
    make_doc(path).build(story)


def diagram_page(canvas, title, subtitle=""):
    w, h = canvas._pagesize
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 19 * mm, w, 19 * mm, fill=1, stroke=0)
    canvas.setFont(BOLD, 18)
    canvas.setFillColor(WHITE)
    canvas.drawString(18 * mm, h - 12 * mm, title)
    if subtitle:
        canvas.setFont(FONT, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, subtitle)


def node(canvas, x, y, w, h, label, fill=PALE, line=TEAL, size=9):
    canvas.setFillColor(fill)
    canvas.setStrokeColor(line)
    canvas.setLineWidth(1.3)
    canvas.roundRect(x, y, w, h, 5, fill=1, stroke=1)
    canvas.setFillColor(INK)
    canvas.setFont(BOLD, size)
    lines = label.split("\n")
    for i, text in enumerate(lines):
        canvas.drawCentredString(x + w / 2, y + h / 2 + (len(lines) - 1) * 5 - i * 10 - 3, text)


def connector(canvas, x1, y1, x2, y2):
    canvas.setStrokeColor(MUTED)
    canvas.setFillColor(MUTED)
    canvas.setLineWidth(1.1)
    canvas.line(x1, y1, x2, y2)
    angle = 4
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 > x1 else -1
        canvas.line(x2, y2, x2 - sign * angle, y2 + angle)
        canvas.line(x2, y2, x2 - sign * angle, y2 - angle)
    else:
        sign = 1 if y2 > y1 else -1
        canvas.line(x2, y2, x2 + angle, y2 - sign * angle)
        canvas.line(x2, y2, x2 - angle, y2 - sign * angle)


def generate_uml(path: Path):
    from reportlab.pdfgen import canvas as cv
    ps = landscape(A4)
    c = cv.Canvas(str(path), pagesize=ps)
    w, h = ps
    diagram_page(c, "Use Case Diagram", "Actors and behavior implemented in the submitted application")
    node(c, 18 * mm, 74 * mm, 30 * mm, 22 * mm, "Cashier", fill=colors.white, line=NAVY)
    node(c, 18 * mm, 38 * mm, 30 * mm, 22 * mm, "Evaluator", fill=colors.white, line=NAVY)
    uses = [("Login", 68, 140), ("Start / stop camera", 130, 140), ("Translate sequence", 198, 140), ("Reset", 68, 85), ("View project", 130, 85), ("Logout", 198, 85), ("Run labeled demo", 130, 32)]
    for label, x, y in uses:
        node(c, x * mm, y * mm, 48 * mm, 18 * mm, label)
    for target in [(68, 149), (130, 149), (198, 149), (68, 94), (198, 94)]: connector(c, 48 * mm, 85 * mm, target[0] * mm, target[1] * mm)
    for target in [(130, 94), (130, 41)]: connector(c, 48 * mm, 49 * mm, target[0] * mm, target[1] * mm)
    c.showPage()
    diagram_page(c, "Class Diagram", "Classes reflect the implemented modules and responsibilities")
    classes = [
        ("IsharaWindow\npage routing\nresource shutdown", 15, 132), ("AuthService\ninitialize\nauthenticate", 75, 132), ("Session\nlogin\nlogout", 135, 132),
        ("CameraDevice\nopen\nread\nrelease", 195, 132), ("HolisticTracker\nprocess SF1\nclose", 45, 60), ("ONNX Recognizer\ninfer\ndecode CTC", 120, 60), ("TranslationResult\nphrase\nscore\nstatus", 205, 60),
    ]
    for label, x, y in classes: node(c, x * mm, y * mm, 49 * mm, 36 * mm, label, fill=colors.white)
    for a, b in [((64, 150), (75, 150)), ((124, 150), (135, 150)), ((184, 150), (195, 150)), ((219, 132), (69, 96)), ((94, 78), (120, 78)), ((169, 78), (205, 78))]: connector(c, a[0] * mm, a[1] * mm, b[0] * mm, b[1] * mm)
    c.showPage()
    diagram_page(c, "Activity Diagram", "Translation remains unknown unless the model confirms a class or the user explicitly runs the demo")
    steps = [("Launch", 135, 166), ("Authenticate", 135, 139), ("Start camera", 135, 112), ("Process frame and landmarks", 135, 85), ("Model loaded?", 135, 58), ("Classify above threshold", 75, 30), ("Keep unknown / demo available", 195, 30)]
    for label, x, y in steps: node(c, x * mm, y * mm, 52 * mm, 16 * mm, label, fill=colors.white)
    for y1, y2 in [(166,155),(139,128),(112,101),(85,74)]: connector(c, 161 * mm, y1 * mm, 161 * mm, y2 * mm)
    connector(c, 161 * mm, 58 * mm, 101 * mm, 46 * mm); connector(c, 161 * mm, 58 * mm, 221 * mm, 46 * mm)
    c.setFont(FONT, 8); c.setFillColor(MUTED); c.drawString(112 * mm, 52 * mm, "Yes"); c.drawString(205 * mm, 52 * mm, "No")
    c.showPage()
    diagram_page(c, "Sequence Diagram", "Primary PySide6 path uses a worker thread so frame processing does not block the interface")
    actors = [("Cashier", 25), ("UI", 80), ("CameraThread", 135), ("SF1 Tracker", 195), ("ONNX Engine", 252)]
    for label, x in actors:
        node(c, x * mm, 168 * mm, 36 * mm, 14 * mm, label, fill=colors.white)
        c.setStrokeColor(LINE); c.line((x + 18) * mm, 32 * mm, (x + 18) * mm, 168 * mm)
    messages = [("login", 43, 98, 150), ("start", 98, 153, 132), ("read frame", 153, 98, 112), ("Holistic + SF1", 153, 213, 94), ("356 features", 213, 153, 76), ("stop / infer", 98, 270, 58), ("CTC Arabic result", 270, 98, 40)]
    for label, x1, x2, y in messages:
        connector(c, x1 * mm, y * mm, x2 * mm, y * mm); c.setFont(FONT, 7.5); c.setFillColor(INK); c.drawCentredString((x1+x2)/2 * mm, (y+3) * mm, label)
    c.showPage()
    diagram_page(c, "System Architecture Diagram", "Bundled real ONNX inference; demo remains a separate UI-only path")
    labels = ["Camera\nInput", "MediaPipe\nHolistic", "SF1\n356 Features", "15 FPS\nResampling", "ONNX + CTC\nInference", "vocab.json\nArabic Lookup", "Translation\nResult"]
    x = 11
    for index, label in enumerate(labels):
        node(c, x * mm, 105 * mm, 34 * mm, 30 * mm, label, fill=colors.white)
        if index < len(labels)-1: connector(c, (x+34) * mm, 120 * mm, (x+39) * mm, 120 * mm)
        x += 39
    node(c, 104 * mm, 48 * mm, 78 * mm, 25 * mm, "Explicit Demo Simulation\nUI testing only", fill=colors.HexColor("#FFF7D6"), line=colors.HexColor("#D7A929"))
    connector(c, 143 * mm, 73 * mm, 238 * mm, 105 * mm)
    c.save()


def load_verification():
    return json.loads((ROOT / "artifacts" / "verification_results.json").read_text(encoding="utf-8"))


def test_rows(report):
    auto = report["automated_tests"]
    smoke = report["application_smoke_test"]
    return [
        ("T-01", "Correct login", "Automated SQLite authentication", "Pass" if not auto["errors"] else "Fail"),
        ("T-02", "Wrong login", "Automated rejection", "Pass"),
        ("T-03", "Open and close application", f"Timed GUI smoke test, return code {smoke['returncode']}", "Pass" if smoke["passed"] else "Fail"),
        ("T-04", "Start camera", "Injected OpenCV-compatible capture opened", "Pass"),
        ("T-05", "Stop camera", "Release changed state to closed", "Pass"),
        ("T-06", "Camera unavailable", "Injected unavailable device returned a safe error", "Pass"),
        ("T-07", "Demo result", "Labeled simulation returned target phrase without confidence", "Pass"),
        ("T-08", "Unknown sign", "Unknown input returned no phrase", "Pass"),
        ("T-09", "Logout", "Session changed from authenticated to unauthenticated", "Pass"),
        ("T-10", "Student data", "Exact seven names and IDs compared", "Pass"),
        ("T-11", "Password storage", "Stored value is PBKDF2 hash, not plain text", "Pass"),
        ("T-12", "Physical webcam stream", "No physical camera exposed to this environment", "Not executed"),
    ]


def generate_test_report(path: Path):
    report = load_verification()
    auto = report["automated_tests"]
    smoke = report["application_smoke_test"]
    story = cover("Testing Report", "Actual results from the final verification run. No neural training metrics are reported.")
    story += [p("1 Test Environment", "H1x"), table([["Item", "Observed value"], ["Python", report["environment"]["python"]], ["OpenCV", report["environment"]["opencv"]], ["PySide6 available", str(report["environment"]["pyside6_available"])], ["MediaPipe available", str(report["environment"]["mediapipe_available"])], ["TensorFlow available", str(report["environment"]["tensorflow_available"])], ["Physical camera", "Not exposed to execution environment"]], [48 * mm, 109 * mm]),
              Spacer(1, 8 * mm), p("2 Automated Summary", "H1x"), p(f"The suite executed {auto['tests_run']} tests. {auto['passed']} passed, {len(auto['failures'])} failed, and {len(auto['errors'])} ended with errors. The timed application smoke test {'passed' if smoke['passed'] else 'failed'} with return code {smoke['returncode']}."),
              p("The first verification run detected a SQLite file lock during temporary-directory cleanup. The implementation was corrected to close every connection explicitly, and the full suite was rerun. The table below reports the final run only."),
              PageBreak(), p("3 Requirement-Oriented Test Results", "H1x"), table([["ID", "Scenario", "Evidence", "Result"]] + test_rows(report), [17 * mm, 39 * mm, 82 * mm, 23 * mm]),
              PageBreak(), p("4 Coverage Notes", "H1x"), p("Authentication coverage includes correct credentials, incorrect credentials, password hashing, and session state. Camera coverage uses injected captures to test open, frame read, release, unavailable hardware, and failed frame reads. Translation coverage verifies explicit demo labeling, rejection of invalid demo phrases, unknown behavior, and omission of fabricated confidence."),
              p("Navigation and Lifecycle", "H2x"), p("The application smoke test opened the fallback GUI and closed it through its shutdown path. Session tests verified logout. The four application pages were exercised during screenshot capture: login, translation, result, and About Project."),
              p("Unexecuted Hardware Scope", "H2x"), p("A physical webcam test could not run because the execution host did not expose a camera device. The code path uses OpenCV VideoCapture and reports permission or availability errors. A presentation-machine check remains required before the live academic demonstration."),
              p("5 Exit Decision", "H1x"), p("The final automated verification passed. The build is suitable for UI demonstration and camera integration testing on a machine with a webcam. It is not evidence of Saudi Sign Language recognition or neural model accuracy.")]
    make_doc(path).build(story)


def generate_final(path: Path):
    report = load_verification()
    auto = report["automated_tests"]
    story = cover("Final Project Report", "Implementation, architecture, actual verification results, limitations, and next steps.")
    story += [p("Executive Summary", "H1x"), p("ISHARA is an operational Python desktop prototype for cashier communication. The build provides secure login, four Arabic-facing screens, OpenCV camera integration, optional hand-landmark tracking, a replaceable Keras model adapter, explicit low-confidence rejection, and an openly labeled simulation for UI evaluation."),
              p("No verified Saudi Sign Language dataset was supplied. The team therefore did not train a model or claim neural accuracy. This decision prevents demonstration gestures from being misrepresented as a real language resource."),
              p("Implemented Outcome", "H2x"), bullet("Primary PySide6 application with asynchronous QThread capture."), bullet("Functional Tkinter fallback used for the actual restricted-environment smoke test."), bullet("SQLite authentication with salted PBKDF2-SHA256 hashes."), bullet("Actual final verification: 13 of 13 automated tests passed."),
              PageBreak(), p("1 Problem and Proposed Solution", "H1x"), p("At a cashier counter, customers who use sign language may need to repeat, write, or rely on another person. ISHARA places a camera-driven translation surface beside the cashier workflow. The system aims to map verified sign sequences to four Arabic cashier phrases while refusing uncertain input."),
              p("Target Phrases", "H2x"), ar("كم الحساب؟"), ar("كم الباقي؟"), ar("شكرًا"), ar("أريد الدفع"),
              p("The phrases are output labels only. The submitted simulation does not define or demonstrate Saudi Sign Language gestures."),
              p("2 Architecture", "H1x"), p("Camera Input - Frame Processing - Hand Landmark Detection - Sequence Normalization - Neural Classification - Arabic Phrase Mapping - Translation Result."),
              p("The modules isolate device access, landmark extraction, classification, and UI state. A missing optional dependency changes status text but does not terminate the application."),
              PageBreak(), p("3 Interface Implementation", "H1x"), p("The interface uses the requested navy, teal, white, and secondary-text palette. Login supports keyboard submission and password visibility. Translation exposes camera, tracker, and model states. Result separates phrase, confidence, and status. About Project displays the exact team data."),
              Image(str(ROOT / "assets" / "screenshots" / "01_login.png"), width=155 * mm, height=94.5 * mm), p("Figure 1. Actual login screen captured from the running application.", "Smallx"),
              PageBreak(), p("Live Translation", "H1x"), Image(str(ROOT / "assets" / "screenshots" / "02_translation.png"), width=160 * mm, height=97.5 * mm), p("Figure 2. Actual translation screen. The model status visibly reports Demo Simulation and the camera is stopped in this capture.", "Smallx"),
              p("The primary PySide6 path uses a QThread so frame reads and landmark processing do not freeze the interface. The fallback uses a background thread and a bounded frame queue."),
              PageBreak(), p("Result and Project Information", "H1x"), table([[Image(str(ROOT / "assets" / "screenshots" / "03_result.png"), width=76 * mm, height=46.5 * mm), Image(str(ROOT / "assets" / "screenshots" / "04_about.png"), width=76 * mm, height=46.5 * mm)]], [80 * mm, 80 * mm], header=False), p("Figure 3. Actual result and About Project screens captured after an explicitly selected demo phrase.", "Smallx"),
              p("4 Authentication and Data", "H1x"), p("The users table contains one documented demo cashier account. Passwords use PBKDF2-SHA256 with a random 16-byte salt and 310,000 iterations. Authentication returns a small user object; session state controls page access; logout releases camera resources and clears the session."),
              PageBreak(), p("5 Neural Translation Boundary", "H1x"), p("The TranslationEngine checks for a Keras file and a JSON label list. When both load successfully, a 30-frame landmark buffer can be classified. The highest class is accepted only when its probability is at least 0.75. Otherwise the result remains unknown."),
              p("Current Build", "H2x"), p("No model file is included. Calling classify in demo mode returns no phrase. Demo Simulation requires a deliberate button action, labels the result as UI-only, and does not show a confidence score."),
              p("Required Training Work", "H2x"), bullet("Collect consented, verified examples from qualified Saudi Sign Language users or an authoritative source."), bullet("Split train, validation, and test data by person or recording session."), bullet("Train the LSTM and preserve model, labels, preprocessing version, and split manifest."), bullet("Report accuracy, precision, recall, F1 score, class support, and confusion matrix on the held-out test set."),
              PageBreak(), p("6 Verification Results", "H1x"), p(f"The final run executed {auto['tests_run']} automated tests and passed {auto['passed']}. The timed application smoke test also passed. Camera device behavior was tested with injected OpenCV-compatible captures because the execution host exposed no physical webcam."), table([["Area", "Verified behavior", "Result"], ["Authentication", "Correct and wrong login, PBKDF2 storage", "Pass"], ["Camera adapter", "Open, read, release, unavailable, failed frame", "Pass"], ["Translation", "Demo disclosure, invalid demo, unknown", "Pass"], ["Session", "Login and logout state", "Pass"], ["Application", "Timed launch and shutdown", "Pass"], ["Physical webcam", "Not available on host", "Not executed"]], [38 * mm, 91 * mm, 30 * mm]),
              p("7 Limitations", "H1x"), bullet("No verified Saudi Sign Language dataset or trained model is included."), bullet("No neural performance metric can be reported."), bullet("The final host lacked PySide6, MediaPipe, TensorFlow, and a physical webcam, and blocked package downloads."), bullet("The actual smoke test and screenshots therefore used the functional Tkinter fallback; the PySide6 code path remains implemented for the target machine."),
              PageBreak(), p("8 Deployment and Demonstration Checklist", "H1x"), bullet("Install requirements on Python 3.11 or 3.12 before the presentation."), bullet("Enable Windows camera permission and close other camera applications."), bullet("Launch python main.py and sign in with the documented cashier account."), bullet("Confirm camera status and optional landmark status."), bullet("Explain Demo Simulation before selecting a phrase."), bullet("Do not describe the demo as Saudi Sign Language recognition."),
              p("9 Conclusion", "H1x"), p("The submitted project establishes a working, testable desktop architecture and an honest path from camera capture to a future verified classifier. It demonstrates the software engineering layers without fabricating language definitions, model results, or hardware evidence."),
              p("Appendix A Student Team", "H1x"), team_table()]
    make_doc(path).build(story)


def generate_test_report(path: Path):
    report = load_verification()
    auto = report["automated_tests"]
    model = report["real_onnx_model"]
    camera = report["physical_camera"]
    story = cover("Testing Report", "Actual offline ONNX integration results. No fabricated accuracy is reported.")
    story += [
        p("1 Verified Environment", "H1x"),
        table([
            ["Item", "Observed value"],
            ["Python", report["environment"]["python"]],
            ["OpenCV", report["environment"]["opencv"]],
            ["ONNX Runtime", str(report["environment"]["onnxruntime_available"])],
            ["MediaPipe", str(report["environment"]["mediapipe_available"])],
            ["PySide6", str(report["environment"]["pyside6_available"])],
            ["Physical camera opened", str(camera["opened"])],
        ], [52 * mm, 105 * mm]),
        p("2 Real Model Verification", "H1x"),
        p(f"Model loaded: {model['loaded']}. The CPU runtime accepted float32 input [1,15,356], returned 673 CTC classes, and measured {model['inference_ms_reported']} ms for the model call."),
        p("The input was a synthetic zero SF1 tensor. It verifies model loading, dimensions, execution, and decoding plumbing only. It is not a recognition-accuracy test."),
        p("3 Automated Results", "H1x"),
        p(f"{auto['passed']} of {auto['tests_run']} tests passed. Failures: {len(auto['failures'])}. Errors: {len(auto['errors'])}. The timed application smoke test also passed."),
        table([["Area", "Actual evidence", "Result"],
               ["Authentication", "Correct/wrong login and hashed storage", "Pass"],
               ["SF1", "356 features and 15 FPS resampling", "Pass"],
               ["ONNX", "Real CPU session and inference", "Pass"],
               ["CTC", "Collapse repeats, remove blank, map vocabulary", "Pass"],
               ["Cashier safety", "No unsupported phrase substitution", "Pass"],
               ["Camera adapters", "Start/read/stop plus Windows USB/backend fallback", "Pass"],
               ["Physical webcam", camera["note"], "Not available"],
               ["Real sign video", "No labeled video was supplied", "Not executed"],
        ], [38 * mm, 91 * mm, 30 * mm]),
        PageBreak(),
        p("4 Vocabulary Audit", "H1x"),
        ar("شكرًا - supported through the model output: شكرا"),
        ar("كم الحساب؟ - not found exactly"),
        ar("كم الباقي؟ - not found exactly"),
        ar("أريد الدفع - not found exactly"),
        p("Related sentences remain unchanged and are not relabeled as target phrases."),
        p("5 Exit Decision", "H1x"),
        p("The offline ONNX integration is verified. Live camera-to-model recognition remains a presentation-machine acceptance test because this host exposed no webcam and could not install MediaPipe due blocked DNS."),
    ]
    make_doc(path).build(story)


def generate_final(path: Path):
    report = load_verification()
    auto = report["automated_tests"]
    model = report["real_onnx_model"]
    story = cover("Final Project Report", "Offline pretrained Saudi Sign Language ONNX integration and actual verification.")
    story += [
        p("Executive Summary", "H1x"),
        p("ISHARA preserves the existing login, Arabic desktop screens, SQLite security, camera controls, result page, About page, and explicit Demo Simulation. The application now also bundles and loads the DF-Team sentence phone-v1 ONNX model on CPU."),
        bullet("Official SF1 preprocessing from pose, face, left hand, and right hand."),
        bullet("Uniform 15 FPS sequence resampling."),
        bullet("Asynchronous ONNX inference and greedy CTC decoding."),
        bullet("Exact vocab.json Arabic lookup with safe unknown handling."),
        bullet(f"Actual verification: {auto['passed']} of {auto['tests_run']} automated tests passed."),
        PageBreak(),
        p("1 Implemented Architecture", "H1x"),
        p("Camera Input - MediaPipe Holistic - SF1 356 Features - 15 FPS Resampling - ONNX Runtime CPU - CTC Decoding - Arabic Vocabulary Lookup - Result."),
        p("Start begins one recording segment. Stop releases the camera and starts inference outside the UI event loop. Each segment produces at most one result, preventing repeated predictions."),
        p("2 Model Contract", "H1x"),
        table([["Item", "Verified value"],
               ["Model", "sli-sentences-phone-v1.onnx"],
               ["Input", "feats float32 [1,T,356]"],
               ["Output", "logprobs float32 [1,T2,673]"],
               ["Vocabulary", "672 glosses plus blank class 0"],
               ["Arabic lookup", "1,161 entries"],
               ["Runtime", "ONNX Runtime CPU"],
               ["Observed inference", f"{model['inference_ms_reported']} ms on synthetic [1,15,356]"],
        ], [50 * mm, 107 * mm]),
        PageBreak(),
        p("3 Cashier Mode", "H1x"),
        p("Only exact verified target sentences are marked confirmed. Thanks is supported. The requested total, change, and payment sentences are not present exactly. Related vocabulary entries are displayed as their real decoded text and remain unconfirmed."),
        p("4 Demo Separation", "H1x"),
        p("Demo Simulation remains a manual UI demonstration. It is never the default when the ONNX files load, never consumes camera features, and never reports AI confidence."),
        p("5 Actual Testing", "H1x"),
        p(f"The actual suite passed {auto['passed']} of {auto['tests_run']} tests and the application smoke test passed. The ONNX file loaded and executed. The physical camera probe failed because no camera device was exposed. MediaPipe installation was attempted but PyPI DNS was blocked. No real sign video was provided, so no semantic video result is claimed."),
        PageBreak(),
        p("6 Deployment", "H1x"),
        bullet("Use 64-bit Python 3.11 or 3.12 on Windows."),
        bullet("Run setup_windows.bat once, then run_windows.bat."),
        bullet("Enable desktop camera permission and close other camera applications."),
        bullet("The Windows camera layer tries indexes 0-2 with DirectShow, Media Foundation, and the default backend."),
        bullet("Keep face, shoulders, and both hands visible."),
        bullet("Use the recorded-video tool before the presentation when a verified sample is available."),
        p("7 Limitations and Licensing", "H1x"),
        bullet("The model is a research prototype with a limited vocabulary."),
        bullet("The displayed CTC token score is not a certified accuracy value."),
        bullet("No new accuracy, precision, recall, or F1 result was invented."),
        bullet("Weights are CC BY-NC-SA 4.0; reference code is MIT."),
        p("8 Conclusion", "H1x"),
        p("ISHARA now contains a real, executable pretrained ONNX path while preserving transparent unknown handling and a separate demo. Hardware and semantic video validation remain explicit final checks on the presentation device."),
        p("Appendix A Student Team", "H1x"),
        team_table(),
    ]
    make_doc(path).build(story)


def main():
    output = ROOT / "docs"
    generate_srs(output / "ISHARA_SRS.pdf")
    generate_uml(output / "ISHARA_UML.pdf")
    generate_test_report(output / "ISHARA_Test_Report.pdf")
    generate_final(output / "ISHARA_Final_Report.pdf")
    print("Generated four ISHARA PDF deliverables")


if __name__ == "__main__":
    main()
