"""Live HVI recomputation when the user adjusts weight sliders."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

WHO_GREEN_STANDARD_M2 = 9.0


def recompute_hvi(
    gdf: gpd.GeoDataFrame,
    w_heat: float,
    w_green: float,
    w_social: float,
) -> gpd.GeoDataFrame:
    """
    Recompute the HVI score using new weights (must sum to 1.0).
    Returns a copy of the GeoDataFrame with updated hvi, hvi_percentile,
    and priority_rank columns.
    """
    out = gdf.copy()
    out["hvi"] = (
        w_heat  * out["heat_score"]
        + w_green * out["green_deficit_score"]
        + w_social * out["social_score"]
    ).round(4)
    out["hvi_percentile"] = out["hvi"].rank(pct=True).round(4) * 100
    out["priority_rank"] = out["hvi"].rank(ascending=False, method="min").astype(int)
    return out


def estimate_cooling_benefit(green_m2_added: float) -> float:
    """
    Estimate LST reduction from adding green space.
    Based on Bowler et al. (2010): ~0.94°C per ha of urban greenery (centre vs edge).
    Simplified: 0.1°C per 1,000 m² of green space added.
    """
    return (green_m2_added / 1_000) * 0.1


def _minmax_value(val: float, series_min: float, series_max: float) -> float:
    """Normalise a single value against a known min/max range."""
    if series_max == series_min:
        return 0.5
    return float(max(0.0, min(1.0, (val - series_min) / (series_max - series_min))))


def green_gap_m2(green_m2_per_resident: float, pop_total: int) -> float:
    """Total m² of green space needed to meet WHO 9 m²/resident standard."""
    gap_per_resident = max(0.0, WHO_GREEN_STANDARD_M2 - green_m2_per_resident)
    return gap_per_resident * pop_total
