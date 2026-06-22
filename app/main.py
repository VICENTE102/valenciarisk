"""
ValenciaRisk — Heat Vulnerability Intelligence Platform
Entry point: streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make app/ importable from any working directory
_APP_DIR = Path(__file__).parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st

st.set_page_config(
    page_title="ValenciaRisk",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**ValenciaRisk** — Urban Heat Vulnerability Platform\n\n"
            "Built with open data from Valencia and public satellite products."
        )
    },
)

# ── Session-state defaults ─────────────────────────────────────────────────
_DEFAULTS = {
    "w_heat":       40,
    "w_green":      30,
    "selected_barri": None,
    "show_high_risk_only": False,
    "district_filter": "Tots",
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar (shared across all pages) ─────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='color:#E63946;margin-bottom:0'>🔴 ValenciaRisk</h2>"
        "<p style='color:#888;font-size:0.8em;margin-top:0'>"
        "Heat Vulnerability Intelligence</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # District filter
    from utils.data_loader import load_barris_hvi  # noqa: PLC0415
    _gdf_all = load_barris_hvi()
    districts = ["Tots"] + sorted(_gdf_all["districte_name"].dropna().unique().tolist())
    st.session_state["district_filter"] = st.selectbox(
        "📍 Districte",
        options=districts,
        index=districts.index(st.session_state["district_filter"])
        if st.session_state["district_filter"] in districts else 0,
    )

    st.session_state["show_high_risk_only"] = st.toggle(
        "Mostrar només risc alt (HVI > 0.65)",
        value=st.session_state["show_high_risk_only"],
    )

    st.divider()
    st.markdown("### ⚖️ Pesos de vulnerabilitat")
    st.caption(
        "Ajusta els pesos per reflectir les teves prioritats de política. "
        "El pes Social s'ajusta automàticament."
    )

    w_heat = st.slider(
        "🌡️ Exposició calor", 0, 90,
        value=st.session_state["w_heat"], step=5,
    )
    max_green = 100 - w_heat
    w_green = st.slider(
        "🌿 Dèficit verd", 0, max_green,
        value=min(st.session_state["w_green"], max_green), step=5,
    )
    w_social = 100 - w_heat - w_green

    st.session_state["w_heat"]  = w_heat
    st.session_state["w_green"] = w_green
    st.session_state["w_social"] = w_social

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Calor",  f"{w_heat}%")
    col_b.metric("Verd",   f"{w_green}%")
    col_c.metric("Social", f"{w_social}%")

    if st.button("↩ Restablir pesos"):
        st.session_state["w_heat"]  = 40
        st.session_state["w_green"] = 30
        st.session_state["w_social"] = 30
        st.rerun()

    st.divider()
    st.markdown("#### 📅 Fonts de dades")
    st.caption(
        "- LST: MODIS 2023 (sintètica si no disponible)\n"
        "- Població: INE Padrón 2023 (sintètica)\n"
        "- Zones verdes: Valencia Open Data\n"
        "- IVU: INE Atlas Vulnerabilitat 2011"
    )

# ── Navigation ─────────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "Anàlisi": [
            st.Page("pages/01_overview.py",
                    title="Visió general", icon="🗺️"),
            st.Page("pages/02_explorer.py",
                    title="Explorador de barris", icon="🔍"),
            st.Page("pages/03_clustering.py",
                    title="Tipologies", icon="🔵"),
            st.Page("pages/04_recommendations.py",
                    title="Pla d'acció", icon="🎯"),
        ],
        "Transparència": [
            st.Page("pages/05_methodology.py",
                    title="Metodologia", icon="📐"),
        ],
    }
)
pg.run()
