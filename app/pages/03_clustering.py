"""Page 3 — Vulnerability Typologies: K-Means cluster profiles."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from components.charts import cluster_profiles_bar, scatter_lst_green, radar_chart
from components.maps import cluster_map
from utils.data_loader import load_barris_hvi, load_metrics
from utils.scoring import recompute_hvi

CLUSTER_COLORS = {0: "#E63946", 1: "#FF6B35", 2: "#FFD166", 3: "#06D6A0"}
CLUSTER_DESCRIPTIONS = {
    0: (
        "**Triple Burden** — Alta calor, baix verd, alta vulnerabilitat social. "
        "Aquests barris acumulen tots tres factors de risc simultàniament i requereixen "
        "atenció urgent i coordinada entre salut, urbanisme i serveis socials."
    ),
    1: (
        "**Heat-Exposed** — Alta temperatura, però baixa vulnerabilitat social. "
        "Barris amb infraestructura o ingressos millors que poden adaptar-se, "
        "però l'exposició tèrmica és real i creixent."
    ),
    2: (
        "**Socialment Fràgils** — Baixa exposició tèrmica però alta vulnerabilitat social. "
        "El canvi climàtic pot agreujar la situació si les temperatures pugen. "
        "Prioritat: reforç de la xarxa de suport social."
    ),
    3: (
        "**Resilients** — Baix risc en els tres eixos. "
        "Barris amb bona cobertura verda, baixa densitat i demografia jove. "
        "Poden servir de referència per a polítiques replicables."
    ),
}

gdf_raw = load_barris_hvi()
w_heat   = st.session_state.get("w_heat",   40) / 100
w_green  = st.session_state.get("w_green",  30) / 100
w_social = st.session_state.get("w_social", 30) / 100
gdf = recompute_hvi(gdf_raw, w_heat, w_green, w_social)
metrics = load_metrics()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🔵 Tipologies de Vulnerabilitat")
st.markdown(
    "Els 87 barris de València s'agrupen en **4 perfils** mitjançant *K-Means clustering* "
    "sobre exposició tèrmica, dèficit verd, vulnerabilitat social i percentatge de majors."
)

if metrics.get("silhouette_score"):
    sil = metrics["silhouette_score"]
    n   = metrics.get("n_clusters", 4)
    st.caption(
        f"Model: K-Means (k={n}) · "
        f"Silhouette score: **{sil:.3f}** "
        f"({'Bona' if sil > 0.40 else 'Acceptable'} separació de clusters)"
    )

st.divider()

# ── Map + selector ─────────────────────────────────────────────────────────
col_map, col_info = st.columns([3, 2], gap="medium")

with col_map:
    st.subheader("Distribució geogràfica dels clusters")
    c_map = cluster_map(gdf)
    st_folium(c_map, width="100%", height=430, returned_objects=[])

with col_info:
    st.subheader("Selecciona una tipologia")
    clusters_ready = "cluster" in gdf.columns and not gdf["cluster"].eq(-1).all()
    if not clusters_ready:
        st.warning(
            "Els clusters no s'han calculat encara. "
            "Executa `python scripts/03_train_model.py`."
        )
        sel_cluster = None
        cluster_labels = {}
    else:
        cluster_ids = sorted(gdf["cluster"].dropna().unique().tolist())
        cluster_labels = {
            c: gdf.loc[gdf["cluster"] == c, "cluster_name"].iloc[0]
            if "cluster_name" in gdf.columns else f"Cluster {c}"
            for c in cluster_ids
        }
        sel_cluster = st.radio(
            "Tipologia",
            options=cluster_ids,
            format_func=lambda c: (
                f"{'🔴' if c == 0 else '🟠' if c == 1 else '🟡' if c == 2 else '🟢'} "
                f"{cluster_labels.get(c, f'Cluster {c}')} "
                f"({(gdf['cluster'] == c).sum()} barris)"
            ),
            key="cluster_radio",
        )
        colour = CLUSTER_COLORS.get(sel_cluster, "#888")
        desc   = CLUSTER_DESCRIPTIONS.get(sel_cluster, "")
        st.markdown(
            f"<div style='border-left:4px solid {colour};padding:8px 12px;"
            f"background:{colour}22;border-radius:4px'>{desc}</div>",
            unsafe_allow_html=True,
        )

# ── Profiles comparison ────────────────────────────────────────────────────
st.divider()
st.subheader("Comparació de perfils")
col_bar, col_scatter = st.columns(2)

with col_bar:
    if "cluster_name" in gdf.columns and not gdf["cluster"].eq(-1).all():
        cluster_df = (
            gdf.groupby(["cluster", "cluster_name"])[
                ["heat_score", "green_deficit_score", "social_score", "hvi"]
            ]
            .mean()
            .reset_index()
        )
        st.plotly_chart(cluster_profiles_bar(cluster_df), use_container_width=True)
    else:
        st.info("Executa el model per veure els perfils de clusters.")

with col_scatter:
    st.plotly_chart(scatter_lst_green(gdf), use_container_width=True)

# ── Barrio table for selected cluster ─────────────────────────────────────
if sel_cluster is not None and "cluster" in gdf.columns:
    st.divider()
    c_name = cluster_labels.get(sel_cluster, f"Cluster {sel_cluster}")
    st.subheader(f"Barris — tipologia «{c_name}»")
    subset = gdf[gdf["cluster"] == sel_cluster][
        ["barri_name", "districte_name", "hvi", "heat_score",
         "green_deficit_score", "social_score", "pop_total", "priority_rank"]
    ].sort_values("priority_rank").rename(columns={
        "barri_name": "Barri", "districte_name": "Districte",
        "hvi": "HVI", "heat_score": "Calor",
        "green_deficit_score": "Dèficit verd", "social_score": "Social",
        "pop_total": "Habitants", "priority_rank": "Rànquing",
    })
    st.dataframe(
        subset.style.background_gradient(subset=["HVI"], cmap="RdYlGn_r"),
        use_container_width=True,
        hide_index=True,
    )
