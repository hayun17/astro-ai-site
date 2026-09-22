from __future__ import annotations

import io
import math
import re
import unicodedata
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


MAX_INTERPRETATION_CHARS = 160_000
PAGE_W, PAGE_H = A4
INK = colors.HexColor("#352b3d")
MUTED = colors.HexColor("#7a6b80")
PLUM = colors.HexColor("#765285")
PLUM_DARK = colors.HexColor("#52395f")
ROSE = colors.HexColor("#d98caf")
LILAC = colors.HexColor("#b89ad1")
BLUSH = colors.HexColor("#fbf4f8")
PAPER = colors.HexColor("#fffdfb")
LINE = colors.HexColor("#e8dce9")

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ABBR = ["ARI", "TAU", "GEM", "CAN", "LEO", "VIR", "LIB", "SCO", "SAG", "CAP", "AQU", "PIS"]
BODY_ABBR = {
    "Sun": "Su", "Moon": "Mo", "Mercury": "Me", "Venus": "Ve", "Mars": "Ma",
    "Jupiter": "Ju", "Saturn": "Sa", "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl",
    "TrueNode": "No", "Lilith": "Li", "Chiron": "Ch",
}
ASPECT_COLORS = {
    "Conjunction": colors.HexColor("#9b77ad"),
    "Opposition": colors.HexColor("#c87686"),
    "Square": colors.HexColor("#d18a82"),
    "Trine": colors.HexColor("#729f93"),
    "Sextile": colors.HexColor("#7f94b7"),
}


def _safe_ascii(value: Any) -> str:
    text = str(value if value is not None else "")
    text = (
        text.replace("°", " deg ")
        .replace("′", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("…", "...")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def _page_decor(canvas, doc, *, premium: bool = False) -> None:
    canvas.saveState()
    if premium:
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#f6eaf3"))
        canvas.circle(PAGE_W + 5 * mm, PAGE_H - 8 * mm, 36 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.HexColor("#f0e9f7"))
        canvas.circle(-8 * mm, 12 * mm, 30 * mm, stroke=0, fill=1)
        canvas.setStrokeColor(colors.HexColor("#eadfeb"))
        canvas.setLineWidth(0.5)
        canvas.line(18 * mm, 14 * mm, PAGE_W - 18 * mm, 14 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(18 * mm, 9.3 * mm, "AstroMYLA - personal astrology report")
        canvas.drawRightString(PAGE_W - 18 * mm, 9.3 * mm, f"Page {doc.page}")
        canvas.setFont("Helvetica-Oblique", 6.4)
        canvas.setFillColor(colors.HexColor("#9a8d9f"))
        canvas.drawCentredString(PAGE_W / 2.0, 5.3 * mm, "For reflection and entertainment only.")
    else:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#7a6887"))
        canvas.drawString(18 * mm, 10 * mm, "AstroMYLA - interpretive astrology report")
        canvas.drawRightString(PAGE_W - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _premium_page(canvas, doc) -> None:
    _page_decor(canvas, doc, premium=True)


def _standard_page(canvas, doc) -> None:
    _page_decor(canvas, doc, premium=False)


def _clean_inline_markup(line: str) -> str:
    cleaned = _safe_ascii(line)
    escaped = escape(cleaned)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped)
    return escaped


def _markdown_blocks(text: str, styles, *, premium: bool = False) -> list[Any]:
    story: list[Any] = []
    text = (text or "")[:MAX_INTERPRETATION_CHARS]
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 2.2 * mm if premium else 2.4 * mm))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_clean_inline_markup(line[4:]), styles["Section"]))
            continue
        if line.startswith("## "):
            story.append(Paragraph(_clean_inline_markup(line[3:]), styles["Section"]))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_clean_inline_markup(line[2:]), styles["Section"]))
            continue
        if line.startswith("- "):
            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", _safe_ascii(line[2:]))
            story.append(Paragraph("- " + escape(cleaned), styles["Body"]))
            continue
        story.append(Paragraph(_clean_inline_markup(line), styles["Body"]))
    return story


def _chart_from_data(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("chart"), dict):
        return data["chart"]
    if isinstance(data.get("composite"), dict):
        return data["composite"]
    return data if isinstance(data, dict) else {}


def _fmt_deg(deg: Any) -> str:
    try:
        value = float(deg)
    except Exception:
        return ""
    d = int(value)
    m = int(round((value - d) * 60.0))
    if m == 60:
        d += 1
        m = 0
    return f"{d} deg {m:02d}'"


def _big_three(chart: dict[str, Any]) -> list[tuple[str, str]]:
    planets = chart.get("planets") or {}
    points = chart.get("points") or {}
    rows: list[tuple[str, str]] = []
    for label, body in [("Sun", planets.get("Sun") or {}), ("Moon", planets.get("Moon") or {}), ("Rising", points.get("Asc") or {})]:
        if not body.get("sign"):
            continue
        deg = body.get("deg_in_sign")
        value = str(body.get("sign")) if deg is None else f"{body.get('sign')} {_fmt_deg(deg)}"
        rows.append((label, value))
    return rows


def _premium_cover_meta(chart: dict[str, Any], tier: str, styles) -> list[Any]:
    name = _safe_ascii(chart.get("name") or "Your chart")[:72]
    birthplace = _safe_ascii(chart.get("birthplace") or "")
    birth_date = _safe_ascii(chart.get("birth_date") or "")
    birth_time = "Time unknown" if chart.get("time_unknown") else _safe_ascii(chart.get("birth_time") or "")
    timezone = _safe_ascii(chart.get("timezone") or "")
    meta_bits = [x for x in [birth_date, birth_time, birthplace, timezone] if x]
    subtitle = "  |  ".join(meta_bits)
    tier_label = "DEEP PERSONAL READING" if tier == "deep" else "PERSONALIZED READING"

    out: list[Any] = [
        Spacer(1, 2 * mm),
        Paragraph("ASTROMYLA", styles["Brand"]),
        Paragraph(tier_label, styles["Kicker"]),
        Spacer(1, 2 * mm),
        Paragraph(f"A personal astrology reading for {escape(name)}", styles["PremiumTitle"]),
    ]
    if subtitle:
        out.append(Paragraph(escape(subtitle), styles["CoverMeta"]))
    out.extend([
        Spacer(1, 3 * mm),
        Paragraph("The chart is the map. The reading is the conversation.", styles["CoverQuote"]),
        Spacer(1, 5 * mm),
    ])
    return out


class NatalChartWheel(Flowable):
    """A compact, vector natal wheel drawn from the computed chart JSON.

    It deliberately uses short ASCII labels so the PDF remains portable without
    bundling font files.  Houses and angles are omitted when the birth time is
    unknown rather than guessed.
    """

    def __init__(self, chart: dict[str, Any], size: float = 142 * mm):
        super().__init__()
        self.chart = chart or {}
        self.width = size
        self.height = size

    @staticmethod
    def _angle_for(lon: float, asc: float) -> float:
        # Put the Ascendant at the left side and progress zodiac clockwise.
        return math.radians(180.0 - ((float(lon) - float(asc)) % 360.0))

    @staticmethod
    def _xy(cx: float, cy: float, r: float, angle: float) -> tuple[float, float]:
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    def draw(self) -> None:
        c = self.canv
        chart = self.chart
        planets = chart.get("planets") or {}
        points = chart.get("points") or {}
        houses = chart.get("houses") or {}
        asc = (points.get("Asc") or {}).get("lon")
        if asc is None:
            asc = houses.get("ascendant")
        if asc is None:
            asc = 0.0

        cx = self.width / 2.0
        cy = self.height / 2.0
        r_outer = min(self.width, self.height) * 0.46
        r_sign_inner = r_outer * 0.80
        r_house = r_outer * 0.67
        r_planet_base = r_outer * 0.59
        r_aspect = r_outer * 0.43

        # Soft disc.
        c.setFillColor(colors.HexColor("#fffafc"))
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.circle(cx, cy, r_outer, stroke=1, fill=1)
        c.circle(cx, cy, r_sign_inner, stroke=1, fill=0)
        c.circle(cx, cy, r_house, stroke=1, fill=0)

        # Zodiac sectors and labels.
        for i in range(12):
            boundary = i * 30.0
            angle = self._angle_for(boundary, asc)
            x1, y1 = self._xy(cx, cy, r_sign_inner, angle)
            x2, y2 = self._xy(cx, cy, r_outer, angle)
            c.setStrokeColor(colors.HexColor("#dfd3e4"))
            c.setLineWidth(0.45)
            c.line(x1, y1, x2, y2)

            mid = self._angle_for(boundary + 15.0, asc)
            tx, ty = self._xy(cx, cy, (r_outer + r_sign_inner) / 2.0, mid)
            c.setFillColor(PLUM_DARK)
            c.setFont("Helvetica-Bold", 6.2)
            c.drawCentredString(tx, ty - 2.2, SIGN_ABBR[i])

        # Houses, only with a known time.
        if not chart.get("time_unknown"):
            cusps = houses.get("cusps") or []
            if isinstance(cusps, list) and len(cusps) == 12:
                for idx, cusp in enumerate(cusps, start=1):
                    try:
                        lon = float(cusp.get("lon") if isinstance(cusp, dict) else cusp)
                    except Exception:
                        continue
                    angle = self._angle_for(lon, asc)
                    x2, y2 = self._xy(cx, cy, r_sign_inner, angle)
                    c.setStrokeColor(colors.HexColor("#c9b7d1"))
                    c.setLineWidth(0.55 if idx not in {1, 4, 7, 10} else 1.15)
                    c.line(cx, cy, x2, y2)

                # House numbers in approximate middle between adjacent cusps.
                for idx in range(12):
                    try:
                        a = float(cusps[idx].get("lon") if isinstance(cusps[idx], dict) else cusps[idx])
                        b = float(cusps[(idx + 1) % 12].get("lon") if isinstance(cusps[(idx + 1) % 12], dict) else cusps[(idx + 1) % 12])
                    except Exception:
                        continue
                    span = (b - a) % 360.0
                    mid_lon = (a + span / 2.0) % 360.0
                    angle = self._angle_for(mid_lon, asc)
                    tx, ty = self._xy(cx, cy, r_house * 0.91, angle)
                    c.setFillColor(colors.HexColor("#9b8ca1"))
                    c.setFont("Helvetica", 6.5)
                    c.drawCentredString(tx, ty - 2.0, str(idx + 1))

        # Aspect lines - major planets only, tightest first to avoid a black web.
        aspects = chart.get("aspects") or {}
        aspect_rows = list(aspects.get("planet_aspects") or [])
        aspect_rows = sorted(aspect_rows, key=lambda a: float(a.get("orb", 99.0)))[:18]
        positions: dict[str, float] = {}
        for name, body in planets.items():
            if body.get("lon") is not None and body.get("available", True):
                positions[name] = float(body["lon"])
        for a in aspect_rows:
            p1, p2 = a.get("p1"), a.get("p2")
            if p1 not in positions or p2 not in positions:
                continue
            ang1 = self._angle_for(positions[p1], asc)
            ang2 = self._angle_for(positions[p2], asc)
            x1, y1 = self._xy(cx, cy, r_aspect, ang1)
            x2, y2 = self._xy(cx, cy, r_aspect, ang2)
            c.setStrokeColor(ASPECT_COLORS.get(str(a.get("aspect")), colors.HexColor("#b5a8ba")))
            c.setLineWidth(0.55)
            c.setFillAlpha(0.65)
            c.line(x1, y1, x2, y2)
        c.setFillAlpha(1)

        # Planet labels.  Stagger close longitudes across three rings.
        body_items: list[tuple[str, float]] = []
        # Keep the wheel visually clean: the ten major planets are plotted on
        # the cover. Nodes/Lilith/Chiron remain fully present in the detailed
        # position table and interpretation.
        for name in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            body = planets.get(name) or {}
            if body.get("lon") is not None and body.get("available", True):
                body_items.append((name, float(body["lon"])))
        body_items.sort(key=lambda x: x[1])

        # Assign a radial lane per body. Nearby longitudes get different lanes
        # instead of piling labels on top of each other.
        lane_last_lon: list[float | None] = [None, None, None, None]
        lane_radii = [r_planet_base + 2.0 * mm, r_planet_base - 5.5 * mm, r_planet_base - 13.0 * mm, r_planet_base - 20.5 * mm]
        for name, lon in body_items:
            lane = 0
            for idx, last_lon in enumerate(lane_last_lon):
                if last_lon is None:
                    lane = idx
                    break
                sep = min((lon - last_lon) % 360.0, (last_lon - lon) % 360.0)
                if sep >= 8.0:
                    lane = idx
                    break
            else:
                lane = min(range(len(lane_last_lon)), key=lambda i: abs(((lon - (lane_last_lon[i] or lon) + 180.0) % 360.0) - 180.0))
            lane_last_lon[lane] = lon
            radius = max(14 * mm, lane_radii[lane])
            angle = self._angle_for(lon, asc)
            x, y = self._xy(cx, cy, radius, angle)
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.HexColor("#bda8c7"))
            c.setLineWidth(0.65)
            c.circle(x, y, 3.6 * mm, stroke=1, fill=1)
            c.setFillColor(PLUM_DARK)
            c.setFont("Helvetica-Bold", 5.8)
            c.drawCentredString(x, y - 1.8, BODY_ABBR.get(name, name[:2]))

        # Angle markers.
        if not chart.get("time_unknown"):
            for label in ["Asc", "MC", "DSC", "IC"]:
                point = points.get(label) or {}
                if point.get("lon") is None:
                    continue
                angle = self._angle_for(float(point["lon"]), asc)
                x1, y1 = self._xy(cx, cy, r_outer + 1.2 * mm, angle)
                c.setFillColor(ROSE if label in {"Asc", "MC"} else PLUM)
                c.setFont("Helvetica-Bold", 7.2)
                c.drawCentredString(x1, y1 - 2.5, label.upper())

        # Centre mark.
        c.setFillColor(colors.HexColor("#eee4f1"))
        c.circle(cx, cy, 2.1 * mm, stroke=0, fill=1)


def _natal_summary(data: dict[str, Any], styles, *, premium: bool = False) -> list[Any]:
    chart = _chart_from_data(data)
    planets = (chart or {}).get("planets") or {}
    rows = [["Body", "Placement", "House", "Motion"]] if premium else [["Body", "Placement", "House"]]
    for name in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "TrueNode", "Lilith", "Chiron"]:
        p = planets.get(name) or {}
        if not p.get("sign"):
            continue
        deg = p.get("deg_in_sign")
        placement = str(p.get("sign")) if deg is None else f"{p.get('sign')} {_fmt_deg(deg)}"
        base_row = [name, placement, "-" if p.get("house") is None else str(p.get("house"))]
        if premium:
            base_row.append("Rx" if p.get("retrograde") else "Direct")
        rows.append(base_row)
    if len(rows) == 1:
        return []
    widths = [30 * mm, 72 * mm, 23 * mm, 25 * mm] if premium else [38 * mm, 80 * mm, 28 * mm]
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2e8f4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), PLUM_DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#d9c8de")),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#eee6ef")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdfafd")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
    ]))
    heading = "Your chart at a glance" if premium else "Chart summary"
    return [Paragraph(heading, styles["Section"]), table, Spacer(1, 4 * mm)]


def _synastry_summary(data: dict[str, Any], styles) -> list[Any]:
    syn = data.get("synastry") if isinstance(data.get("synastry"), dict) else data
    aspects = (syn or {}).get("aspects") or []
    rows = [["Person A", "Aspect", "Person B", "Orb"]]
    for a in aspects[:28]:
        rows.append([str(a.get("a", "")), str(a.get("aspect", "")), str(a.get("b", "")), f"{float(a.get('orb', 0)):.2f} deg"])
    if len(rows) == 1:
        return []
    table = Table(rows, colWidths=[38 * mm, 38 * mm, 38 * mm, 30 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3e8f8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ddd1e5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcf9fd")]),
    ]))
    return [Paragraph("Tight cross-chart aspects", styles["Section"]), table, Spacer(1, 4 * mm)]


def _astrocartography_summary(data: dict[str, Any], styles) -> list[Any]:
    acg = data.get("astrocartography") if isinstance(data.get("astrocartography"), dict) else data
    bodies = (acg or {}).get("bodies") or {}
    rows = [["Planet", "RA", "Declination"]]
    for name, body in bodies.items():
        rows.append([name, f"{float(body.get('ra', 0)):.2f} deg", f"{float(body.get('dec', 0)):.2f} deg"])
    table = Table(rows, colWidths=[45 * mm, 50 * mm, 50 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3e8f8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ddd1e5")),
    ]))
    return [Paragraph("Astrocartography calculation summary", styles["Section"]), table, Spacer(1, 4 * mm)]


def _reflection_card(styles, tier: str) -> Table:
    text = (
        "This report is designed to be read slowly. Circle what feels true, question what does not, and come back to the sections that keep catching your attention. "
        "Astrology works best here as a language for reflection - not a verdict about who you are."
        if tier == "personalized"
        else
        "A deep reading is not asking you to become a different person. It is asking you to notice the patterns you already live inside with a little more choice. "
        "Keep the parts that create recognition, leave the parts that do not, and let the report become a conversation rather than a rulebook."
    )
    inner = Paragraph(escape(_safe_ascii(text)), styles["Callout"])
    table = Table([[inner]], colWidths=[154 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf1f7")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#ead2e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def _build_styles(premium: bool) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    if not premium:
        return {
            "Title": ParagraphStyle("AstroTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=PLUM_DARK, alignment=TA_CENTER, spaceAfter=8 * mm),
            "Section": ParagraphStyle("AstroSection", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#6e4c82"), spaceBefore=4 * mm, spaceAfter=2 * mm),
            "Body": ParagraphStyle("AstroBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13.2, textColor=colors.HexColor("#312b35"), spaceAfter=1.3 * mm),
            "Small": ParagraphStyle("AstroSmall", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#6f6475")),
        }
    return {
        "Brand": ParagraphStyle("Brand", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=PLUM, alignment=TA_CENTER, tracking=2),
        "Kicker": ParagraphStyle("Kicker", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.8, leading=10, textColor=ROSE, alignment=TA_CENTER, spaceBefore=1.5 * mm, spaceAfter=2 * mm),
        "PremiumTitle": ParagraphStyle("PremiumTitle", parent=base["Title"], fontName="Times-Bold", fontSize=25, leading=29, textColor=PLUM_DARK, alignment=TA_CENTER, spaceAfter=3 * mm),
        "CoverMeta": ParagraphStyle("CoverMeta", parent=base["BodyText"], fontName="Helvetica", fontSize=8.1, leading=10.5, textColor=MUTED, alignment=TA_CENTER),
        "CoverQuote": ParagraphStyle("CoverQuote", parent=base["BodyText"], fontName="Times-Italic", fontSize=11.2, leading=14, textColor=colors.HexColor("#826a87"), alignment=TA_CENTER),
        "Title": ParagraphStyle("AstroPremiumTitle", parent=base["Title"], fontName="Times-Bold", fontSize=22, leading=26, textColor=PLUM_DARK, alignment=TA_CENTER, spaceAfter=6 * mm),
        "Section": ParagraphStyle("AstroPremiumSection", parent=base["Heading2"], fontName="Times-Bold", fontSize=15.2, leading=18, textColor=PLUM_DARK, spaceBefore=6 * mm, spaceAfter=2.5 * mm, keepWithNext=True),
        "Body": ParagraphStyle("AstroPremiumBody", parent=base["BodyText"], fontName="Times-Roman", fontSize=10.45, leading=15.2, textColor=INK, spaceAfter=2.1 * mm),
        "Small": ParagraphStyle("AstroPremiumSmall", parent=base["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.4, textColor=MUTED),
        "Callout": ParagraphStyle("AstroCallout", parent=base["BodyText"], fontName="Times-Italic", fontSize=10.1, leading=14.2, textColor=PLUM_DARK),
        "MiniLabel": ParagraphStyle("MiniLabel", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.2, leading=9, textColor=ROSE, alignment=TA_CENTER),
        "MiniValue": ParagraphStyle("MiniValue", parent=base["BodyText"], fontName="Times-Bold", fontSize=10.2, leading=12, textColor=PLUM_DARK, alignment=TA_CENTER),
    }


def _premium_story(*, title: str, data: dict[str, Any], interpretation: str, tier: str, styles) -> list[Any]:
    chart = _chart_from_data(data)
    story: list[Any] = []
    story.extend(_premium_cover_meta(chart, tier, styles))
    story.append(NatalChartWheel(chart, size=135 * mm))
    story.append(Spacer(1, 1.5 * mm))

    big3 = _big_three(chart)
    if big3:
        cells: list[Any] = []
        for label, value in big3:
            cells.append(Table([[Paragraph(label.upper(), styles["MiniLabel"])], [Paragraph(escape(_safe_ascii(value)), styles["MiniValue"])]], colWidths=[48 * mm]))
        table = Table([cells], colWidths=[52 * mm] * len(cells), hAlign="CENTER")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#eaddea")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eaddea")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffafd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
    story.extend([
        Spacer(1, 3 * mm),
        Paragraph("Your natal chart is placed first on purpose: every page that follows should be traceable back to the map above.", styles["Small"]),
        PageBreak(),
        _reflection_card(styles, tier),
        Spacer(1, 3 * mm),
    ])
    story.extend(_natal_summary(data, styles, premium=True))

    premium_meta = data.get("premium") if isinstance(data.get("premium"), dict) else {}
    questions = premium_meta.get("questions") or []
    if tier == "deep" and questions:
        story.append(Paragraph("The questions you brought into this reading", styles["Section"]))
        for idx, question in enumerate(questions[:3], start=1):
            story.append(Paragraph(f"<b>{idx}.</b> {escape(_safe_ascii(question))}", styles["Body"]))
        story.append(Spacer(1, 2 * mm))

    if interpretation:
        story.extend(_markdown_blocks(interpretation, styles, premium=True))
    return story


def build_report_pdf(*, kind: str, title: str, data: dict[str, Any], interpretation: str, tier: str = "free") -> bytes:
    tier = tier if tier in {"free", "personalized", "deep"} else "free"
    premium = tier in {"personalized", "deep"} and kind == "natal"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm if premium else 18 * mm,
        rightMargin=20 * mm if premium else 18 * mm,
        topMargin=18 * mm if premium else 20 * mm,
        bottomMargin=19 * mm if premium else 18 * mm,
        title=_safe_ascii(title),
        author="AstroMYLA",
        subject="Personal astrology reading" if premium else "Astrology report",
    )
    styles = _build_styles(premium)

    if premium:
        story = _premium_story(title=title, data=data, interpretation=interpretation, tier=tier, styles=styles)
        doc.build(story, onFirstPage=_premium_page, onLaterPages=_premium_page)
        return buffer.getvalue()

    story: list[Any] = [
        Paragraph(escape(_safe_ascii(title)), styles["Title"]),
        Paragraph(
            "Astrology is interpretive and is not a scientific, medical, legal, or financial assessment.",
            styles["Small"],
        ),
        Spacer(1, 5 * mm),
    ]

    if kind == "natal":
        story.extend(_natal_summary(data, styles))
    elif kind == "synastry":
        story.extend(_synastry_summary(data, styles))
    elif kind == "astrocartography":
        story.extend(_astrocartography_summary(data, styles))
    elif kind == "composite":
        composite = data.get("composite") if isinstance(data.get("composite"), dict) else data
        story.extend(_natal_summary({"chart": composite or {}}, styles))

    if interpretation:
        story.append(Paragraph("Interpretation", styles["Section"]))
        story.extend(_markdown_blocks(interpretation, styles))

    doc.build(story, onFirstPage=_standard_page, onLaterPages=_standard_page)
    return buffer.getvalue()
