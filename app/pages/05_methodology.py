"""Page 5 — Methodology: transparent explanation of all DS methods."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from components.charts import scatter_lst_green
from utils.data_loader import load_barris_hvi, load_metrics
from utils.scoring import recompute_hvi

gdf_raw = load_barris_hvi()
w_heat   = st.session_state.get("w_heat",   40) / 100
w_green  = st.session_state.get("w_green",  30) / 100
w_social = st.session_state.get("w_social", 30) / 100
gdf = recompute_hvi(gdf_raw, w_heat, w_green, w_social)
metrics = load_metrics()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("📐 Metodologia")
st.markdown(
    "Aquesta pàgina explica de manera transparent com es calcula l'HVI, "
    "quines dades s'utilitzen i quines limitacions té el model."
)

# ── Index formula ──────────────────────────────────────────────────────────
st.subheader("1. Fórmula de l'Índex HVI")
st.markdown(
    r"""
$$
\text{HVI} = w_1 \cdot \text{CalorScore} + w_2 \cdot \text{DèficitVerdScore} + w_3 \cdot \text{SocialScore}
$$

**Valors per defecte:** $w_1 = 0.40$, $w_2 = 0.30$, $w_3 = 0.30$

Tots els subíndexs estan normalitzats a **[0, 1]** mitjançant Min-Max scaling:
$$
\text{Score} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}
$$
"""
)

with st.expander("Detall de cada sub-índex"):
    st.markdown(
        """
**Exposició a la calor (CalorScore)**
- Variable base: Temperatura Superficial de la Terra (LST) en °C (estiu 2023)
- Font: MODIS MOD11A2 via Google Earth Engine (o dades sintètiques calibrades)
- Escala: LST més alta → puntuació més alta → més risc

**Dèficit de zona verda (DèficitVerdScore)**
- Variable base: `màx(0, 9 m²/hab − zona_verda_m²_per_habitant)`
- Font: capes de zones verdes de Valencia Open Data
- L'estàndard de 9 m²/hab és la recomanació de l'OMS (WHO, 2016)

**Vulnerabilitat social (SocialScore)**
- Variable base: proxy basat en percentatge de majors d'edat i indicadors socioeconòmics
- Font ideal: INE Atlas de Vulnerabilitat Urbana (2011) — cens de seccions censals
- Nota: en la versió actual s'utilitza un proxy calculat des de les dades disponibles
        """
    )

# ── Clustering ─────────────────────────────────────────────────────────────
st.subheader("2. Classificació de barris (K-Means)")
col_c1, col_c2 = st.columns(2)
with col_c1:
    st.markdown(
        """
- **Algorisme**: K-Means (scikit-learn)
- **Nombre de clusters**: 4 (determinat per mètode del colze + silhouette)
- **Variables d'entrada**: CalorScore, DèficitVerdScore, SocialScore, % majors d'edat
- **Preprocessat**: StandardScaler (mitjana 0, desviació estàndard 1)
- **Inicialització**: k-means++ amb 20 intents (`n_init=20`)
        """
    )
with col_c2:
    if metrics.get("silhouette_score"):
        st.metric(
            "Silhouette Score",
            f"{metrics['silhouette_score']:.3f}",
            "Valor > 0.35 = bona separació de clusters",
        )
    if metrics.get("n_clusters"):
        st.metric("Nombre de clusters", metrics["n_clusters"])

# ── Statistical validation ─────────────────────────────────────────────────
st.subheader("3. Validació estadística")

col_s1, col_s2 = st.columns(2)
with col_s1:
    ols = metrics.get("ols_regression", {})
    st.markdown("**Regressió OLS**: LST ~ zona_verda + densitat_població")
    if ols:
        st.metric("R²", f"{ols.get('r_squared', '—'):.3f}")
        st.metric("Coef. zona verda",
                  f"{ols.get('coef_green_m2_per_resident', '—'):.4f}")
        st.metric("p-valor zona verda",
                  f"{ols.get('pval_green', '—'):.4f}",
                  "< 0.05 = significatiu" if ols.get("pval_green", 1) < 0.05 else "")

with col_s2:
    mi = metrics.get("morans_i", {})
    st.markdown("**Moran's I** (autocorrelació espacial de l'HVI)")
    if mi and mi.get("morans_i") is not None:
        st.metric("Moran's I", f"{mi['morans_i']:.3f}")
        st.metric("p-valor", f"{mi.get('p_value', '—'):.4f}")
        st.caption(mi.get("interpretation", ""))
    else:
        st.caption("No calculat en aquesta sessió.")

    pearson = metrics.get("pearson_correlation", {})
    if pearson:
        st.markdown("**Correlació de Pearson**: LST vs zona_verda")
        st.metric("r", f"{pearson.get('pearson_r', '—'):.3f}")
        st.metric("p-valor", f"{pearson.get('p_value', '—'):.4f}")

# Scatter plot
st.plotly_chart(scatter_lst_green(gdf), use_container_width=True)

# ── Data sources ───────────────────────────────────────────────────────────
st.subheader("4. Fonts de dades")
st.dataframe(
    {
        "Dataset": [
            "Límits de barris",
            "Zones verdes",
            "Centres de salut",
            "Temperatura Superficial (LST)",
            "Vulnerabilitat Urbana (IVU)",
            "Població per edat",
        ],
        "Font": [
            "OpenStreetMap / Valencia Open Data",
            "Valencia Open Data",
            "Valencia Open Data",
            "NASA MODIS MOD11A2 / sintètica",
            "INE Atlas de Vulnerabilitat Urbana",
            "INE Padrón Municipal / sintètica",
        ],
        "Any": ["2024", "2024", "2024", "2023", "2011", "2023"],
        "Format": ["GeoJSON", "GeoJSON", "GeoJSON", "GeoTIFF / CSV", "CSV", "CSV"],
        "Limitació coneguda": [
            "OSM pot no coincidir exactament amb límits oficials",
            "No inclou jardins privats ni arbres de carrer",
            "Pot no incloure tots els recursos temporals de calor",
            "Dades sintètiques si no es fa processament GEE",
            "Dades del 2011 — possible desactualització",
            "Dades sintètiques calibrades si no es descarreguen de l'INE",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

# ── Limitations ────────────────────────────────────────────────────────────
st.subheader("5. Limitacions i consideracions ètiques")

with st.expander("Limitacions metodològiques"):
    st.markdown(
        """
- L'HVI és un **índex compost**, no un model causal. La correlació entre variables no implica causalitat.
- Els **pesos del model** (40/30/30 per defecte) reflecteixen judicis de valor. Canviant-los, el ranking canvia.
- Les **dades de LST sintètiques** estan calibrades per reproduir patrons d'illa de calor urbana reals, però no substitueixen mesures satellite verificades.
- L'**IVU de l'INE** data del cens de 2011. Barris que han experimentat gentrificació o canvis demogràfics importants poden estar mal representats.
- El **benefici estimat de la zona verda** (−0.1°C per 1.000 m²) és una aproximació de la literatura científica per a ciutats mediterrànies; la reducció real depèn del tipus d'espècie plantada, la localització i les condicions microclimàtiques.
        """
    )

with st.expander("Consideracions ètiques i de justícia"):
    st.markdown(
        """
- **Privacitat**: totes les dades estan agregades a nivell de barri (mínim ~2.000 habitants). No es processen dades individuals.
- **Equitat**: una puntuació social alta reflecteix **desavantatge estructural**, no característiques individuals. L'eina està dissenyada per **dirigir recursos cap** a les comunitats més vulnerables, no per estigmatitzar-les.
- **Transparència**: els pesos i les fórmules són visibles i ajustables. L'Ajuntament pot adaptar el model als seus prioritats polítiques documentades.
- **Participació**: es recomana validar el rànquing amb associacions de veïns locals abans de prendre decisions d'inversió.
        """
    )

# ── References ─────────────────────────────────────────────────────────────
st.subheader("6. Referències")
st.markdown(
    """
- Bowler, D.E. et al. (2010). Urban greening to cool towns and cities: A systematic review of the empirical evidence. *Landscape and Urban Planning*, 97(3), 147–155.
- WHO Regional Office for Europe (2016). *Urban Green Spaces and Health: A Review of Evidence*. Copenhagen.
- INE (2011). *Atlas de Vulnerabilidad Urbana de España*. Ministerio de Fomento.
- NASA/USGS (2023). *MOD11A2 — MODIS Land Surface Temperature and Emissivity*. LP DAAC.
- Ajuntament de València. *Valencia Open Data Portal*. https://valencia.opendatasoft.com
- scikit-learn (2024). KMeans documentation.
- PySAL / esda (2024). Moran's I spatial autocorrelation.
    """
)
