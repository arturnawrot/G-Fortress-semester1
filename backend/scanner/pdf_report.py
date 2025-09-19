# thx chatGPT
from __future__ import annotations
from typing import Dict, List, Tuple, Iterable
from datetime import datetime

from scanner.scanner_service import scan_user
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
)

from scanner.vulnerabilities.vulnerability_interface import VulnerabilityInterface
from scanner.vulnerabilities.severity_score import SeverityScore
from scanner_api_client.user import User
from scanner.report import Report

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import settings

def _severity_label(score: int) -> str:
    return SeverityScore(score).get_description()

def _severity_color_hex(score: int) -> str:
    return SeverityScore(score).get_color_hex()

def _count_by_label(vulns: Iterable[VulnerabilityInterface]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for v in vulns:
        label = _severity_label(int(v.get_severity_score()))
        counts[label] = counts.get(label, 0) + 1
    counts["Total"] = sum(counts.values())
    return counts

def _severity_score_key(v: VulnerabilityInterface) -> Tuple[int, str]:
    return (int(v.get_severity_score()), v.get_vulnerability_name())

def _label_priority(labels: Iterable[str]) -> List[str]:
    sample_points = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    label_rank: Dict[str, int] = {}
    for i, s in enumerate(sample_points):
        label = _severity_label(s)
        label_rank[label] = min(label_rank.get(label, i), i)
    return sorted(set(labels), key=lambda L: label_rank.get(L, 999))

class MultiUserPDFReport:
    """Builds one PDF with sections per user; uses SeverityScore for labels/colors."""

    def __init__(self, title: str, subtitle: str | None = None, font_name="roboto"):
        self.title = title
        self.subtitle = subtitle

        font_path = settings.PROJECT_ROOT_PATH / "fonts" / "roboto.ttf"
        pdfmetrics.registerFont(TTFont(font_name, font_path))

        self.styles = getSampleStyleSheet()
        for style_name in ["Normal", "Title", "Heading1", "Heading2"]:
            self.styles[style_name].fontName = font_name

        self.styles["Title"].fontSize = 22
        self.styles["Title"].leading = 26
        self.styles["Heading1"].spaceBefore = 10
        self.styles["Heading1"].spaceAfter = 4
        self.styles["Heading2"].spaceBefore = 8
        self.styles["Heading2"].spaceAfter = 4

        self.styles.add(ParagraphStyle(name="Small", fontName=font_name, fontSize=9, leading=11, textColor=colors.black))
        self.styles.add(ParagraphStyle(name="Muted", fontName=font_name, fontSize=8, leading=10, textColor=colors.grey))

        self._FONT_REGULAR = font_name
        self._FONT_BOLD = font_name  # if you register a bold face, set it here

        self.doc = SimpleDocTemplate(
            filename="",
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=self.title,
            author="scanner",
            subject="User vulnerability report",
        )

    # ---- page furniture
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setStrokeColor(colors.lightgrey)
        canvas.setLineWidth(0.3)
        canvas.line(self.doc.leftMargin, h - self.doc.topMargin + 6, w - self.doc.rightMargin, h - self.doc.topMargin + 6)
        canvas.setFont(self._FONT_REGULAR, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(w - self.doc.rightMargin, self.doc.bottomMargin - 10, f"Page {doc.page}")
        canvas.restoreState()

    def _title_page(self):
        parts = []
        parts.append(Spacer(1, 40))
        parts.append(Paragraph(self.title, self.styles["Title"]))
        if self.subtitle:
            parts.append(Spacer(1, 6))
            parts.append(Paragraph(self.subtitle, self.styles["Heading2"]))
        parts.append(Spacer(1, 8))
        parts.append(Paragraph(datetime.utcnow().strftime("Generated on %Y-%m-%d %H:%M UTC"), self.styles["Small"]))
        parts.append(Spacer(1, 20))
        return parts

    def _toc(self, markers: list[tuple[str, int]]):
        parts = [Paragraph("Table of Contents", self.styles["Heading1"])]
        data = [["User", "Page"]] + [[t, str(p)] for (t, p) in markers]
        t = Table(data, colWidths=[None, 40])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), self._FONT_REGULAR),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F4F4")),
            ("FONTNAME", (0, 0), (-1, 0), self._FONT_BOLD),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
        ]))
        parts += [t, Spacer(1, 12), PageBreak()]
        return parts

    def _summary_table(self, counts: Dict[str, int]) -> Table:
        labels = [k for k in counts.keys() if k != "Total"]
        ordered = _label_priority(labels)
        headers = ordered + ["Total"]
        row = [counts.get(h, 0) for h in headers]

        t = Table([headers, row])
        style = [
            ("FONTNAME", (0, 0), (-1, -1), self._FONT_REGULAR),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F4F4")),
            ("FONTNAME", (0, 0), (-1, 0), self._FONT_BOLD),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]
        sample_points = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        for idx, label in enumerate(ordered):
            for s in sample_points:
                if _severity_label(s) == label:
                    style.append(("TEXTCOLOR", (idx, 0), (idx, 0), colors.HexColor(_severity_color_hex(s))))
                    break
        t.setStyle(TableStyle(style))
        return t

    def _findings_table(self, vulns: List[VulnerabilityInterface]) -> Table:
        def _clamp(x, lo, hi):
            return max(lo, min(hi, x))

        headers = ["Name", "Generic Description", "Detected", "Score"]
        rows: List[List[str]] = []
        name_chars = generic_chars = detected_chars = 0

        for v in vulns:
            score = int(v.get_severity_score())
            name = v.get_vulnerability_name() or ""
            generic = v.get_vulnerability_description() or ""
            detected = v.get_description_of_the_detected_vulnerability() or ""

            name_chars += len(name)
            generic_chars += len(generic)
            detected_chars += len(detected)

            rows.append([name, generic, detected, str(score)])

        body_style = ParagraphStyle(
            name="TableBody",
            parent=self.styles["Normal"],
            fontName=self._FONT_REGULAR,
            fontSize=8.5,
            leading=10,
        )

        data = [headers]
        for r in rows:
            data.append([
                Paragraph(r[0], body_style),
                Paragraph(r[1], body_style),
                Paragraph(r[2], body_style),
                Paragraph(r[3], body_style),
            ])

        available = self.doc.width
        score_w = 35
        name_min, generic_min, detected_min = 70, 120, 120

        remaining = max(available - score_w, name_min + generic_min + detected_min)

        smooth = 200
        total_desc_chars = (generic_chars + detected_chars) + 2 * smooth

        name_share = (name_chars + smooth) / (name_chars + total_desc_chars + 3 * smooth)
        name_w = _clamp(remaining * max(0.15, min(0.25, name_share)), name_min, remaining * 0.30)

        rest = remaining - name_w
        generic_share = (generic_chars + smooth) / (generic_chars + detected_chars + 2 * smooth)
        generic_w = _clamp(rest * generic_share, generic_min, rest * 0.70)
        detected_w = max(detected_min, rest - generic_w)

        col_widths = [name_w, generic_w, detected_w, score_w]
        t = Table(data, colWidths=col_widths, repeatRows=1)

        st = TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), self._FONT_REGULAR),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FAFAFA")),
            ("FONTNAME", (0, 0), (-1, 0), self._FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FCFCFF")]),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])

        for i, v in enumerate(vulns, start=1):
            s = int(v.get_severity_score())
            st.add("TEXTCOLOR", (3, i), (3, i), colors.HexColor(_severity_color_hex(s)))

        t.setStyle(st)
        return t

    def build(self, path: str, report: Report):  # <-- CHANGED: accept Report
        self.doc.filename = path

        # Build a sortable list of (user, vulns) from the Report
        pairs: List[Tuple[User, List[VulnerabilityInterface]]] = []
        for u in report.users():
            pairs.append((u, list(report.vulnerabilities_for(u))))

        def risk_key(vs: List[VulnerabilityInterface]) -> Tuple[int, int, int]:
            high = sum(1 for v in vs if int(v.get_severity_score()) >= 9)
            mid  = sum(1 for v in vs if 4 <= int(v.get_severity_score()) <= 8)
            return (high, mid, len(vs))

        items = sorted(pairs, key=lambda kv: risk_key(kv[1]), reverse=True)

        story, markers = self._build_story(items, collect_markers=True)
        self.doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

        story, _ = self._build_story(items, collected_markers=markers)
        self.doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

    def _build_story(self, items, collect_markers: bool = False, collected_markers: list[tuple[str, int]] | None = None):
        story = []
        story += self._title_page()
        if collected_markers is not None:
            story += self._toc(collected_markers)

        markers: list[tuple[str, int]] = []

        for user, vulns in items:
            if collect_markers:
                story.append(_PageMarker(lambda page, name=user.name: markers.append((name, page))))

            heading = f"{user.name}  —  {user.machine.friendly_name}"
            meta = " / ".join(filter(None, [
                getattr(user, "email", None),
                getattr(user.machine, "operating_system", None),
                f"pwd updated: {user.get_password_updated_at()}" if user.get_password_updated_at() else None
            ]))
            story.append(Paragraph(heading, self.styles["Heading1"]))
            if meta:
                story.append(Paragraph(meta, self.styles["Muted"]))
            story.append(Spacer(1, 6))

            # Use your interface's `check()` to filter detected findings
            detected = [v for v in vulns if v.check()]
            detected.sort(key=_severity_score_key, reverse=True)

            counts = _count_by_label(detected)
            story.append(Paragraph("Summary", self.styles["Heading2"]))
            story.append(self._summary_table(counts))
            story.append(Spacer(1, 8))

            if detected:
                story.append(Paragraph("Findings", self.styles["Heading2"]))
                story.append(self._findings_table(detected))
            else:
                story.append(Paragraph("No detected vulnerabilities for this user.", self.styles["Small"]))

            story.append(Spacer(1, 10))
            story.append(PageBreak())

        if story and isinstance(story[-1], PageBreak):
            story.pop()

        return story, markers


class _PageMarker(Flowable):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.width = 0
        self.height = 0
    def draw(self):
        self.callback(self.canv.getPageNumber())


# ---------------
# Glue: build a Report, then render it
# ---------------

def build_report_as_pdf(report: Report, out_path: str):
    MultiUserPDFReport(
        title="Organization User Vulnerability Report",
        subtitle="Consolidated findings across scanned users",
    ).build(str(settings.PDF_STORAGE_PATH / out_path), report)