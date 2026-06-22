"""Page 4 — City Action Plan: intervention priorities and simulator."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import streamlit as st
from streamlit_folium import st_folium

from components.charts import priority_bar, simulator_delta_chart
from components.maps import priority_map
from utils.data_loader import load_barris_hvi, load_health_centres
from utils.scoring import (
    estimate_cooling_benefit, green_gap_m2, recompute_hvi,
)

HIGH_RISK = 0.65

gdf_raw = load_barris_hvi()
w_heat   = st.session_state.get("w_heat",   40) / 100
w_green  = st.session_state.get("w_green",  30) / 100
w_social = st.session_state.get("w_social", 30) / 100
gdf = recompute_hvi(gdf_raw, w_heat, w_green, w_social)
health_centres = load_health_centres()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🎯 Pla d'Acció Municipal")
st.markdown(
    "Basant-se en l'HVI calculat amb els pesos actuals, "
    "aquesta pàgina presenta les intervencions prioritàries per reduir la "
    "vulnerabilitat a la calor a València."
)

# ── Alert banner ───────────────────────────────────────────────────────────
high_risk = gdf[gdf["hvi"] > HIGH_RISK]
n_hr      = len(high_risk)
pop_hr    = int(high_risk["pop_total"].sum())
eld_hr    = int(high_risk["pop_65plus"].sum())

st.markdown(
    f"<div style='background:#E6394622;border:1px solid #E63946;"
    f"border-radius:8px;padding:14px 18px;margin-bottom:20px'>"
    f"⚠️ Amb els pesos actuals, <b>{n_hr} barris</b> estan en risc CRÍTIC (HVI > {HIGH_RISK}). "
    f"Afecten <b>{pop_hr:,} habitants</b>, dels quals "
    f"<b>{eld_hr:,} són majors de 65 anys</b>."
    f"</div>".replace(",", "."),
    unsafe_allow_html=True,
)

# ── Priority map ───────────────────────────────────────────────────────────
st.subheader("Mapa de prioritats")
top_n_map = st.slider("Nombre de barris destacats al mapa", 5, 20, 10, key="top_n_map")
p_map = priority_map(gdf, top_n=top_n_map, health_centres=health_centres)
st_folium(p_map, width="100%", height=450, returned_objects=[])

st.divider()

# ── Priority list with recommended actions ─────────────────────────────────
st.subheader("Intervencions recomanades per prioritat")
top_actions = gdf.nsmallest(10, "priority_rank")

for _, row in top_actions.iterrows():
    rank = int(row["priority_rank"])
    hvi  = row["hvi"]
    gap  = green_gap_m2(row["green_m2_per_resident"], int(row["pop_total"]))
    cool = estimate_cooling_benefit(gap)
    fp   = gap / 7_140

    colour = "#E63946" if hvi > HIGH_RISK else "#FFD166"
    with st.expander(
        f"#{rank} — {row['barri_name']} ({row['districte_name']})  |  "
        f"HVI: {hvi:.3f}",
        expanded=(rank <= 3),
    ):
        c1, c2, c3 = st.columns(3)
        c1.metric("Habitants", f"{int(row['pop_total']):,}".replace(",", "."))
        c2.metric("Majors 65+", f"{int(row['pop_65plus']):,}".replace(",", "."))
        c3.metric("LST estiu", f"{row['lst_mean_summer']:.1f}°C")

        st.markdown("**Accions recomanades:**")
        actions = []
        if row["green_deficit_score"] > 0.60:
            actions.append(
                f"🌳 **Zona verda**: Plantar {gap:,.0f} m² addicionals "
                f"(≈ {fp:.0f} camps de futbol). Reducció estimada de LST: −{cool:.2f}°C."
                .replace(",", ".")
            )
        if row["heat_score"] > 0.65:
            actions.append(
                "🏥 **Centres de refrescament**: Obrir o ampliar centres de refrescament "
                f"durant onades de calor. Barri actual: {int(row['health_centre_count'])} centre(s)."
            )
        if row["social_score"] > 0.60:
            actions.append(
                "📞 **Alerta salut**: Activar protocols d'alerta per als "
                f"{int(row['pop_65plus']):,} majors d'edat.".replace(",", ".")
            )
        if row["pct_elderly"] > 0.20:
            actions.append(
                "🤝 **Serveis socials**: Reforçar visites domiciliàries a la tercera edat "
                f"({row['pct_elderly']*100:.1f}% de la població)."
            )
        if not actions:
            actions.append("ℹ️ Monitoratge continu recomanat.")

        for a in actions:
            st.markdown(f"- {a}")

st.divider()

# ── Intervention Simulator ─────────────────────────────────────────────────
st.subheader("🔬 Simulador d'intervencions")
st.markdown(
    "Estima l'impacte d'afegir zona verda a un barri prioritari. "
    "El càlcul usa el coeficient de refrescament de Bowler et al. (2010): "
    "−0.1°C per cada 1.000 m² de verd urbà afegit."
)

col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    sim_barri = st.selectbox(
        "Barri de la simulació",
        options=gdf.nsmallest(15, "priority_rank")["barri_name"].tolist(),
        key="sim_barri",
    )
with col_sim2:
    added_green = st.slider(
        "Zona verda afegida (m²)", 1_000, 100_000, 10_000, 1_000,
        key="added_green",
    )

sim_row = gdf[gdf["barri_name"] == sim_barri].iloc[0]
before_hvi = float(sim_row["hvi"])

# Estimate new green_m2_per_resident and recompute green_deficit_score
new_green_per_res = sim_row["green_m2_per_resident"] + (added_green / max(int(sim_row["pop_total"]), 1))

# Compute new green deficit score relative to city range
gdf_sim = gdf.copy()
sim_idx = gdf_sim[gdf_sim["barri_name"] == sim_barri].index[0]
gdf_sim.at[sim_idx, "green_m2_per_resident"] = new_green_per_res
new_deficit = max(0.0, 9.0 - new_green_per_res)
city_max_def = (9.0 - gdf["green_m2_per_resident"].clip(upper=9.0)).max()
city_min_def = 0.0
new_gd_score = (new_deficit - city_min_def) / max(city_max_def - city_min_def, 1e-9)
gdf_sim.at[sim_idx, "green_deficit_score"] = float(np.clip(new_gd_score, 0.0, 1.0))

gdf_sim = recompute_hvi(gdf_sim, w_heat, w_green, w_social)
after_hvi = float(gdf_sim.loc[sim_idx, "hvi"])
delta_lst  = estimate_cooling_benefit(added_green)

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("HVI abans", f"{before_hvi:.3f}")
col_r2.metric("HVI després", f"{after_hvi:.3f}", f"{after_hvi - before_hvi:+.3f}")
col_r3.metric("Reducció LST estimada", f"−{delta_lst:.2f}°C")

st.plotly_chart(
    simulator_delta_chart(before_hvi, after_hvi, sim_barri),
    use_container_width=True,
)

if before_hvi > HIGH_RISK and after_hvi <= HIGH_RISK:
    st.success(
        f"✅ Amb {added_green:,} m² de zona verda, {sim_barri} "
        f"sortiria de la zona de risc crític.".replace(",", ".")
    )

st.divider()

# ── Download ───────────────────────────────────────────────────────────────
csv_actions = (
    gdf.nsmallest(20, "priority_rank")[
        ["priority_rank", "barri_name", "districte_name", "hvi",
         "pop_total", "pop_65plus", "green_m2_per_resident", "lst_mean_summer"]
    ]
    .rename(columns={
        "priority_rank": "Prioritat", "barri_name": "Barri",
        "districte_name": "Districte", "hvi": "HVI",
        "pop_total": "Habitants", "pop_65plus": "Majors65",
        "green_m2_per_resident": "VerdM2xHab",
        "lst_mean_summer": "LST_C",
    })
    .to_csv(index=False)
    .encode("utf-8")
)
st.download_button(
    "⬇️ Descarregar pla d'acció (CSV)",
    data=csv_actions,
    file_name="valenciarisk_pla_accio.csv",
    mime="text/csv",
)
