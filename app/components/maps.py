"""Folium map builders for ValenciaRisk."""

from __future__ import annotations

import folium
import geopandas as gpd
import numpy as np
import pandas as pd

VALENCIA_CENTER = [39.4699, -0.3763]
TILES = "CartoDB dark_matter"

CLUSTER_COLORS = {
    0: "#E63946",  # red   — Triple Burden
    1: "#FF6B35",  # orange — Heat-Exposed
    2: "#FFD166",  # yellow — Socially Fragile
    3: "#06D6A0",  # green  — Resilient
    -1: "#888888", # grey   — unassigned
}

CLUSTER_LABELS = {
    0: "Triple Burden",
    1: "Heat-Exposed",
    2: "Socially Fragile",
    3: "Resilient",
}


def _base_map(zoom: int = 12) -> folium.Map:
    return folium.Map(
        location=VALENCIA_CENTER,
        zoom_start=zoom,
        tiles=TILES,
        prefer_canvas=True,
    )


def choropleth_map(
    gdf: gpd.GeoDataFrame,
    column: str = "hvi",
    title: str = "Heat Vulnerability Index",
) -> folium.Map:
    """
    Choropleth coloured by `column`. Includes hover tooltip.
    Colour scale: RdYlGn reversed (red = high risk).
    """
    m = _base_map()
    gdf_wgs = gdf.to_crs("EPSG:4326") if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

    folium.Choropleth(
        geo_data=gdf_wgs.__geo_interface__,
        data=gdf_wgs[["barri_id", column]],
        columns=["barri_id", column],
        key_on="feature.properties.barri_id",
        fill_color="RdYlGn_r",
        fill_opacity=0.72,
        line_opacity=0.25,
        line_color="#FFFFFF",
        legend_name=title,
        bins=6,
        nan_fill_color="#444444",
    ).add_to(m)

    # Transparent overlay for tooltips (Choropleth has no built-in tooltip)
    tooltip_fields = [
        "barri_name", "districte_name", "hvi",
        "heat_score", "green_deficit_score", "social_score",
        "pop_total", "lst_mean_summer",
    ]
    tooltip_aliases = [
        "Barri", "Districte", "HVI",
        "Calor", "Dèficit verd", "Social",
        "Habitants", "LST (°C)",
    ]
    # Keep only available columns
    available = [f for f in tooltip_fields if f in gdf_wgs.columns]
    aliases   = [a for f, a in zip(tooltip_fields, tooltip_aliases) if f in gdf_wgs.columns]

    def _style(_): return {"fillOpacity": 0, "weight": 0}

    folium.GeoJson(
        gdf_wgs[available + ["geometry"]],
        style_function=_style,
        tooltip=folium.GeoJsonTooltip(
            fields=available,
            aliases=aliases,
            localize=True,
            sticky=True,
            labels=True,
        ),
    ).add_to(m)

    return m


def priority_map(
    gdf: gpd.GeoDataFrame,
    top_n: int = 10,
    health_centres: gpd.GeoDataFrame | None = None,
) -> folium.Map:
    """
    Map highlighting the top-N priority barrios with numbered markers.
    Optional: overlay health centre locations.
    """
    m = _base_map()
    gdf_wgs = gdf.to_crs("EPSG:4326") if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf
    top = gdf_wgs.nsmallest(top_n, "priority_rank")

    # Background: all barrios (light)
    folium.GeoJson(
        gdf_wgs,
        style_function=lambda _: {
            "fillColor": "#1C2B3A", "color": "#FFFFFF",
            "weight": 0.5, "fillOpacity": 0.4,
        },
    ).add_to(m)

    # Highlighted top-N
    for _, row in top.iterrows():
        centroid = row.geometry.centroid
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=(
                    f'<div style="'
                    f'background:#E63946;color:white;border-radius:50%;'
                    f'width:28px;height:28px;text-align:center;'
                    f'line-height:28px;font-weight:bold;font-size:13px;'
                    f'border:2px solid white;">'
                    f'{int(row["priority_rank"])}</div>'
                ),
                icon_size=(28, 28),
                icon_anchor=(14, 14),
            ),
            tooltip=(
                f"#{int(row['priority_rank'])} {row['barri_name']} "
                f"| HVI: {row['hvi']:.3f}"
            ),
        ).add_to(m)

        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda _: {
                "fillColor": "#E63946", "color": "#FF0000",
                "weight": 2, "fillOpacity": 0.45,
            },
        ).add_to(m)

    # Health centres
    if health_centres is not None and len(health_centres) > 0:
        hc_wgs = (health_centres.to_crs("EPSG:4326")
                  if health_centres.crs and health_centres.crs.to_epsg() != 4326
                  else health_centres)
        for _, hc in hc_wgs.iterrows():
            if hc.geometry.geom_type == "Point":
                folium.CircleMarker(
                    location=[hc.geometry.y, hc.geometry.x],
                    radius=4,
                    color="#06D6A0",
                    fill=True,
                    fill_color="#06D6A0",
                    fill_opacity=0.8,
                    tooltip=hc.get("name", "Centre de salut"),
                ).add_to(m)

    return m


def neighbourhood_zoom_map(row: pd.Series) -> folium.Map:
    """Zoomed map of a single barrio with its boundary highlighted."""
    centroid = row.geometry.centroid
    m = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=14,
        tiles=TILES,
    )
    folium.GeoJson(
        row.geometry.__geo_interface__,
        style_function=lambda _: {
            "fillColor": "#E63946", "color": "#FF6B35",
            "weight": 3, "fillOpacity": 0.35,
        },
    ).add_to(m)
    return m


def cluster_map(gdf: gpd.GeoDataFrame) -> folium.Map:
    """Choropleth coloured by cluster label (4 discrete colours)."""
    m = _base_map()
    gdf_wgs = gdf.to_crs("EPSG:4326") if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

    def _style(feature):
        cluster = feature["properties"].get("cluster", -1)
        return {
            "fillColor": CLUSTER_COLORS.get(cluster, "#888888"),
            "color": "#FFFFFF",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    folium.GeoJson(
        gdf_wgs[["barri_name", "cluster", "cluster_name", "hvi", "geometry"]],
        style_function=_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["barri_name", "cluster_name", "hvi"],
            aliases=["Barri", "Tipologia", "HVI"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    return m
