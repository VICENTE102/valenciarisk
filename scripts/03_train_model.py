"""
Fit the clustering model and compute statistical validation metrics.

Inputs:  data/processed/barris_hvi.parquet
Outputs: models/kmeans_hvi.joblib
         models/metrics.json
         data/processed/barris_hvi.parquet  (updated with cluster column)

Run after 02_clean_and_join.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import joblib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

N_CLUSTERS = 4
RANDOM_SEED = 42

# Features used for clustering
CLUSTER_FEATURES = ["heat_score", "green_deficit_score", "social_score", "pct_elderly"]


def fit_kmeans(gdf: gpd.GeoDataFrame) -> tuple[KMeans, StandardScaler, float]:
    """Fit K-Means on vulnerability sub-scores."""
    X = gdf[CLUSTER_FEATURES].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_SEED, n_init=20)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)

    print(f"  K-Means fitted | silhouette score: {sil:.3f}")
    return km, scaler, float(sil)


def label_clusters(gdf: gpd.GeoDataFrame, labels: np.ndarray) -> gpd.GeoDataFrame:
    """
    Assign interpretable names to clusters based on their mean profile.
    Cluster names are derived from which sub-score is highest.
    """
    gdf = gdf.copy()
    gdf["cluster"] = labels

    cluster_means = gdf.groupby("cluster")[
        ["heat_score", "green_deficit_score", "social_score", "hvi"]
    ].mean()

    # Sort clusters by mean HVI descending so cluster 0 = most vulnerable
    order = cluster_means["hvi"].sort_values(ascending=False).index.tolist()
    remap = {old: new for new, old in enumerate(order)}
    gdf["cluster"] = gdf["cluster"].map(remap)

    cluster_names = {
        0: "Triple Burden",
        1: "Heat-Exposed",
        2: "Socially Fragile",
        3: "Resilient",
    }
    gdf["cluster_name"] = gdf["cluster"].map(cluster_names)
    return gdf


def run_ols(gdf: gpd.GeoDataFrame) -> dict:
    """OLS regression: LST ~ green_m2_per_resident + pop_density."""
    import statsmodels.api as sm

    subset = gdf.dropna(subset=["lst_mean_summer", "green_m2_per_resident", "pop_density"])
    X = subset[["green_m2_per_resident", "pop_density"]].copy()
    X = sm.add_constant(X)
    y = subset["lst_mean_summer"]

    model = sm.OLS(y, X).fit()
    r2 = float(model.rsquared)
    pval_green = float(model.pvalues["green_m2_per_resident"])
    coef_green = float(model.params["green_m2_per_resident"])

    print(f"  OLS: R²={r2:.3f} | coef(green)={coef_green:.4f} | p={pval_green:.4f}")
    return {
        "r_squared": round(r2, 4),
        "coef_green_m2_per_resident": round(coef_green, 4),
        "pval_green": round(pval_green, 4),
        "n_obs": len(subset),
    }


def run_pearson(gdf: gpd.GeoDataFrame) -> dict:
    """Pearson correlation: LST vs green cover."""
    subset = gdf.dropna(subset=["lst_mean_summer", "green_m2_per_resident"])
    r, p = pearsonr(subset["lst_mean_summer"], subset["green_m2_per_resident"])
    print(f"  Pearson r(LST, green) = {r:.3f}  p = {p:.4f}")
    return {"pearson_r": round(float(r), 4), "p_value": round(float(p), 4)}


def run_morans_i(gdf: gpd.GeoDataFrame) -> dict:
    """Moran's I spatial autocorrelation on HVI."""
    try:
        from esda.moran import Moran
        from libpysal.weights import Queen

        # Queen contiguity (shared edge or vertex)
        w = Queen.from_dataframe(gdf, silence_warnings=True)
        w.transform = "r"  # row-standardise
        mi = Moran(gdf["hvi"], w, permutations=999)
        print(f"  Moran's I = {mi.I:.3f}  p = {mi.p_sim:.4f}")
        return {
            "morans_i": round(float(mi.I), 4),
            "p_value": round(float(mi.p_sim), 4),
            "interpretation": "Significant spatial clustering" if mi.p_sim < 0.05
                              else "No significant spatial clustering",
        }
    except Exception as e:
        print(f"  Moran's I skipped: {e}")
        return {"morans_i": None, "p_value": None, "interpretation": "Not computed"}


def main() -> None:
    print("=== ValenciaRisk — Step 3: Train Model ===\n")

    gdf = gpd.read_parquet(PROCESSED_DIR / "barris_hvi.parquet")
    print(f"  Loaded {len(gdf)} barrios\n")

    # Clustering
    print("[1/4] Fitting K-Means")
    km, scaler, sil = fit_kmeans(gdf)
    labels = km.labels_
    gdf = label_clusters(gdf, labels)

    # Save model and scaler
    joblib.dump({"kmeans": km, "scaler": scaler, "features": CLUSTER_FEATURES},
                MODELS_DIR / "kmeans_hvi.joblib")
    print(f"  Model saved -> models/kmeans_hvi.joblib")

    # Statistical validation
    print("\n[2/4] OLS regression")
    ols_results = run_ols(gdf)

    print("\n[3/4] Pearson correlation")
    pearson_results = run_pearson(gdf)

    print("\n[4/4] Moran's I")
    morans_results = run_morans_i(gdf)

    # Cluster profiles (for the app)
    cluster_profiles = (
        gdf.groupby(["cluster", "cluster_name"])[
            ["heat_score", "green_deficit_score", "social_score", "hvi", "pop_total"]
        ]
        .mean()
        .round(3)
        .reset_index()
        .to_dict(orient="records")
    )

    metrics = {
        "silhouette_score": round(sil, 4),
        "n_clusters": N_CLUSTERS,
        "cluster_features": CLUSTER_FEATURES,
        "ols_regression": ols_results,
        "pearson_correlation": pearson_results,
        "morans_i": morans_results,
        "cluster_profiles": cluster_profiles,
        "n_barrios": len(gdf),
        "n_high_risk": int((gdf["hvi"] > 0.65).sum()),
        "pop_high_risk": int(gdf.loc[gdf["hvi"] > 0.65, "pop_total"].sum()),
    }

    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\n  Metrics saved -> models/metrics.json")

    # Update parquet with cluster labels
    gdf.to_parquet(PROCESSED_DIR / "barris_hvi.parquet", index=False)
    print(f"  Updated barris_hvi.parquet with cluster labels")

    print("\n=== Training complete. Run the app: streamlit run app/main.py ===")


if __name__ == "__main__":
    main()

