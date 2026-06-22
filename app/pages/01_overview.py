"""Page 1 — City Overview: choropleth map, KPIs, distribution, top-10 table."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit_folium import st_folium

from components.charts import hvi_histogram, priority_bar
from components.kpi_cards import render_kpi_row
from components.maps import choropleth_map
from utils.data_loader import load_barris_hvi
from utils.scoring import recompute_hvi

# ── Load & filter data ─────────────────────────────────────────────────────
gdf_raw = load_barris_hvi()

w_heat   = st.session_state.get("w_heat",   40) / 100
w_green  = st.session_state.get("w_green",  30) / 100
w_social = st.session_state.get("w_social", 30) / 100
gdf = recompute_hvi(gdf_raw, w_heat, w_green, w_social)

district = st.session_state.get("district_filter", "Tots")
if district != "Tots":
    gdf = gdf[gdf["districte_name"] == district].copy()

if st.session_state.get("show_high_risk_only", False):
    gdf = gdf[gdf["hvi"] > 0.65].copy()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🗺️ Visió General de la Ciutat")
st.markdown(
    "L'**Índex de Vulnerabilitat a la Calor (HVI)** combina exposició tèrmica, "
    "dèficit de zones verdes i vulnerabilitat social per identificar els barris "
    "que necessiten atenció prioritària."
)

if gdf_raw["data_type"].eq("synthetic").any():
    st.info(
        "ℹ️ Algunes dades (LST, població) són sintètiques calibrades amb demografia "
        "real de València. Consulta la metodologia per més detalls.",
        icon="ℹ️",
    )

# ── KPIs ──────────────────────────────────────────────────────────────────
render_kpi_row(gdf)
st.divider()

# ── Map + Top-10 ──────────────────────────────────────────────────────────
col_map, col_table = st.columns([3, 2], gap="medium")

with col_map:
    st.subheader("Mapa d'Índex HVI per barri")
    m = choropleth_map(gdf, column="hvi", title="HVI — Vulnerabilitat a la Calor")
    st_folium(m, width="100%", height=460, returned_objects=[])

with col_table:
    st.subheader("Top 10 barris més vulnerables")
    top10 = (
        gdf.nsmallest(10, "priority_rank")[
            ["priority_rank", "barri_name", "districte_name",
             "hvi", "heat_score", "green_deficit_score", "social_score", "pop_total"]
        ]
        .rename(columns={
            "priority_rank": "#",
            "barri_name": "Barri",
            "districte_name": "Districte",
            "hvi": "HVI",
            "heat_score": "Calor",
            "green_deficit_score": "Dèficit verd",
            "social_score": "Social",
            "pop_total": "Habitants",
        })
    )
    st.dataframe(
        top10.style.background_gradient(subset=["HVI"], cmap="RdYlGn_r"),
        use_container_width=True,
        hide_index=True,
    )
    csv = gdf.drop(columns="geometry").to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descarregar ranking complet (CSV)",
        data=csv,
        file_name="valenciarisk_ranking.csv",
        mime="text/csv",
    )

st.divider()

# ── Distribution chart ─────────────────────────────────────────────────────
st.subheader("Distribució de puntuacions HVI")
col_hist, col_bar = st.columns(2)
with col_hist:
    st.plotly_chart(hvi_histogram(gdf), use_container_width=True)
with col_bar:
    st.plotly_chart(priority_bar(gdf, top_n=15), use_container_width=True)
