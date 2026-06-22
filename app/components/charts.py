"""Plotly chart builders for ValenciaRisk."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

PALETTE = {
    "red":    "#E63946",
    "orange": "#FF6B35",
    "yellow": "#FFD166",
    "green":  "#06D6A0",
    "navy":   "#0F1923",
    "card":   "#1C2B3A",
    "text":   "#F1FAEE",
}

CLUSTER_COLORS = ["#E63946", "#FF6B35", "#FFD166", "#06D6A0"]

_LAYOUT = dict(
    paper_bgcolor=PALETTE["navy"],
    plot_bgcolor=PALETTE["card"],
    font=dict(color=PALETTE["text"], family="sans-serif"),
    margin=dict(t=40, b=40, l=40, r=20),
)


def hvi_histogram(df: pd.DataFrame) -> go.Figure:
    """Distribution of HVI scores across all barrios."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["hvi"],
        nbinsx=20,
        marker_color=[
            PALETTE["red"] if v > 0.65 else
            PALETTE["yellow"] if v > 0.40 else
            PALETTE["green"]
            for v in pd.cut(df["hvi"], bins=20, labels=False,
                            include_lowest=True).astype(float) * (1 / 20)
        ],
        marker_line_color=PALETTE["navy"],
        marker_line_width=1,
        opacity=0.85,
        name="Barrios",
    ))
    # Threshold lines
    for threshold, label, color in [
        (0.40, "Risc mitjà", PALETTE["yellow"]),
        (0.65, "Risc alt",   PALETTE["red"]),
    ]:
        fig.add_vline(
            x=threshold,
            line_dash="dash",
            line_color=color,
            annotation_text=label,
            annotation_position="top right",
            annotation_font_color=color,
        )
    fig.update_layout(
        **_LAYOUT,
        title="Distribució de l'Índex de Vulnerabilitat (HVI)",
        xaxis_title="HVI",
        yaxis_title="Nombre de barris",
        showlegend=False,
    )
    return fig


def radar_chart(
    barri_row: pd.Series,
    city_avg: pd.Series,
    barri_name: str,
) -> go.Figure:
    """Radar chart comparing a barrio's sub-scores to the city average."""
    categories = ["Exposició Calor", "Dèficit Verd", "Vulnerabilitat Social"]
    barri_vals = [
        barri_row["heat_score"],
        barri_row["green_deficit_score"],
        barri_row["social_score"],
    ]
    avg_vals = [
        city_avg["heat_score"],
        city_avg["green_deficit_score"],
        city_avg["social_score"],
    ]
    # Close the polygon
    cats  = categories + [categories[0]]
    bvals = barri_vals + [barri_vals[0]]
    avals = avg_vals   + [avg_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=bvals, theta=cats, fill="toself",
        name=barri_name,
        line_color=PALETTE["red"],
        fillcolor="rgba(230,57,70,0.3)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=avals, theta=cats, fill="toself",
        name="Mitjana ciutat",
        line_color=PALETTE["green"],
        fillcolor="rgba(6,214,160,0.15)",
        line_dash="dot",
    ))
    fig.update_layout(
        **_LAYOUT,
        polar=dict(
            bgcolor=PALETTE["card"],
            radialaxis=dict(visible=True, range=[0, 1],
                            tickfont=dict(color=PALETTE["text"]), gridcolor="#2A3E52"),
            angularaxis=dict(tickfont=dict(color=PALETTE["text"]), gridcolor="#2A3E52"),
        ),
        legend=dict(font=dict(color=PALETTE["text"])),
        title=f"Perfil: {barri_name}",
    )
    return fig


def subscores_bar(row: pd.Series) -> go.Figure:
    """Horizontal bar chart of the three sub-scores for one barrio."""
    labels = ["Exposició Calor", "Dèficit Verd", "Vulnerabilitat Social"]
    values = [row["heat_score"], row["green_deficit_score"], row["social_score"]]
    colors = [PALETTE["red"], PALETTE["orange"], PALETTE["yellow"]]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}" for v in values],
        textposition="outside",
        textfont=dict(color=PALETTE["text"]),
    ))
    fig.add_vline(x=0.5, line_dash="dash", line_color=PALETTE["text"],
                  annotation_text="Mitjana", annotation_font_color=PALETTE["text"])
    fig.update_layout(
        **_LAYOUT,
        xaxis=dict(range=[0, 1.1], title="Puntuació normalitzada [0–1]"),
        yaxis=dict(title=""),
        title="Descomposició de la puntuació",
    )
    return fig


def priority_bar(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Horizontal bar chart of top-N barrios by HVI."""
    top = df.nsmallest(top_n, "priority_rank").sort_values("hvi")
    colors = [
        PALETTE["red"] if v > 0.65 else
        PALETTE["orange"] if v > 0.50 else
        PALETTE["yellow"]
        for v in top["hvi"]
    ]
    fig = go.Figure(go.Bar(
        x=top["hvi"],
        y=top["barri_name"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}" for v in top["hvi"]],
        textposition="outside",
        textfont=dict(color=PALETTE["text"]),
    ))
    fig.update_layout(
        **_LAYOUT,
        height=max(400, top_n * 22),
        xaxis=dict(range=[0, 1.1], title="HVI"),
        yaxis=dict(title=""),
        title=f"Top {top_n} barris més vulnerables",
    )
    return fig


def cluster_profiles_bar(cluster_df: pd.DataFrame) -> go.Figure:
    """Grouped bar comparing sub-score means across clusters."""
    dims = ["heat_score", "green_deficit_score", "social_score"]
    labels = ["Calor", "Dèficit Verd", "Social"]

    fig = go.Figure()
    for c_id, color in enumerate(CLUSTER_COLORS):
        row = cluster_df[cluster_df["cluster"] == c_id]
        if row.empty:
            continue
        name = row["cluster_name"].iloc[0] if "cluster_name" in row.columns else f"Cluster {c_id}"
        fig.add_trace(go.Bar(
            name=name,
            x=labels,
            y=[float(row[d].iloc[0]) for d in dims],
            marker_color=color,
            opacity=0.85,
        ))
    fig.update_layout(
        **_LAYOUT,
        barmode="group",
        title="Perfil mitja per tipologia",
        yaxis=dict(range=[0, 1], title="Puntuació normalitzada"),
        legend=dict(font=dict(color=PALETTE["text"])),
    )
    return fig


def scatter_lst_green(df: pd.DataFrame) -> go.Figure:
    """Scatter plot: LST vs green cover with OLS trend line."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["green_m2_per_resident"],
        y=df["lst_mean_summer"],
        mode="markers",
        marker=dict(
            color=df["hvi"],
            colorscale="RdYlGn_r",
            size=8,
            opacity=0.85,
            colorbar=dict(title="HVI", tickfont=dict(color=PALETTE["text"])),
            line=dict(color=PALETTE["navy"], width=0.5),
        ),
        text=df["barri_name"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Verd: %{x:.1f} m²/hab<br>"
            "LST: %{y:.1f}°C<extra></extra>"
        ),
        name="Barrios",
    ))
    # OLS trend line
    mask = df["green_m2_per_resident"].notna() & df["lst_mean_summer"].notna()
    x_arr = df.loc[mask, "green_m2_per_resident"].values
    y_arr = df.loc[mask, "lst_mean_summer"].values
    if len(x_arr) > 2:
        coef = np.polyfit(x_arr, y_arr, 1)
        x_line = np.linspace(x_arr.min(), x_arr.max(), 100)
        y_line = np.polyval(coef, x_line)
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode="lines",
            line=dict(color=PALETTE["green"], dash="dash", width=2),
            name="Tendència OLS",
        ))
    fig.update_layout(
        **_LAYOUT,
        title="LST vs Zona Verda per resident",
        xaxis=dict(title="Zona verda (m²/habitant)"),
        yaxis=dict(title="Temperatura superficial (°C)"),
        legend=dict(font=dict(color=PALETTE["text"])),
    )
    return fig


def simulator_delta_chart(before_hvi: float, after_hvi: float,
                          barri_name: str) -> go.Figure:
    """Simple before/after bar for the intervention simulator."""
    fig = go.Figure(go.Bar(
        x=["Abans", "Després"],
        y=[before_hvi, after_hvi],
        marker_color=[PALETTE["red"], PALETTE["green"]],
        text=[f"{before_hvi:.3f}", f"{after_hvi:.3f}"],
        textposition="outside",
        textfont=dict(color=PALETTE["text"]),
    ))
    fig.update_layout(
        **_LAYOUT,
        title=f"Impacte estimat — {barri_name}",
        yaxis=dict(range=[0, 1.1], title="HVI"),
    )
    return fig
