"""
Generate the ValenciaRisk video demo script as a formatted PDF.
Output: valenciarisk_video_script.pdf (project root)
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUT = Path(__file__).parent.parent / "valenciarisk_video_script.pdf"

# ── Colour palette ─────────────────────────────────────────────────────────
RED      = colors.HexColor("#E63946")
NAVY     = colors.HexColor("#0F1923")
CARD     = colors.HexColor("#1C2B3A")
OFFWHITE = colors.HexColor("#F1FAEE")
GREY     = colors.HexColor("#888888")
GREEN    = colors.HexColor("#06D6A0")
ORANGE   = colors.HexColor("#FF6B35")

# ── Styles ─────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, **kw):
    s = ParagraphStyle(name, parent=base["Normal"], **kw)
    return s

S = {
    "title": style("title",
        fontSize=22, textColor=RED, spaceAfter=4,
        fontName="Helvetica-Bold", alignment=TA_CENTER),
    "subtitle": style("subtitle",
        fontSize=11, textColor=GREY, spaceAfter=2,
        fontName="Helvetica", alignment=TA_CENTER),
    "url": style("url",
        fontSize=9, textColor=GREEN, spaceAfter=16,
        fontName="Helvetica", alignment=TA_CENTER),
    "section": style("section",
        fontSize=13, textColor=RED, spaceBefore=14, spaceAfter=4,
        fontName="Helvetica-Bold"),
    "subsection": style("subsection",
        fontSize=10, textColor=NAVY, spaceBefore=8, spaceAfter=2,
        fontName="Helvetica-Bold",
        backColor=colors.HexColor("#E8EEF4"),
        leftIndent=0, borderPad=4),
    "body": style("body",
        fontSize=9.5, textColor=colors.black, spaceAfter=4,
        fontName="Helvetica", leading=14, alignment=TA_JUSTIFY),
    "script": style("script",
        fontSize=9.5, textColor=NAVY, spaceAfter=4,
        fontName="Helvetica-Oblique", leading=14,
        leftIndent=14, alignment=TA_JUSTIFY),
    "screen": style("screen",
        fontSize=8.5, textColor=colors.HexColor("#5555AA"), spaceAfter=3,
        fontName="Helvetica-Oblique", leading=12, leftIndent=14),
    "label": style("label",
        fontSize=8, textColor=GREY, spaceAfter=1,
        fontName="Helvetica-Bold"),
    "note": style("note",
        fontSize=8, textColor=GREY, spaceAfter=4,
        fontName="Helvetica-Oblique", leading=11),
    "cue": style("cue",
        fontSize=8.5, textColor=colors.black, spaceAfter=2,
        fontName="Courier", leading=12),
}

# ── Helper ─────────────────────────────────────────────────────────────────
def hr(color=RED, thickness=1): return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)
def sp(h=6): return Spacer(1, h)
def P(text, s="body"): return Paragraph(text, S[s])

def section_block(title, speaker, timing, screen_text, script_text):
    """Build one script section as a keepable block."""
    items = []
    items.append(KeepTogether([
        P(title, "section"),
        hr(RED, 0.5),
    ]))
    meta = [
        ["Speaker", speaker],
        ["Timing",  timing],
    ]
    t = Table(meta, colWidths=[2.5*cm, 14*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",    (0,0),(-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0),(-1,-1), 8),
        ("TEXTCOLOR",   (0,0),(0,-1),  GREY),
        ("TEXTCOLOR",   (1,0),(1,-1),  colors.black),
        ("FONTNAME",    (0,0),(0,-1),  "Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",  (0,0),(-1,-1),2),
        ("VALIGN",      (0,0),(-1,-1),"TOP"),
    ]))
    items.append(t)
    items.append(sp(4))
    items.append(P(f"<b>ON SCREEN:</b> {screen_text}", "screen"))
    items.append(sp(3))
    items.append(P("SCRIPT:", "label"))
    for line in script_text:
        items.append(P(f'"{line}"', "script"))
    items.append(sp(6))
    return items

# ── Content ────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="ValenciaRisk — Video Demo Script",
        author="UPV EDM 2024-25",
    )

    story = []

    # ── Cover ───────────────────────────────────────────────────────────────
    story.append(sp(20))
    story.append(P("ValenciaRisk", "title"))
    story.append(P("Heat Vulnerability Intelligence Platform", "subtitle"))
    story.append(P("Video Demo Script — Max 5 Minutes", "subtitle"))
    story.append(sp(6))
    story.append(P("https://valenciarisk.streamlit.app", "url"))
    story.append(P("https://github.com/VICENTE102/valenciarisk", "url"))
    story.append(hr(RED, 2))
    story.append(sp(6))

    # Assignment note
    note_data = [[
        P("<b>Assignment requirement:</b> A link to a video of the team with a demo "
          "of the app. The video should explain the benefits of the application as "
          "well as the methodology and details employed to build the app. Max 5 minutes.", "body")
    ]]
    note_t = Table(note_data, colWidths=[16.5*cm])
    note_t.setStyle(TableStyle([
        ("BOX",         (0,0),(-1,-1), 0.8, RED),
        ("BACKGROUND",  (0,0),(-1,-1), colors.HexColor("#FFF5F5")),
        ("TOPPADDING",  (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
    ]))
    story.append(note_t)
    story.append(sp(14))

    # ── Timing overview table ───────────────────────────────────────────────
    story.append(P("TIMING OVERVIEW", "section"))
    story.append(hr(RED, 0.5))

    rows = [
        ["#", "Section", "Speaker", "Duration", "Cumulative"],
        ["1", "Hook + Urban Problem",        "A", "0:40", "0:40"],
        ["2", "Benefits of the Application", "B", "0:35", "1:15"],
        ["3", "Data Sources",                "C", "0:25", "1:40"],
        ["4", "DS Methodology & Details",    "B", "0:40", "2:20"],
        ["5", "Live Demo — Overview Map",    "A", "0:30", "2:50"],
        ["6", "Live Demo — Explorer",        "C", "0:25", "3:15"],
        ["7", "Live Demo — Typologies",      "A", "0:20", "3:35"],
        ["8", "Live Demo — Action Plan",     "B", "0:35", "4:10"],
        ["9", "Benefits — Summary",          "C", "0:20", "4:30"],
        ["10","Limitations + Closing",       "A", "0:30", "5:00"],
    ]
    col_w = [0.6*cm, 6.8*cm, 2*cm, 2.2*cm, 2.4*cm]
    t = Table(rows, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  RED),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
        ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F7F7F7")]),
        ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("ALIGN",        (1,0), (1,-1),  "LEFT"),
    ]))
    story.append(t)
    story.append(sp(12))

    # ── Production notes ───────────────────────────────────────────────────
    story.append(P("PRODUCTION NOTES", "section"))
    story.append(hr(RED, 0.5))
    notes = [
        "<b>Recording tool:</b> OBS Studio (free) / Loom / Teams screen recording.",
        "<b>Resolution:</b> 1920x1080. Browser at 90% zoom. Dark theme active.",
        "<b>App URL:</b> https://valenciarisk.streamlit.app — open before recording.",
        "<b>App state:</b> Page 1 loaded · Natzaret pre-selected on Page 2 · "
        "Weight sliders at defaults (40/30/30) · Simulator set to 30,000 m².",
        "<b>Key numbers to memorise:</b> 85 barris · 4 clusters · silhouette 0.455 · "
        "Pearson r = −0.39 (p = 0.0003) · OLS R² = 0.34 · "
        "Natzaret HVI = 0.943 rank #1 · green gap 87,000 m² · −8.7 °C cooling.",
    ]
    for n in notes:
        story.append(P(f"• {n}", "body"))
    story.append(sp(10))

    # ── Full script ────────────────────────────────────────────────────────
    story.append(P("FULL SCRIPT", "section"))
    story.append(hr(RED, 1.5))
    story.append(sp(4))

    # Section 1
    story += section_block(
        "SECTION 1 — Hook + Urban Problem",
        "Speaker A",
        "0:00 – 0:40  (40 seconds)",
        "Title card: '🔴 ValenciaRisk · Heat Vulnerability Intelligence Platform' on dark "
        "background. After 3 seconds, cut to live app — Page 1, choropleth map fully loaded.",
        [
            "In November 2024, Valencia suffered a catastrophic flood that shocked the world.",
            "But the city faces a second, slower crisis every single summer — extreme urban heat.",
            "In the European heat waves of 2022 and 2023, Spain recorded thousands of excess "
            "deaths. Those deaths were not evenly distributed.",
            "Dense, under-vegetated, socioeconomically fragile neighbourhoods suffered the most "
            "— while city planners had no single tool to identify them, rank them, or decide "
            "where to invest first.",
            "That is the problem ValenciaRisk was built to solve.",
        ]
    )

    # Section 2 — BENEFITS
    story += section_block(
        "SECTION 2 — Benefits of the Application",
        "Speaker B",
        "0:40 – 1:15  (35 seconds)",
        "Stay on Page 1. Point to the red neighbourhoods on the choropleth map, "
        "then highlight the 4 KPI cards at the top.",
        [
            "ValenciaRisk gives Valencia's city government something it did not have before: "
            "a single, transparent tool that answers one question a city councillor can act "
            "on immediately — which neighbourhoods need heat resilience investment first, and why.",
            "For city planners, it provides a ranked, evidence-based priority list ready to hand "
            "to a tree-planting contractor or a cooling-centre placement committee.",
            "For health departments, it activates a neighbourhood risk map before a heat wave "
            "— no manual analysis, no expert consultation required.",
            "And for citizens, it is a transparent public tool anyone can open in a browser, "
            "check their own neighbourhood score, and use as evidence when requesting "
            "improvements from their local council.",
            "The app is free, deployed online, and fully open source on GitHub.",
        ]
    )

    # Section 3 — DATA SOURCES
    story += section_block(
        "SECTION 3 — Data Sources",
        "Speaker C",
        "1:15 – 1:40  (25 seconds)",
        "Navigate to Page 5 — Methodology. Scroll slowly to the data sources table.",
        [
            "All data comes from verified public sources.",
            "Neighbourhood boundaries come from OpenStreetMap. Green zones and health "
            "centres from the Valencia Open Data portal. Land Surface Temperature from "
            "NASA's MODIS satellite product, pre-aggregated per neighbourhood.",
            "Population data comes from the INE Padron Municipal. Where live satellite "
            "data was not yet processed, we used carefully calibrated synthetic data — "
            "always clearly labelled inside the app, with every assumption documented "
            "on this methodology page.",
        ]
    )

    # Section 4 — METHODOLOGY
    story += section_block(
        "SECTION 4 — Data Science Methodology & Technical Details",
        "Speaker B",
        "1:40 – 2:20  (40 seconds)",
        "Stay on Page 5. Show the HVI formula, then scroll to the statistical "
        "validation section — point to the R² and Pearson r values.",
        [
            "The Data Science pipeline has four components.",
            "First: three normalised sub-scores per neighbourhood — heat exposure from "
            "satellite surface temperature, green-space deficit against the WHO standard "
            "of nine square metres per resident, and social vulnerability from the INE "
            "Urban Vulnerability Atlas. All normalised zero-to-one using Min-Max scaling "
            "and combined into a weighted HVI score.",
            "Second: K-Means clustering — four clusters — groups all 85 neighbourhoods "
            "into vulnerability typologies. Our silhouette score is 0.455, confirming "
            "good cluster separation.",
            "Third: OLS regression of surface temperature on green cover gives an "
            "R-squared of 0.34. The Pearson correlation between temperature and green "
            "cover is negative 0.39, p-value 0.0003 — statistically significant evidence "
            "that more green space means lower temperatures.",
            "Fourth: Moran's I confirms that vulnerability is spatially concentrated, "
            "so the city can target compact geographic zones rather than scattered points.",
            "The entire pipeline — download, clean, model, deploy — is reproducible "
            "from the open-source GitHub repository.",
        ]
    )

    # Section 5 — DEMO Overview
    story += section_block(
        "SECTION 5 — Live Demo: City Overview",
        "Speaker A",
        "2:20 – 2:50  (30 seconds)",
        "Navigate to Page 1. Hover over a red neighbourhood to show the tooltip. "
        "Point to the four KPI cards.",
        [
            "This is the City Overview. Every neighbourhood is coloured from green — "
            "low risk — to red — critical risk. Hovering shows the exact HVI score, "
            "heat, green deficit, social score, and population.",
            "The four cards at the top give the decision-maker the headline numbers "
            "instantly: four neighbourhoods at critical risk, over 20,000 residents "
            "directly affected.",
            "The distribution chart confirms the skew — a small number of neighbourhoods "
            "carry a disproportionate share of the burden. That is exactly where "
            "investment should go.",
        ]
    )

    # Section 6 — DEMO Explorer
    story += section_block(
        "SECTION 6 — Live Demo: Neighbourhood Explorer",
        "Speaker C",
        "2:50 – 3:15  (25 seconds)",
        "Navigate to Page 2. Natzaret is pre-selected. Show the CRITICAL banner, "
        "the radar chart, then scroll to the green gap metrics.",
        [
            "Let us look at Natzaret — ranked number one out of 85 neighbourhoods "
            "with an HVI of 0.943.",
            "The radar chart shows why immediately: maximum heat exposure, maximum "
            "green deficit, and high social vulnerability — all at once.",
            "This neighbourhood needs 87,000 additional square metres of green space "
            "to reach the WHO standard. Closing that gap would reduce local temperatures "
            "by an estimated 8.7 degrees Celsius. That is a precise, quantified "
            "investment target the city can take directly to its budget.",
        ]
    )

    # Section 7 — DEMO Clusters
    story += section_block(
        "SECTION 7 — Live Demo: Vulnerability Typologies",
        "Speaker A",
        "3:15 – 3:35  (20 seconds)",
        "Navigate to Page 3. Click 'Triple Burden' (Cluster 0) in the selector. "
        "Point to the cluster map colours.",
        [
            "The Typologies page groups all 85 neighbourhoods into four profiles "
            "using K-Means clustering.",
            "The red cluster — Triple Burden — six neighbourhoods that score high "
            "on heat, green deficit, and social vulnerability simultaneously. "
            "These are the most urgent cases city-wide.",
            "The scatter plot below confirms the core scientific finding: "
            "the negative relationship between green cover and surface temperature "
            "is clear and statistically significant.",
        ]
    )

    # Section 8 — DEMO Action Plan
    story += section_block(
        "SECTION 8 — Live Demo: City Action Plan + Simulator",
        "Speaker B",
        "3:35 – 4:10  (35 seconds)",
        "Navigate to Page 4. Show the red alert banner. Expand priority #1 — Natzaret. "
        "Then scroll to the Intervention Simulator and move the slider to 30,000 m².",
        [
            "This is the page a city councillor opens at the start of a budget meeting.",
            "Clicking the top priority — Natzaret — expands specific, actionable "
            "recommendations: how many square metres of trees to plant, whether a "
            "cooling centre should open, and how many elderly residents need a "
            "health alert protocol.",
            "And this is where the tool becomes a genuine decision simulator. "
            "I add 30,000 square metres of green space — the equivalent of four "
            "football pitches — and the HVI updates in real time.",
            "The city can test any investment scenario before committing a single "
            "euro of public money.",
        ]
    )

    # Section 9 — BENEFITS SUMMARY
    story += section_block(
        "SECTION 9 — Benefits Summary",
        "Speaker C",
        "4:10 – 4:30  (20 seconds)",
        "Return to Page 1. Slowly pan across the choropleth map.",
        [
            "To summarise the benefits: ValenciaRisk turns fragmented open data into "
            "a ranked, transparent, actionable priority list.",
            "It reduces the time a city health department needs to identify at-risk "
            "neighbourhoods from days to seconds.",
            "It gives citizens a public tool to hold their local council accountable.",
            "And it provides evaluators — and city managers — with a fully documented, "
            "reproducible methodology they can trust, challenge, and improve.",
        ]
    )

    # Section 10 — LIMITATIONS + CLOSING
    story += section_block(
        "SECTION 10 — Limitations + Closing",
        "Speaker A",
        "4:30 – 5:00  (30 seconds)",
        "Show Page 5 — open the Limitations expander. Last 4 seconds: closing title card "
        "with app URL, GitHub link, and team names.",
        [
            "We are honest about the limitations. The social vulnerability index uses "
            "2011 census data — neighbourhoods that have changed since then may be "
            "misrepresented. The Land Surface Temperature uses synthetic data calibrated "
            "to Valencia's urban heat patterns — not yet live satellite readings. "
            "And the cooling benefit is a literature estimate, not a local model.",
            "All of this is documented inside the app.",
            "ValenciaRisk is a starting point for evidence-based decisions — "
            "not a substitute for field investigation.",
            "The data already existed. The need already existed. "
            "The only thing missing was putting them together.",
            "ValenciaRisk does exactly that.",
        ]
    )

    # ── Closing title card description ─────────────────────────────────────
    story.append(P("CLOSING TITLE CARD (last 4 seconds on screen)", "section"))
    story.append(hr(RED, 0.5))
    card_lines = [
        "🔴 ValenciaRisk",
        "Heat Vulnerability Intelligence Platform",
        "",
        "https://valenciarisk.streamlit.app",
        "https://github.com/VICENTE102/valenciarisk",
        "",
        "Built with open data  ·  UPV EDM 2024–25",
        "[Names of team members]",
    ]
    for line in card_lines:
        story.append(P(line if line else "&nbsp;", "cue"))
    story.append(sp(14))

    # ── Speaker cue sheet ──────────────────────────────────────────────────
    story.append(P("SPEAKER CUE SHEET  (print and tape to monitor)", "section"))
    story.append(hr(RED, 0.5))
    cues = [
        ["00:00", "A", "\"In November 2024...\"",           "Title card → Page 1"],
        ["00:40", "B", "\"ValenciaRisk gives Valencia...\"","Page 1 — map + KPIs"],
        ["01:15", "C", "\"All data comes from...\"",        "Page 5 — data table"],
        ["01:40", "B", "\"The Data Science pipeline...\"",  "Page 5 — formula + stats"],
        ["02:20", "A", "\"This is the City Overview...\"",  "Page 1 — hover tooltip"],
        ["02:50", "C", "\"Let us look at Natzaret...\"",    "Page 2 — Natzaret"],
        ["03:15", "A", "\"The Typologies page...\"",        "Page 3 — cluster map"],
        ["03:35", "B", "\"This is the page a councillor...\"","Page 4 — expand #1"],
        ["04:10", "C", "\"To summarise the benefits...\"",  "Page 1 — pan map"],
        ["04:30", "A", "\"We are honest...\"",              "Page 5 — limitations"],
        ["04:56", "—", "[Closing title card]",              ""],
        ["05:00", "—", "STOP",                              ""],
    ]
    col_w2 = [1.4*cm, 1*cm, 8.5*cm, 5.6*cm]
    t2 = Table(cues, colWidths=col_w2)
    t2.setStyle(TableStyle([
        ("FONTNAME",     (0,0),(-1,-1), "Courier"),
        ("FONTSIZE",     (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, colors.HexColor("#F7F7F7")]),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TEXTCOLOR",    (0,0),(0,-1),  RED),
        ("FONTNAME",     (0,0),(0,-1),  "Courier-Bold"),
        ("TEXTCOLOR",    (1,0),(1,-1),  colors.HexColor("#1166CC")),
        ("FONTNAME",     (1,0),(1,-1),  "Courier-Bold"),
    ]))
    story.append(t2)
    story.append(sp(10))

    # ── Key numbers reference ──────────────────────────────────────────────
    story.append(P("KEY NUMBERS TO MEMORISE", "section"))
    story.append(hr(RED, 0.5))
    numbers = [
        ["Metric", "Value"],
        ["Total barris analysed", "85"],
        ["K-Means clusters", "4"],
        ["Silhouette score", "0.455"],
        ["Pearson r  (LST vs green cover)", "−0.39  (p = 0.0003)"],
        ["OLS R²  (LST ~ green + density)", "0.34"],
        ["Barris at critical risk (HVI > 0.65)", "4"],
        ["Residents at critical risk", "20,360"],
        ["Natzaret — HVI score", "0.943  (rank #1 of 85)"],
        ["Natzaret — green gap", "87,000 m²  (≈ 12 football pitches)"],
        ["Natzaret — estimated cooling", "−8.7 °C if gap closed"],
        ["App URL", "https://valenciarisk.streamlit.app"],
        ["GitHub URL", "https://github.com/VICENTE102/valenciarisk"],
    ]
    col_w3 = [8*cm, 8.5*cm]
    t3 = Table(numbers, colWidths=col_w3)
    t3.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0),  RED),
        ("TEXTCOLOR",    (0,0),(-1,0),  colors.white),
        ("FONTNAME",     (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,-1), 8.5),
        ("FONTNAME",     (0,1),(-1,-1), "Helvetica"),
        ("FONTNAME",     (1,1),(1,-1),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F7F7F7")]),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",   (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(t3)
    story.append(sp(8))
    story.append(P(
        "This script was generated automatically from the deployed ValenciaRisk application. "
        "All statistics reflect the real model output (synthetic data pipeline, June 2025).",
        "note"
    ))

    doc.build(story)
    print(f"PDF saved -> {OUT}")


if __name__ == "__main__":
    build()
