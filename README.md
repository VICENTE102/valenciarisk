# 🔴 ValenciaRisk — Heat Vulnerability Intelligence Platform

> Which neighbourhoods in Valencia are most at risk from urban heat — and what should the city do about it?

ValenciaRisk is an interactive Streamlit application that computes a composite **Heat Vulnerability Index (HVI)** for every neighbourhood (*barri*) in Valencia. It combines heat exposure, green-space deficit, and social vulnerability into a ranked, map-based decision-support tool for city planners, health officials, and community organisations.

---

## Live App

🔗 **[valenciarisk.streamlit.app](https://valenciarisk.streamlit.app)**

📦 **[github.com/VICENTE102/valenciarisk](https://github.com/VICENTE102/valenciarisk)**

---

## Features

| Feature | Details |
|---|---|
| 🗺️ Choropleth map | HVI score per neighbourhood, hover tooltips |
| ⚖️ Adjustable weights | Sliders to change heat / green / social importance |
| 🔍 Neighbourhood explorer | Radar chart, sub-score breakdown, green gap |
| 🔵 K-Means clustering | 4 vulnerability typologies with profiles |
| 🎯 Intervention recommender | Ranked priority list with specific actions |
| 🌡️ Intervention simulator | Estimate HVI change from adding green space |
| 📐 Methodology page | All formulas, statistics, data sources, limitations |
| ⬇️ CSV exports | Download rankings and action plans |

---

## Data Sources

| Dataset | Source | Type |
|---|---|---|
| Neighbourhood boundaries | OpenStreetMap / Valencia Open Data | Real |
| Green zones | [Valencia Open Data](https://valencia.opendatasoft.com) | Real (API) |
| Health centres | Valencia Open Data | Real (API) |
| Land Surface Temperature | NASA MODIS MOD11A2 | **Synthetic** if GEE not used |
| Population by age | INE Padrón Municipal | **Synthetic** (calibrated) |
| Urban Vulnerability Index | INE Atlas Vulnerabilitat 2011 | Proxy computed |

> Synthetic datasets are clearly labelled in the app and generated with realistic parameters calibrated to Valencia's known demographics.

---

## Project Structure

```
valenciarisk/
├── .streamlit/config.toml       # Dark theme
├── app/
│   ├── main.py                  # Entry point + shared sidebar
│   ├── pages/
│   │   ├── 01_overview.py       # City map + KPIs
│   │   ├── 02_explorer.py       # Neighbourhood deep-dive
│   │   ├── 03_clustering.py     # Typology profiles
│   │   ├── 04_recommendations.py# Action plan + simulator
│   │   └── 05_methodology.py    # Transparency page
│   ├── components/
│   │   ├── maps.py              # Folium map builders
│   │   ├── charts.py            # Plotly chart builders
│   │   └── kpi_cards.py         # st.metric cards
│   └── utils/
│       ├── data_loader.py       # Cached parquet loaders
│       └── scoring.py           # HVI computation
├── data/
│   ├── raw/                     # Downloaded files (gitignored)
│   └── processed/               # Committed parquet files
├── models/
│   ├── kmeans_hvi.joblib        # Trained clustering model
│   └── metrics.json             # Validation statistics
├── scripts/
│   ├── 01_download_data.py      # Download / generate raw data
│   ├── 02_clean_and_join.py     # Spatial joins + sub-scores
│   └── 03_train_model.py        # K-Means + OLS + Moran's I
├── requirements.txt             # App dependencies
├── requirements-dev.txt         # Pipeline dependencies (adds osmnx)
└── .env.example                 # Environment template
```

---

## Quickstart — Local Development

### Prerequisites

- Python 3.11+
- Recommended: [conda](https://docs.conda.io) for `geopandas` on Windows

### 1. Clone and set up environment

```bash
git clone https://github.com/VICENTE102/valenciarisk.git
cd valenciarisk

# With conda (recommended on Windows):
conda create -n valenciarisk python=3.11 -y
conda activate valenciarisk
conda install -c conda-forge geopandas -y
pip install -r requirements-dev.txt

# Or with pip only (Linux / Mac / Windows with prebuilt wheels):
pip install -r requirements-dev.txt
```

### 2. Copy environment file

```bash
cp .env.example .env
# Edit .env if needed (DATA_MODE=synthetic skips live API calls)
```

### 3. Run the data pipeline

```bash
python scripts/01_download_data.py
python scripts/02_clean_and_join.py
python scripts/03_train_model.py
```

This generates `data/processed/barris_hvi.parquet` and `models/kmeans_hvi.joblib`.

> **Skip this step** if `data/processed/` already contains committed parquet files — the pipeline has already been run.

### 4. Launch the app

```bash
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser.

---

## Deployment — Streamlit Community Cloud

1. Push the repository to GitHub (make sure `data/processed/` and `models/` are committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repository, branch `main`, and set **Main file path** to `app/main.py`.
4. Click **Deploy**. The app will be live at `https://YOUR_APP.streamlit.app` in ~3 minutes.

No environment variables are required for the default configuration.

---

## Using Real Satellite LST Data (Optional)

To replace synthetic LST with real MODIS data:

1. Create a free [Google Earth Engine](https://earthengine.google.com) account.
2. Run the following GEE script to export mean summer LST per barrio:

```javascript
// GEE Script — paste into code.earthengine.google.com
var barrios = ee.FeatureCollection('users/YOUR_USER/valencia_barrios');
var lst = ee.ImageCollection('MODIS/061/MOD11A2')
  .filterDate('2023-06-01', '2023-08-31')
  .select('LST_Day_1km')
  .mean()
  .multiply(0.02)
  .subtract(273.15); // Convert to Celsius

var result = lst.reduceRegions({
  collection: barrios,
  reducer: ee.Reducer.mean(),
  scale: 1000
});
Export.table.toDrive({collection: result, description: 'lst_per_barri'});
```

3. Download the exported CSV and place it at `data/raw/lst_per_barri.csv`.
4. Set the `data_type` column to `"real"` in that CSV.
5. Re-run `02_clean_and_join.py` and `03_train_model.py`.

---

## Data Science Methodology

| Component | Method | Library |
|---|---|---|
| Sub-score normalisation | Min-Max scaling | pandas / numpy |
| Composite index | Weighted sum (MCDA) | numpy |
| Vulnerability typologies | K-Means (k=4, k-means++) | scikit-learn |
| Heat–green correlation | Pearson's r | scipy |
| Heat regression | OLS (LST ~ green + density) | statsmodels |
| Spatial autocorrelation | Moran's I (Queen contiguity) | esda / libpysal |
| Cooling benefit estimate | Literature coefficient (Bowler 2010) | Python |

---

## Upload to GitHub

```bash
# First time
git init
git add .
git commit -m "Initial commit: ValenciaRisk application"
git branch -M main
git remote add origin https://github.com/VICENTE102/valenciarisk.git
git push -u origin main

# After changes
git add .
git commit -m "Update: describe change here"
git push
```

---

## Suggested README Screenshots

Add these screenshots to the `screenshots/` folder and reference them in the README:

1. `01_overview_map.png` — city choropleth map at full zoom
2. `02_kpi_cards.png` — four KPI cards with high-risk counts
3. `03_explorer_radar.png` — radar chart for a high-risk neighbourhood
4. `04_action_plan.png` — top-5 priority list with actions expanded
5. `05_simulator.png` — intervention simulator before/after bars
6. `06_methodology.png` — statistical validation metrics table

---

## Team

Built with open data by students of the Universitat Politècnica de València (UPV)
as part of the **Eines de Data Management** course (2024–25).

---

## References

- Bowler, D.E. et al. (2010). Urban greening to cool towns and cities. *Landscape and Urban Planning* 97(3), 147–155.
- WHO (2016). *Urban Green Spaces and Health*. Copenhagen.
- INE (2011). *Atlas de Vulnerabilidad Urbana de España*.
- NASA/USGS (2023). *MODIS MOD11A2 LST product*.
