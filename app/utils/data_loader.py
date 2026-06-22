"""Cached data loading functions for the Streamlit app."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

_PROCESSED = Path(__file__).parent.parent.parent / "data" / "processed"
_MODELS = Path(__file__).parent.parent.parent / "models"


@st.cache_data(ttl=3600, show_spinner=False)
def load_barris_hvi() -> gpd.GeoDataFrame:
    """Load the main enriched neighbourhood dataset."""
    path = _PROCESSED / "barris_hvi.parquet"
    if not path.exists():
        st.error(
            "Processed data not found. Run `python scripts/02_clean_and_join.py` "
            "and `python scripts/03_train_model.py` first."
        )
        st.stop()
    return gpd.read_parquet(path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_green_zones() -> gpd.GeoDataFrame | None:
    path = _PROCESSED / "green_zones.parquet"
    if not path.exists():
        return None
    return gpd.read_parquet(path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_health_centres() -> gpd.GeoDataFrame | None:
    path = _PROCESSED / "health_centres.parquet"
    if not path.exists():
        return None
    return gpd.read_parquet(path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_metrics() -> dict:
    path = _MODELS / "metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())
