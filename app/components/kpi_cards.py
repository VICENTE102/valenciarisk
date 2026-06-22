"""KPI card row rendered with st.metric."""

from __future__ import annotations

import geopandas as gpd
import streamlit as st

HIGH_RISK_THRESHOLD = 0.65
WHO_GREEN_M2 = 9.0


def render_kpi_row(gdf: gpd.GeoDataFrame) -> None:
    """Render four KPI cards summarising city-level vulnerability."""
    high_risk = gdf[gdf["hvi"] > HIGH_RISK_THRESHOLD]
    n_high          = len(high_risk)
    pop_high        = int(high_risk["pop_total"].sum())
    elderly_exposed = int(high_risk["pop_65plus"].sum())
    avg_green_gap   = float(
        (WHO_GREEN_M2 - gdf["green_m2_per_resident"].clip(upper=WHO_GREEN_M2)).mean()
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        label="Barris en risc alt (HVI > 0.65)",
        value=f"{n_high}",
        delta=f"de {len(gdf)} barris",
        delta_color="off",
    )
    col2.metric(
        label="Població en risc alt",
        value=f"{pop_high:,}".replace(",", "."),
        delta="habitants",
        delta_color="off",
    )
    col3.metric(
        label="Persones majors exposades (65+)",
        value=f"{elderly_exposed:,}".replace(",", "."),
        delta="en barris de risc alt",
        delta_color="off",
    )
    col4.metric(
        label="Dèficit verd mitja",
        value=f"{avg_green_gap:.1f} m²/hab",
        delta=f"OMS recomana {WHO_GREEN_M2:.0f} m²/hab",
        delta_color="off",
    )
