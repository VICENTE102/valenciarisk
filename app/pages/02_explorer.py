"""Page 2 — Neighbourhood Explorer: deep-dive into a single barrio."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit_folium import st_folium

from components.charts import radar_chart, subscores_bar
from components.maps import neighbourhood_zoom_map
from utils.data_loader import load_barris_hvi
from utils.scoring import recompute_hvi, estimate_cooling_benefit, green_gap_m2

WHO_GREEN_M2 = 9.0

gdf_raw = load_barris_hvi()
w_heat   = st.session_state.get("w_heat",   40) / 100
w_green  = st.session_state.get("w_green",  30) / 100
w_social = st.session_state.get("w_social", 30) / 100
gdf = recompute_hvi(gdf_raw, w_heat, w_green, w_social)

city_avg = gdf[["heat_score", "green_deficit_score", "social_score"]].mean()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🔍 Explorador de Barris")
st.markdown(
    "Selecciona un barri per veure la descomposició completa del seu índex de "
    "vulnerabilitat i la recomanació d'intervenció específica."
)

# ── Selector ───────────────────────────────────────────────────────────────
barri_names = sorted(gdf["barri_name"].dropna().unique().tolist())
default_idx = 0
if st.session_state.get("selected_barri") in barri_names:
    default_idx = barri_names.index(st.session_state["selected_barri"])

selected_name = st.selectbox(
    "Cerca o selecciona un barri:",
    options=barri_names,
    index=default_idx,
    key="explorer_selector",
)
st.session_state["selected_barri"] = selected_name

row = gdf[gdf["barri_name"] == selected_name].iloc[0]

# ── HVI banner ─────────────────────────────────────────────────────────────
risk_colour = (
    "#E63946" if row["hvi"] > 0.65 else
    "#FFD166" if row["hvi"] > 0.40 else
    "#06D6A0"
)
risk_label = (
    "RISC ALT" if row["hvi"] > 0.65 else
    "RISC MITJÀ" if row["hvi"] > 0.40 else
    "RISC BAIX"
)
st.markdown(
    f"<div style='background:{risk_colour}22;border-left:4px solid {risk_colour};"
    f"padding:12px 16px;border-radius:6px;margin-bottom:16px'>"
    f"<span style='font-size:1.4em;font-weight:bold;color:{risk_colour}'>"
    f"{selected_name}</span>"
    f"&nbsp;&nbsp;<span style='background:{risk_colour};color:white;"
    f"padding:3px 10px;border-radius:4px;font-size:0.85em'>{risk_label}</span><br>"
    f"<span style='font-size:0.9em;color:#aaa'>Districte: {row['districte_name']}"
    f" · HVI: <b>{row['hvi']:.3f}</b>"
    f" · Rànquing: #{int(row['priority_rank'])} de {len(gdf)}</span>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Two-column layout ──────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.subheader("Perfil de vulnerabilitat")
    st.plotly_chart(
        radar_chart(row, city_avg, selected_name),
        use_container_width=True,
    )
    st.plotly_chart(subscores_bar(row), use_container_width=True)

with col_right:
    st.subheader("Dades contextuals")
    c1, c2 = st.columns(2)
    c1.metric("Habitants", f"{int(row['pop_total']):,}".replace(",", "."))
    c2.metric("Majors 65+", f"{int(row['pop_65plus']):,} ({row['pct_elderly']*100:.1f}%)".replace(",", "."))
    c1.metric("Zona verda / hab", f"{row['green_m2_per_resident']:.1f} m²")
    c2.metric("LST estiu", f"{row['lst_mean_summer']:.1f} °C")
    c1.metric("Centres de salut", f"{int(row['health_centre_count'])}")
    c2.metric("Cluster", row.get("cluster_name", "—"))

    st.divider()
    st.subheader("Mapa del barri")
    zoom_map = neighbourhood_zoom_map(row)
    st_folium(zoom_map, width="100%", height=280, returned_objects=[])

# ── Green gap analysis ─────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Anàlisi del dèficit de zona verda")

gap_m2 = green_gap_m2(row["green_m2_per_resident"], int(row["pop_total"]))
cooling = estimate_cooling_benefit(gap_m2)
football_pitches = gap_m2 / 7_140  # standard football pitch ≈ 7,140 m²

col_g1, col_g2, col_g3 = st.columns(3)
col_g1.metric(
    "Dèficit total de zona verda",
    f"{gap_m2:,.0f} m²".replace(",", "."),
    f"≈ {football_pitches:.0f} camps de futbol",
    delta_color="off",
)
col_g2.metric(
    "Reducció estimada de LST",
    f"−{cooling:.2f} °C",
    "si es tanca el dèficit (Bowler et al. 2010)",
    delta_color="off",
)
col_g3.metric(
    "Zona verda actual",
    f"{row['green_m2_per_resident']:.1f} m²/hab",
    f"OMS recomana {WHO_GREEN_M2:.0f} m²/hab",
    delta_color="inverse",
)

# ── Similar barrios (same cluster) ────────────────────────────────────────
if "cluster" in row and row["cluster"] >= 0:
    st.divider()
    same_cluster = gdf[
        (gdf["cluster"] == row["cluster"]) & (gdf["barri_name"] != selected_name)
    ].nsmallest(5, "priority_rank")
    if not same_cluster.empty:
        st.subheader(f"Barris similars — Tipologia «{row.get('cluster_name', '')}»")
        st.dataframe(
            same_cluster[["barri_name", "districte_name", "hvi", "priority_rank"]]
            .rename(columns={
                "barri_name": "Barri", "districte_name": "Districte",
                "hvi": "HVI", "priority_rank": "Rànquing",
            }),
            hide_index=True,
            use_container_width=True,
        )
