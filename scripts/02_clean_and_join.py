"""
Clean raw data and build the main analysis dataset.

Inputs  (data/raw/):   barris.geojson, green_zones.geojson,
                        health_centres.geojson, population.csv, lst_per_barri.csv
Outputs (data/processed/): barris_hvi.parquet, green_zones.parquet,
                             health_centres.parquet

Run after 01_download_data.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, shape

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Official Valencia barrio list used in 01_download_data.py
def _load_barrios_list() -> list:
    """Load the BARRIOS constant from 01_download_data without side effects."""
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        "_dl_data", Path(__file__).parent / "01_download_data.py"
    )
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BARRIOS


BARRIOS = _load_barrios_list()

# WHO green space standard: 9 m² per resident
WHO_GREEN_STANDARD_M2 = 9.0
CRS_WEB = "EPSG:4326"    # WGS84 for web maps and Folium
CRS_METRIC = "EPSG:25830" # UTM zone 30N for area calculations (metres)


# ---------------------------------------------------------------------------
# Barrios
# ---------------------------------------------------------------------------

def _barri_id_from_name(name: str, lookup: dict[str, int]) -> int | None:
    """Fuzzy match barrio name to barri_id."""
    name_clean = name.lower().strip()
    for k, v in lookup.items():
        if k in name_clean or name_clean in k:
            return v
    return None


def load_barris() -> gpd.GeoDataFrame:
    """
    Load barrio boundaries and standardise columns.
    Handles both OSM downloads (name only) and synthetic boundaries (full attrs).
    """
    path = RAW_DIR / "barris.geojson"
    gdf = gpd.read_file(path)
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    name_to_id = {b[1].lower(): b[0] for b in BARRIOS}
    id_to_meta = {b[0]: b for b in BARRIOS}

    if "barri_id" not in gdf.columns:
        # OSM download: match by name
        name_col = next((c for c in gdf.columns if "name" in c.lower()), None)
        if name_col is None:
            raise ValueError("Cannot find a name column in barris.geojson")
        gdf["barri_id"] = gdf[name_col].apply(
            lambda n: _barri_id_from_name(str(n), name_to_id) if pd.notna(n) else None
        )
        gdf = gdf.dropna(subset=["barri_id"]).copy()
        gdf["barri_id"] = gdf["barri_id"].astype(int)

    # Enrich with district info from lookup table
    for col_idx, col_name in [(1, "barri_name"), (2, "districte_id"),
                               (3, "districte_name")]:
        gdf[col_name] = gdf["barri_id"].map(
            {b[0]: b[col_idx] for b in BARRIOS}
        )

    gdf = gdf[["barri_id", "barri_name", "districte_id", "districte_name",
               "geometry"]].copy()
    gdf = gdf.set_crs(CRS_WEB, allow_override=True)
    print(f"  Loaded {len(gdf)} barrio polygons")
    return gdf


# ---------------------------------------------------------------------------
# Green zones
# ---------------------------------------------------------------------------

def compute_green_per_barri(barris: gpd.GeoDataFrame) -> pd.Series:
    """
    Spatially join green zones to barrios and compute total green area (m²).
    Returns a Series indexed by barri_id.
    """
    path = RAW_DIR / "green_zones.geojson"
    gdf_green = gpd.read_file(path)
    gdf_green = gdf_green[gdf_green.geometry.notna()].copy()
    gdf_green = gdf_green[
        gdf_green.geometry.type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    # Reproject to metric CRS for area computation
    barris_m = barris.to_crs(CRS_METRIC)
    green_m = gdf_green.to_crs(CRS_METRIC)

    # Clip green zones to barrio boundaries, then aggregate area per barrio
    joined = gpd.overlay(green_m, barris_m[["barri_id", "geometry"]],
                         how="intersection")
    joined["green_m2_clip"] = joined.geometry.area
    result = joined.groupby("barri_id")["green_m2_clip"].sum()

    # Save clean green zones (WGS84) for the app
    gdf_green.to_crs(CRS_WEB).to_parquet(PROCESSED_DIR / "green_zones.parquet")

    print(f"  Green zones joined: {len(result)} barrios have green space")
    return result


# ---------------------------------------------------------------------------
# Health centres
# ---------------------------------------------------------------------------

def compute_health_centres_per_barri(barris: gpd.GeoDataFrame) -> pd.DataFrame:
    """Count health centres per barrio via spatial join."""
    path = RAW_DIR / "health_centres.geojson"
    gdf_hc = gpd.read_file(path)
    gdf_hc = gdf_hc[gdf_hc.geometry.notna()].copy()

    # Points only
    gdf_hc = gdf_hc[gdf_hc.geometry.type == "Point"].copy()
    gdf_hc = gdf_hc.set_crs(CRS_WEB, allow_override=True)

    # Drop any pre-existing barri_id so sjoin doesn't produce suffixed duplicates
    hc_geom_only = gdf_hc[["geometry"]].copy()
    joined = gpd.sjoin(hc_geom_only, barris[["barri_id", "geometry"]],
                       how="left", predicate="within")
    counts = joined.groupby("barri_id").size().rename("health_centre_count")

    # Save for the app map
    gdf_hc.to_parquet(PROCESSED_DIR / "health_centres.parquet")

    print(f"  Health centres joined to barrios")
    return counts.reset_index()


# ---------------------------------------------------------------------------
# Sub-score computation
# ---------------------------------------------------------------------------

def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


def build_hvi_dataset(
    barris: gpd.GeoDataFrame,
    green_per_barri: pd.Series,
    health_centres: pd.DataFrame,
    w_heat: float = 0.40,
    w_green: float = 0.30,
    w_social: float = 0.30,
) -> gpd.GeoDataFrame:
    """
    Join all sub-datasets and compute sub-scores and default HVI.
    """
    gdf = barris.copy()

    # Population
    pop = pd.read_csv(RAW_DIR / "population.csv")
    gdf = gdf.merge(pop[["barri_id", "pop_total", "pop_65plus",
                          "pop_75plus", "pct_elderly"]], on="barri_id", how="left")

    # Green area
    gdf["green_m2"] = gdf["barri_id"].map(green_per_barri).fillna(0.0)
    gdf["green_m2_per_resident"] = (
        gdf["green_m2"] / gdf["pop_total"].replace(0, np.nan)
    ).fillna(0.0)

    # Green deficit (how far below WHO standard each barrio is)
    gdf["green_deficit_m2_per_resident"] = (
        WHO_GREEN_STANDARD_M2 - gdf["green_m2_per_resident"]
    ).clip(lower=0.0)

    # Health centres
    gdf = gdf.merge(health_centres, on="barri_id", how="left")
    gdf["health_centre_count"] = gdf["health_centre_count"].fillna(0).astype(int)

    # LST
    lst = pd.read_csv(RAW_DIR / "lst_per_barri.csv")
    gdf = gdf.merge(lst[["barri_id", "lst_mean_summer", "data_type"]],
                    on="barri_id", how="left")
    gdf["lst_mean_summer"] = gdf["lst_mean_summer"].fillna(
        gdf["lst_mean_summer"].mean()
    )
    gdf["data_type"] = gdf["data_type"].fillna("synthetic")

    # INU (INE Urban Vulnerability) — using unemployment proxy from population age
    # Real data: replace pct_elderly-based proxy with INE IVU once downloaded
    rng = np.random.default_rng(42)
    gdf["ivu_proxy"] = (
        gdf["pct_elderly"] * 0.6
        + (1 - gdf["green_m2_per_resident"].clip(upper=15) / 15) * 0.3
        + rng.uniform(0, 0.1, len(gdf))
    ).clip(0, 1)

    # Population density (proxy from area)
    gdf_metric = gdf.to_crs(CRS_METRIC)
    gdf["area_m2"] = gdf_metric.geometry.area
    gdf["pop_density"] = gdf["pop_total"] / (gdf["area_m2"] / 1_000_000)  # per km²

    # ── Sub-scores [0, 1] ───────────────────────────────────────────────────
    gdf["heat_score"]          = _minmax(gdf["lst_mean_summer"])
    gdf["green_deficit_score"] = _minmax(gdf["green_deficit_m2_per_resident"])
    gdf["social_score"]        = _minmax(gdf["ivu_proxy"])

    # ── Composite HVI ───────────────────────────────────────────────────────
    gdf["hvi"] = (
        w_heat  * gdf["heat_score"]
        + w_green * gdf["green_deficit_score"]
        + w_social * gdf["social_score"]
    ).round(4)

    gdf["hvi_percentile"] = gdf["hvi"].rank(pct=True).round(4) * 100
    gdf["priority_rank"]  = gdf["hvi"].rank(ascending=False, method="min").astype(int)

    # Placeholder cluster column (filled by 03_train_model.py)
    gdf["cluster"] = -1

    return gdf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== ValenciaRisk — Step 2: Clean & Join ===\n")

    print("[1/4] Loading barrio boundaries")
    barris = load_barris()

    print("\n[2/4] Computing green space per barrio")
    green_per_barri = compute_green_per_barri(barris)

    print("\n[3/4] Joining health centres")
    health_centres = compute_health_centres_per_barri(barris)

    print("\n[4/4] Building HVI dataset")
    gdf = build_hvi_dataset(barris, green_per_barri, health_centres)

    out_path = PROCESSED_DIR / "barris_hvi.parquet"
    gdf.to_parquet(out_path, index=False)
    print(f"\n  Saved {len(gdf)} barrios -> {out_path}")
    print(f"  HVI range: {gdf['hvi'].min():.3f} - {gdf['hvi'].max():.3f}")
    print(f"  High-risk barrios (HVI > 0.65): {(gdf['hvi'] > 0.65).sum()}")

    print("\n=== Clean complete. Next: python scripts/03_train_model.py ===")


if __name__ == "__main__":
    main()

