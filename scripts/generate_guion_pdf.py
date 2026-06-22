"""
Genera el guion del video de ValenciaRisk en español como PDF.
Output: valenciarisk_guion_video.pdf (raiz del proyecto)
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

OUT = Path(__file__).parent.parent / "valenciarisk_guion_video.pdf"

RED      = colors.HexColor("#E63946")
NAVY     = colors.HexColor("#0F1923")
GREY     = colors.HexColor("#888888")
GREEN    = colors.HexColor("#06D6A0")
LIGHTBG  = colors.HexColor("#FFF5F5")
ROWALT   = colors.HexColor("#F7F7F7")

base = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, parent=base["Normal"], **kw)

STYLES = {
    "title":    S("title",    fontSize=24, textColor=RED,   fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4),
    "subtitle": S("subtitle", fontSize=11, textColor=GREY,  fontName="Helvetica",      alignment=TA_CENTER, spaceAfter=3),
    "url":      S("url",      fontSize=9,  textColor=GREEN, fontName="Helvetica",      alignment=TA_CENTER, spaceAfter=14),
    "section":  S("section",  fontSize=13, textColor=RED,   fontName="Helvetica-Bold", spaceBefore=16, spaceAfter=4),
    "meta":     S("meta",     fontSize=8.5,textColor=GREY,  fontName="Helvetica-Bold", spaceAfter=2),
    "screen":   S("screen",   fontSize=8.5,textColor=colors.HexColor("#4455AA"), fontName="Helvetica-Oblique",
                              leading=12, leftIndent=12, spaceAfter=4),
    "body":     S("body",     fontSize=9.5,textColor=colors.black, fontName="Helvetica",
                              leading=14, spaceAfter=3, alignment=TA_JUSTIFY),
    "dialog":   S("dialog",   fontSize=10, textColor=NAVY,  fontName="Helvetica-Oblique",
                              leading=15, leftIndent=16, spaceAfter=4, alignment=TA_JUSTIFY),
    "note":     S("note",     fontSize=8,  textColor=GREY,  fontName="Helvetica-Oblique", leading=11, spaceAfter=4),
    "cue":      S("cue",      fontSize=9,  textColor=colors.black, fontName="Courier", leading=13, spaceAfter=2),
    "final":    S("final",    fontSize=10, textColor=GREEN, fontName="Courier-Bold",  leading=15, alignment=TA_CENTER, spaceAfter=3),
}

def hr(color=RED, thickness=0.7):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)

def sp(h=6):
    return Spacer(1, h)

def P(text, style="body"):
    return Paragraph(text, STYLES[style])


SECTIONS = [
    {
        "num": "01",
        "title": "Introducción y problema urbano",
        "speaker": "Speaker A",
        "timing": "0:00 – 0:40  (40 segundos)",
        "screen": "Pantalla: tarjeta de título → Página 1, mapa coroplético cargado.",
        "lines": [
            "En noviembre de 2024, Valencia vivió una catástrofe que sacudió al mundo entero. "
            "Pero la ciudad enfrenta cada verano una segunda crisis, más silenciosa: el calor "
            "urbano extremo.",

            "En las olas de calor de 2022 y 2023, España registró miles de muertes por exceso "
            "de temperatura. Esas muertes no se distribuyeron al azar. Los barrios más densos, "
            "con menos zonas verdes y mayor vulnerabilidad social fueron los que más sufrieron.",

            "Hasta ahora, los planificadores de la ciudad no tenían una herramienta única para "
            "identificar esos barrios, priorizarlos, y decidir dónde invertir primero. "
            "ValenciaRisk existe para resolver exactamente ese problema.",
        ],
    },
    {
        "num": "02",
        "title": "Beneficios de la aplicación",
        "speaker": "Speaker B",
        "timing": "0:40 – 1:15  (35 segundos)",
        "screen": "Pantalla: Página 1 — mapa + 4 tarjetas KPI en la parte superior.",
        "lines": [
            "ValenciaRisk da al Ayuntamiento de Valencia algo que no tenía: una herramienta "
            "transparente que responde en segundos la pregunta que importa — ¿qué barrios "
            "necesitan intervención urgente contra el calor, y por qué?",

            "Para urbanistas y técnicos municipales: una lista priorizada y basada en evidencia, "
            "lista para pasarle a un equipo de plantación de árboles o a un comité de centros "
            "de climatización.",

            "Para los servicios de salud: un mapa de riesgo por barrio activable antes de una "
            "ola de calor, sin necesitar análisis manuales ni consultar a un experto.",

            "Y para los ciudadanos: una herramienta pública que cualquier vecino puede abrir "
            "en el móvil, consultar su barrio, y usar como argumento ante su ayuntamiento "
            "para pedir mejoras.",

            "La app es gratuita, está desplegada online, y todo el código es open source "
            "en GitHub.",
        ],
    },
    {
        "num": "03",
        "title": "Fuentes de datos",
        "speaker": "Speaker C",
        "timing": "1:15 – 1:40  (25 segundos)",
        "screen": "Pantalla: Página 5 (Metodología) — desplazarse lentamente hasta la tabla de fuentes.",
        "lines": [
            "Todos los datos provienen de fuentes públicas verificadas.",

            "Los límites de los barrios vienen de OpenStreetMap. Las zonas verdes y centros de "
            "salud del portal Open Data del Ayuntamiento de Valencia. La temperatura superficial "
            "del suelo, del satélite MODIS de la NASA.",

            "Los datos de población proceden del Padrón Municipal del INE. Donde los datos en "
            "tiempo real aún no estaban procesados, usamos datos sintéticos cuidadosamente "
            "calibrados — siempre etiquetados claramente dentro de la app, con cada supuesto "
            "documentado en esta página de metodología.",
        ],
    },
    {
        "num": "04",
        "title": "Metodología Data Science y detalles técnicos",
        "speaker": "Speaker B",
        "timing": "1:40 – 2:20  (40 segundos)",
        "screen": "Pantalla: Página 5 — fórmula HVI, luego métricas estadísticas (R², Pearson r).",
        "lines": [
            "El pipeline de Data Science tiene cuatro componentes.",

            "Primero: tres sub-índices normalizados por barrio — exposición al calor mediante "
            "temperatura superficial del satélite, déficit de zona verde respecto al estándar "
            "OMS de 9 metros cuadrados por habitante, y vulnerabilidad social del Atlas de "
            "Vulnerabilidad Urbana del INE. Todo normalizado entre 0 y 1 con Min-Max y "
            "combinado en un índice HVI ponderado.",

            "Segundo: clustering K-Means con cuatro grupos agrupa los 85 barrios en tipologías "
            "de vulnerabilidad. Nuestro coeficiente de silueta es 0,455, confirmando buena "
            "separación entre grupos.",

            "Tercero: una regresión OLS de temperatura sobre cobertura verde da un R² de 0,34. "
            "La correlación de Pearson entre temperatura y zonas verdes es menos 0,39 con un "
            "p-valor de 0,0003 — evidencia estadísticamente significativa de que más verde "
            "significa menos calor.",

            "Cuarto: el índice de Moran I confirma que la vulnerabilidad está espacialmente "
            "concentrada, permitiendo focalizar intervenciones en zonas geográficas compactas.",

            "Todo el pipeline es reproducible desde el repositorio open source en GitHub.",
        ],
    },
    {
        "num": "05",
        "title": "Demo en vivo: Mapa general de la ciudad",
        "speaker": "Speaker A",
        "timing": "2:20 – 2:50  (30 segundos)",
        "screen": "Pantalla: Página 1 — hover sobre barrio rojo (tooltip), luego señalar KPIs.",
        "lines": [
            "Este es el panel principal. Cada barrio está coloreado de verde — bajo riesgo — "
            "a rojo — riesgo crítico. Al pasar el ratón vemos el índice HVI exacto, "
            "la puntuación de calor, déficit verde, vulnerabilidad social y población.",

            "Las cuatro tarjetas superiores dan al decisor los datos clave de un vistazo: "
            "cuatro barrios en riesgo crítico, más de 20.000 residentes directamente afectados.",

            "El histograma de distribución confirma lo esperado: unos pocos barrios concentran "
            "una carga desproporcionada. Exactamente ahí debe ir la inversión.",
        ],
    },
    {
        "num": "06",
        "title": "Demo en vivo: Explorer de barrio — Natzaret",
        "speaker": "Speaker C",
        "timing": "2:50 – 3:15  (25 segundos)",
        "screen": "Pantalla: Página 2 — Natzaret seleccionado, banner CRÍTICO visible, gráfico radar.",
        "lines": [
            "Veamos Natzaret: el barrio número uno de los 85, con un HVI de 0,943.",

            "El gráfico radar lo explica de inmediato: exposición al calor máxima, déficit "
            "de zonas verdes máximo, y alta vulnerabilidad social — todo al mismo tiempo.",

            "Este barrio necesita 87.000 metros cuadrados adicionales de zonas verdes para "
            "alcanzar el estándar OMS. Cerrar esa brecha reduciría la temperatura local en "
            "8,7 grados Celsius. Eso es un objetivo de inversión concreto y cuantificado, "
            "listo para llevar al presupuesto municipal.",
        ],
    },
    {
        "num": "07",
        "title": "Demo en vivo: Tipologías de vulnerabilidad",
        "speaker": "Speaker A",
        "timing": "3:15 – 3:35  (20 segundos)",
        "screen": "Pantalla: Página 3 — mapa de clusters, seleccionar 'Triple Carga' (cluster 0).",
        "lines": [
            "La página de tipologías agrupa los 85 barrios en cuatro perfiles usando K-Means.",

            "El cluster rojo — Triple Carga — son 6 barrios que puntúan alto en calor, déficit "
            "verde y vulnerabilidad social simultáneamente. Son los casos más urgentes de "
            "toda la ciudad.",

            "El diagrama de dispersión confirma el hallazgo científico principal: la relación "
            "negativa entre cobertura verde y temperatura superficial es clara y "
            "estadísticamente significativa.",
        ],
    },
    {
        "num": "08",
        "title": "Demo en vivo: Plan de acción + Simulador",
        "speaker": "Speaker B",
        "timing": "3:35 – 4:10  (35 segundos)",
        "screen": "Pantalla: Página 4 — expandir prioridad #1 Natzaret, luego mover slider a 30.000 m².",
        "lines": [
            "Esta es la página que un concejal abre al inicio de una reunión de presupuesto.",

            "Al expandir la prioridad número uno — Natzaret — aparecen recomendaciones "
            "específicas y accionables: cuántos metros cuadrados de arbolado plantar, si debe "
            "abrirse un centro de climatización, cuántos residentes mayores necesitan un "
            "protocolo de alerta sanitaria.",

            "Y aquí la herramienta se convierte en un simulador real. Añado 30.000 metros "
            "cuadrados de zonas verdes — el equivalente a cuatro campos de fútbol — y el HVI "
            "se actualiza en tiempo real.",

            "La ciudad puede probar cualquier escenario de inversión antes de comprometer "
            "un solo euro de dinero público.",
        ],
    },
    {
        "num": "09",
        "title": "Resumen de beneficios",
        "speaker": "Speaker C",
        "timing": "4:10 – 4:30  (20 segundos)",
        "screen": "Pantalla: Página 1 — panorámica lenta del mapa coroplético.",
        "lines": [
            "En resumen: ValenciaRisk convierte datos públicos fragmentados en una lista de "
            "prioridades transparente y accionable.",

            "Reduce de días a segundos el tiempo que necesita un departamento de salud para "
            "identificar barrios en riesgo.",

            "Da a los ciudadanos una herramienta pública para exigir rendición de cuentas "
            "a su ayuntamiento.",

            "Y ofrece a los evaluadores una metodología completamente documentada, "
            "reproducible y de código abierto.",
        ],
    },
    {
        "num": "10",
        "title": "Limitaciones y cierre",
        "speaker": "Speaker A",
        "timing": "4:30 – 5:00  (30 segundos)",
        "screen": "Pantalla: Página 5 — abrir expander de Limitaciones → tarjeta de cierre final.",
        "lines": [
            "Somos honestos sobre las limitaciones. El índice de vulnerabilidad social usa "
            "datos del censo de 2011 — barrios que han cambiado mucho desde entonces pueden "
            "estar mal representados. La temperatura superficial usa datos sintéticos "
            "calibrados al patrón climático de Valencia, no lecturas satelitales en tiempo "
            "real. Y el beneficio de enfriamiento es una estimación de la literatura "
            "científica, no un modelo local validado en campo.",

            "Todo esto está documentado dentro de la app.",

            "ValenciaRisk es un punto de partida para decisiones basadas en evidencia — "
            "no un sustituto de la investigación de campo.",

            "Los datos ya existían. La necesidad ya existía. "
            "Lo único que faltaba era ponerlos juntos.",

            "ValenciaRisk hace exactamente eso.",
        ],
    },
]


def build():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="ValenciaRisk — Guion Video Demo",
        author="UPV EDM 2024-25",
    )

    story = []

    # ── Portada ──────────────────────────────────────────────────────────────
    story.append(sp(18))
    story.append(P("ValenciaRisk", "title"))
    story.append(P("Heat Vulnerability Intelligence Platform", "subtitle"))
    story.append(P("GUION VIDEO DEMO — Máximo 5 minutos", "subtitle"))
    story.append(sp(6))
    story.append(P("https://valenciarisk.streamlit.app", "url"))
    story.append(P("https://github.com/VICENTE102/valenciarisk", "url"))
    story.append(hr(RED, 2))
    story.append(sp(8))

    # Caja de instruccion de entrega
    req = [[P(
        "<b>Requisito de entrega:</b> Un enlace a un video del equipo con una demo de la app. "
        "El video debe explicar los <b>beneficios de la aplicación</b>, así como la "
        "<b>metodología y detalles</b> empleados para construirla. Máximo 5 minutos.",
        "body"
    )]]
    t = Table(req, colWidths=[16.5*cm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.8, RED),
        ("BACKGROUND",   (0,0),(-1,-1), LIGHTBG),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(t)
    story.append(sp(16))

    # ── Tabla de tiempos ─────────────────────────────────────────────────────
    story.append(P("TABLA DE TIEMPOS", "section"))
    story.append(hr())

    rows = [["#", "Sección", "Speaker", "Duración", "Acumulado"]]
    timings = [
        ("01", "Introducción y problema",            "A", "0:40", "0:40"),
        ("02", "Beneficios de la aplicación",        "B", "0:35", "1:15"),
        ("03", "Fuentes de datos",                   "C", "0:25", "1:40"),
        ("04", "Metodología DS y detalles técnicos", "B", "0:40", "2:20"),
        ("05", "Demo: Mapa general",                 "A", "0:30", "2:50"),
        ("06", "Demo: Explorer — Natzaret",          "C", "0:25", "3:15"),
        ("07", "Demo: Tipologías",                   "A", "0:20", "3:35"),
        ("08", "Demo: Plan de acción + Simulador",   "B", "0:35", "4:10"),
        ("09", "Resumen de beneficios",              "C", "0:20", "4:30"),
        ("10", "Limitaciones y cierre",              "A", "0:30", "5:00"),
    ]
    rows += list(timings)

    t2 = Table(rows, colWidths=[0.8*cm, 7*cm, 1.8*cm, 2.2*cm, 2.4*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  RED),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, ROWALT]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("ALIGN",         (1,0), (1,-1),  "LEFT"),
    ]))
    story.append(t2)
    story.append(sp(16))

    # ── Notas de producción ──────────────────────────────────────────────────
    story.append(P("NOTAS DE GRABACIÓN", "section"))
    story.append(hr())
    notas = [
        "<b>Herramienta recomendada:</b> OBS Studio (gratuito) / Loom / grabación de Teams.",
        "<b>Resolución:</b> 1920×1080. Navegador al 90% de zoom. Tema oscuro activado.",
        "<b>URL de la app:</b> https://valenciarisk.streamlit.app — abrir y esperar carga completa antes de grabar.",
        "<b>Estado inicial:</b> Página 1 cargada · Natzaret preseleccionado en Página 2 · "
        "Sliders en valores por defecto (40/30/30) · Simulador a 30.000 m².",
        "<b>Números clave a memorizar:</b> 85 barrios · 4 clusters · silueta 0,455 · "
        "Pearson r = −0,39 (p = 0,0003) · OLS R² = 0,34 · "
        "Natzaret HVI = 0,943 (rank #1) · brecha verde 87.000 m² · −8,7 °C de enfriamiento.",
    ]
    for n in notas:
        story.append(P(f"• {n}", "body"))
    story.append(sp(14))

    # ── Guion completo ───────────────────────────────────────────────────────
    story.append(P("GUION COMPLETO", "section"))
    story.append(hr(RED, 1.5))
    story.append(sp(4))

    for sec in SECTIONS:
        block = []

        # Cabecera de sección
        block.append(P(
            f"SECCIÓN {sec['num']} — {sec['title'].upper()}",
            "section"
        ))
        block.append(hr(RED, 0.4))

        # Metadatos
        meta = [
            ["Speaker",  sec["speaker"]],
            ["Tiempo",   sec["timing"]],
        ]
        tm = Table(meta, colWidths=[2.2*cm, 14.3*cm])
        tm.setStyle(TableStyle([
            ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("TEXTCOLOR",     (0,0), (0,-1),  GREY),
            ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
            ("TEXTCOLOR",     (1,0), (1,-1),  colors.black),
            ("TOPPADDING",    (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        block.append(tm)
        block.append(sp(4))

        # Indicacion de pantalla
        block.append(P(f"<b>EN PANTALLA:</b> {sec['screen']}", "screen"))
        block.append(sp(3))

        # Dialogo
        block.append(P("<b>TEXTO:</b>", "meta"))
        for line in sec["lines"]:
            block.append(P(f'"{line}"', "dialog"))

        block.append(sp(10))
        story.append(KeepTogether(block))

    # ── Tarjeta de cierre ────────────────────────────────────────────────────
    story.append(P("TARJETA DE CIERRE (últimos 4 segundos en pantalla)", "section"))
    story.append(hr())
    cierre = [
        "🔴 ValenciaRisk",
        "Heat Vulnerability Intelligence Platform",
        " ",
        "https://valenciarisk.streamlit.app",
        "https://github.com/VICENTE102/valenciarisk",
        " ",
        "UPV · Eines de Data Management · 2024–25",
        "[Nombres del equipo]",
    ]
    for line in cierre:
        story.append(P(line, "cue"))
    story.append(sp(16))

    # ── Hoja de avisos ───────────────────────────────────────────────────────
    story.append(P("HOJA DE AVISOS  (imprimir y pegar en el monitor)", "section"))
    story.append(hr())
    cues = [
        ["00:00", "A", '"En noviembre de 2024..."',           "Título → Página 1"],
        ["00:40", "B", '"ValenciaRisk da al Ayuntamiento..."',"Página 1 — mapa + KPIs"],
        ["01:15", "C", '"Todos los datos provienen..."',      "Página 5 — tabla de datos"],
        ["01:40", "B", '"El pipeline de Data Science..."',    "Página 5 — fórmula + estadísticas"],
        ["02:20", "A", '"Este es el panel principal..."',     "Página 1 — hover tooltip"],
        ["02:50", "C", '"Veamos Natzaret..."',                "Página 2 — Natzaret"],
        ["03:15", "A", '"La página de tipologías..."',        "Página 3 — mapa de clusters"],
        ["03:35", "B", '"Esta es la página que un concejal..."', "Página 4 — expandir #1"],
        ["04:10", "C", '"En resumen: ValenciaRisk..."',       "Página 1 — panorámica"],
        ["04:30", "A", '"Somos honestos sobre las limitaciones..."', "Página 5 — limitaciones"],
        ["04:56", "—", "[Tarjeta de cierre]",                 ""],
        ["05:00", "—", "STOP",                                ""],
    ]
    cue_t = Table(cues, colWidths=[1.4*cm, 0.9*cm, 9*cm, 5.2*cm])
    cue_t.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (-1,-1), "Courier"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, ROWALT]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TEXTCOLOR",     (0,0), (0,-1),  RED),
        ("FONTNAME",      (0,0), (0,-1),  "Courier-Bold"),
        ("TEXTCOLOR",     (1,0), (1,-1),  colors.HexColor("#1166CC")),
        ("FONTNAME",      (1,0), (1,-1),  "Courier-Bold"),
    ]))
    story.append(cue_t)
    story.append(sp(10))

    # ── Números clave ────────────────────────────────────────────────────────
    story.append(P("NÚMEROS CLAVE A MEMORIZAR", "section"))
    story.append(hr())
    nums = [
        ["Métrica", "Valor"],
        ["Total barrios analizados",                "85"],
        ["Clusters K-Means",                        "4"],
        ["Coeficiente de silueta",                  "0,455"],
        ["Pearson r  (LST vs cobertura verde)",      "−0,39  (p = 0,0003)"],
        ["OLS R²  (LST ~ verde + densidad)",         "0,34"],
        ["Barrios en riesgo crítico (HVI > 0,65)",  "4"],
        ["Residentes en riesgo crítico",             "20.360"],
        ["Natzaret — puntuación HVI",               "0,943  (rank #1 de 85)"],
        ["Natzaret — brecha de zona verde",         "87.000 m²  (~12 campos de fútbol)"],
        ["Natzaret — enfriamiento estimado",        "−8,7 °C si se cierra la brecha"],
        ["URL de la app",                           "https://valenciarisk.streamlit.app"],
        ["URL de GitHub",                           "https://github.com/VICENTE102/valenciarisk"],
    ]
    num_t = Table(nums, colWidths=[8*cm, 8.5*cm])
    num_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  RED),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTNAME",      (1,1), (1,-1),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, ROWALT]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(num_t)
    story.append(sp(8))
    story.append(P(
        "Guion generado automáticamente desde la aplicación desplegada ValenciaRisk. "
        "Todas las estadísticas corresponden a la salida real del modelo (pipeline con "
        "datos sintéticos, junio 2025). UPV · Eines de Data Management · 2024–25.",
        "note"
    ))

    doc.build(story)
    print(f"PDF guardado -> {OUT}")


if __name__ == "__main__":
    build()
