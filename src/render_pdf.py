"""
render_pdf.py — deterministic newspaper-style PDF. Pure formatting; no network,
no LLM. Renders identically every day regardless of which branch (LLM-valid or
fallback) produced the data, so the layout can never "break" the way it did
before. Works with zero papers (prints an honest quiet-day note).

Design brief: a one-reader research broadsheet for AUDITORY neuroscience.
Palette is "ink & signal": near-black ink, warm paper, a single spectral-teal
accent (evoking a spectrogram/tuning curve) rather than the default broadsheet
red. Display face: Times (serif, authoritative masthead). Utility face:
Helvetica (labels, meta, data). The signature device is a thin spectral rule
under the masthead.
"""
from __future__ import annotations
import datetime as dt

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    KeepTogether, Flowable,
)

INK = colors.HexColor("#161616")
ACCENT = colors.HexColor("#0f6e6e")     # spectral teal
ACCENT_DK = colors.HexColor("#0a4f4f")
RULE = colors.HexColor("#cdc7ba")
MUTED = colors.HexColor("#5c5c5c")
POTD_BG = colors.HexColor("#161616")
QBOX_BG = colors.HexColor("#0f6e6e")

POOL_A_BADGE = colors.HexColor("#0f6e6e")
POOL_B_BADGE = colors.HexColor("#8a5a00")


class SpectralRule(Flowable):
    """A thin bar of varying-height ticks, evoking a spectrogram slice —
    the paper's signature device under the masthead."""
    def __init__(self, width, height=10):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        import math
        c = self.canv
        n = 90
        step = self.width / n
        for i in range(n):
            # deterministic pseudo-spectral envelope
            h = (0.35 + 0.65 * abs(math.sin(i * 0.7) * math.cos(i * 0.23))) * self.height
            c.setStrokeColor(ACCENT if i % 3 else ACCENT_DK)
            c.setLineWidth(step * 0.7)
            x = i * step + step / 2
            c.line(x, 0, x, h)


def _styles():
    ss = getSampleStyleSheet()
    return {
        "masthead": ParagraphStyle("m", parent=ss["Title"], fontName="Times-Bold",
                                   fontSize=25, textColor=INK, leading=27, spaceAfter=1),
        "dateline": ParagraphStyle("dl", parent=ss["Normal"], fontName="Helvetica",
                                   fontSize=8.5, textColor=MUTED, spaceAfter=0),
        "editorial": ParagraphStyle("ed", parent=ss["Normal"], fontName="Times-Roman",
                                    fontSize=10.5, textColor=INK, leading=14.5,
                                    alignment=TA_JUSTIFY, spaceAfter=4),
        "section": ParagraphStyle("s", parent=ss["Heading2"], fontName="Helvetica-Bold",
                                  fontSize=10, textColor=ACCENT_DK, spaceBefore=9,
                                  spaceAfter=3, tracking=0),
        "ptitle": ParagraphStyle("pt", parent=ss["Normal"], fontName="Times-Bold",
                                 fontSize=10.5, textColor=INK, leading=13, spaceAfter=1),
        "pmeta": ParagraphStyle("pm", parent=ss["Normal"], fontName="Helvetica-Oblique",
                                fontSize=7.8, textColor=MUTED, spaceAfter=2),
        "pnote": ParagraphStyle("pn", parent=ss["Normal"], fontName="Helvetica",
                                fontSize=9.3, textColor=INK, leading=12.2, spaceAfter=6),
        "potd_label": ParagraphStyle("pl", fontName="Helvetica-Bold", fontSize=8,
                                     textColor=colors.HexColor("#8fd4d4"), spaceAfter=3),
        "potd_title": ParagraphStyle("ptt", fontName="Times-Bold", fontSize=13,
                                     textColor=colors.white, leading=15.5, spaceAfter=2),
        "potd_meta": ParagraphStyle("ptm", fontName="Helvetica-Oblique", fontSize=8.5,
                                    textColor=colors.HexColor("#d8d8d8"), spaceAfter=4),
        "potd_bullet": ParagraphStyle("pb", fontName="Helvetica", fontSize=9.4,
                                      textColor=colors.white, leading=12.8, spaceAfter=3,
                                      leftIndent=10),
        "qlabel": ParagraphStyle("ql", fontName="Helvetica-Bold", fontSize=7.5,
                                 textColor=colors.white, spaceAfter=2),
        "qtext": ParagraphStyle("qt", fontName="Times-Italic", fontSize=10.3,
                                textColor=colors.white, leading=13),
        "footer": ParagraphStyle("f", fontName="Helvetica", fontSize=7.5, textColor=MUTED),
        "quiet": ParagraphStyle("q", parent=ss["Normal"], fontName="Times-Italic",
                                fontSize=11, textColor=MUTED, leading=15),
    }


def _badge(pool, source_api):
    label = source_api or ("preprint" if pool == "A" else "journal")
    hexc = "#0f6e6e" if pool == "A" else "#8a5a00"
    return f'<font color="{hexc}" size="7"><b>{label.upper()}</b></font>'


def render_digest(output_path, issue_date, editorial, sections, paper_of_day,
                  candidates_count, sources_status, llm_ok):
    st = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        topMargin=0.65 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        title=f"Auditory Grouping Daily — {issue_date.isoformat()}",
        author="Auditory Grouping Daily",
    )
    content_w = LETTER[0] - 1.5 * inch
    story = []

    # Masthead
    story.append(Paragraph("AUDITORY GROUPING DAILY", st["masthead"]))
    story.append(SpectralRule(content_w, 7))
    story.append(Spacer(1, 3))
    mode = "curated" if llm_ok else "keyword fallback"
    story.append(Paragraph(
        f'{issue_date.strftime("%A, %d %B %Y")} &nbsp;&middot;&nbsp; '
        f'{candidates_count} papers screened &nbsp;&middot;&nbsp; {mode}', st["dateline"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=INK, spaceAfter=7))

    # Editorial
    if editorial:
        story.append(Paragraph(editorial, st["editorial"]))
        story.append(Spacer(1, 3))

    # Sections (papers first — Paper of the Day now closes the issue, not opens it)
    any_papers = False
    for name, papers in sections.items():
        if not papers:
            continue
        any_papers = True
        story.append(Paragraph(name.upper(), st["section"]))
        story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=4))
        for p in papers:
            badge = _badge(p.get("pool", "A"), p.get("source_api", ""))
            entry = [
                Paragraph(p.get("title", "(untitled)"), st["ptitle"]),
                Paragraph(f'{badge} &nbsp; {p.get("meta","")}', st["pmeta"]),
                Paragraph(p.get("note", ""), st["pnote"]),
            ]
            story.append(KeepTogether(entry))

    # Paper of the Day — closes the issue
    if paper_of_day:
        story.append(Spacer(1, 10))
        story.append(KeepTogether(_potd_box(st, paper_of_day, content_w)))
        story.append(Spacer(1, 8))

    if not any_papers and not paper_of_day:
        story.append(Paragraph(
            "No papers cleared the relevance bar today — that's a quiet-literature "
            "day, not an error. The source-health line below confirms the fetch ran. "
            "Back tomorrow.", st["quiet"]))

    # Footer: source health
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=3))
    status = " &nbsp;|&nbsp; ".join(
        f'{s}: {_status_text(v)}' for s, v in sources_status.items())
    story.append(Paragraph(f"Source status — {status}", st["footer"]))

    doc.build(story)
    return output_path


def _status_text(v):
    """v is {'ok': bool, 'count': int} (new format) or a plain bool (legacy).
    Showing the actual count is the point — a source that returns 0 without
    crashing (rate-limited, genuinely quiet) is now visibly different from
    one that's actually healthy, instead of both showing as 'ok'."""
    if isinstance(v, dict):
        if not v.get("ok"):
            return "FAILED"
        return f'{v.get("count", 0)} papers'
    return "ok" if v else "FAILED"


def _potd_box(st, potd, content_w):
    label = "PAPER OF THE DAY" if potd.get("source") != "canon" else "FOUNDATIONS PICK — read this classic"
    inner = [Paragraph(label, st["potd_label"]),
             Paragraph(potd.get("title", "(untitled)"), st["potd_title"])]
    if potd.get("meta"):
        inner.append(Paragraph(potd["meta"], st["potd_meta"]))
    inner.append(Spacer(1, 4))
    for b in potd.get("bullets", []):
        inner.append(Paragraph(f"&bull;&nbsp; {b}", st["potd_bullet"]))

    if potd.get("read_plan"):
        inner.append(Spacer(1, 5))
        inner.append(Paragraph("HOW TO READ IT (≈20 min)", st["qlabel"]))
        inner.append(Paragraph(potd["read_plan"], st["potd_bullet"]))

    # reflection question in its own accent sub-box
    if potd.get("reflection_question"):
        q_inner = [Paragraph("YOUR QUESTION TO ANSWER", st["qlabel"]),
                   Paragraph(potd["reflection_question"], st["qtext"])]
        qbox = Table([[q_inner]], colWidths=[content_w - 0.5 * inch])
        qbox.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), QBOX_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        inner.append(Spacer(1, 4))
        inner.append(qbox)

    box = Table([[inner]], colWidths=[content_w])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), POTD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
    ]))
    return box
