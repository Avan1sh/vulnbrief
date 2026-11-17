"""Build static submission assets; requires reportlab (documentation-only dependency).

The final PNG can be rendered from architecture.pdf using pdftoppm.
This script does not invoke an LLM or manufacture sample runs.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

BASE = Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
NAVY = HexColor("#17243d")
PURPLE = HexColor("#6755c8")
GRAY = HexColor("#526078")


def architecture():
    c = canvas.Canvas(str(DOCS / "architecture.pdf"), pagesize=(1110, 650))
    c.setFillColor(HexColor("#f6f8fc")); c.rect(0, 0, 1110, 650, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 26)
    c.drawString(55, 604, "VulnBrief")
    c.setFont("Helvetica", 12); c.setFillColor(GRAY)
    c.drawString(55, 581, "One LLM agent. Live source evidence. Observable recovery.")

    def box(x, y, title, subtitle, h=65, accent=False):
        c.setFillColor(PURPLE if accent else white)
        c.setStrokeColor(HexColor("#d9deeb")); c.roundRect(x, y, 180, h, 12, fill=1, stroke=1)
        c.setFillColor(white if accent else NAVY); c.setFont("Helvetica-Bold", 13)
        c.drawString(x + 14, y + h - 24, title)
        c.setFont("Helvetica", 10)
        for i, line in enumerate(subtitle.split("\n")):
            c.drawString(x + 14, y + h - 42 - i * 14, line)

    def arrow(points, label=None, label_xy=None):
        c.setStrokeColor(PURPLE); c.setLineWidth(1.7)
        path = c.beginPath(); path.moveTo(*points[0])
        for point in points[1:]: path.lineTo(*point)
        c.drawPath(path)
        x,y=points[-1]; px,py=points[-2]
        if x == px:
            sign = 1 if y > py else -1
            c.line(x,y,x-4,y-sign*7); c.line(x,y,x+4,y-sign*7)
        else:
            sign = 1 if x > px else -1
            c.line(x,y,x-sign*7,y-4); c.line(x,y,x-sign*7,y+4)
        if label:
            c.setFillColor(GRAY); c.setFont("Helvetica", 10); c.drawString(*label_xy, label)

    box(55, 490, "LOCAL UI / CLI", "Goal + CSV / JSON inventory")
    box(325, 490, "PLAN", "LLM: steps + assumptions", accent=True)
    box(595, 490, "DECIDE", "LLM selects function calls", accent=True)
    box(865, 490, "DISPATCH", "Validate scope + arguments")
    box(865, 315, "SIX DATA TOOLS", "Context / CVE / KEV / EPSS\nVendor advisory / asset versions", h=100)
    box(595, 325, "OBSERVE", "Evidence IDs or typed errors")
    box(325, 325, "REPORT + REVIEW", "Schema + source-grounding LLM")
    box(55, 325, "REPORTS + HISTORY", "JSON / Markdown / local SQLite")
    for x in (235,505,775): arrow([(x,522),(x+90,522)])
    arrow([(955,490),(955,415)])
    arrow([(865,357),(775,357)])
    arrow([(685,390),(685,490)], "Inspect / revise", (695,438))
    arrow([(595,510),(550,510),(550,357),(505,357)], "Finish or limit", (427,434))
    arrow([(325,357),(235,357)])
    arrow([(415,325),(415,285),(495,285),(495,325)], "One repair", (423,267))
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 12)
    c.drawString(55, 207, "EXECUTION CONTROLS")
    c.setFillColor(GRAY); c.setFont("Helvetica", 11)
    for i,line in enumerate([
        "10 decision rounds / 20 tool attempts / 600 seconds by default; token-aware pacing and bounded retries.",
        "Optional one-shot primary CVE timeout reaches the LLM; the LLM selects the recovery action.",
        "All stages emit local JSONL events and a readable transcript. Private reasoning is not stored.",
        "SQLite retains runs and reviewable task drafts; the dashboard compares saved source observations."]):
        c.drawString(55,181-i*22,line)
    c.setFont("Helvetica",9); c.drawString(55,52,"VulnBrief v0.3 | FastAPI workbench + LangGraph + Groq SDK + HTTPX + Pydantic + SQLite | Local, single-user prototype")
    c.save()


def writeup():
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyCustom",fontName="Helvetica",fontSize=10,leading=14,textColor=NAVY,spaceAfter=9))
    doc=SimpleDocTemplate(str(DOCS / "design-writeup.pdf"),pagesize=(595.28,841.89),
                          rightMargin=45,leftMargin=45,topMargin=40,bottomMargin=40)
    text=(DOCS / "design-writeup.txt").read_text(encoding="utf-8")
    flow=[Paragraph("VulnBrief | Design decisions and limitations",styles["Title"]),Spacer(1,10)]
    for paragraph in text.strip().split("\n\n"):
        flow.append(Paragraph(paragraph.replace("\n"," "),styles["BodyCustom"]))
    doc.build(flow)


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    architecture()
    if (DOCS / "design-writeup.txt").exists(): writeup()
