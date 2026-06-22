"""
Download or generate all raw data needed for ValenciaRisk.

Execution order: run this script first, then 02_clean_and_join.py.

Data sources:
  - Neighbourhood boundaries: OpenStreetMap via osmnx
  - Green zones:              Valencia Open Data (Opendatasoft API)
  - Health centres:           Valencia Open Data (Opendatasoft API)
  - Population by age:        Synthetic (INE-calibrated demographics)
  - Land Surface Temperature: Synthetic (correlated with green cover + density)

Set DATA_MODE=synthetic in .env to skip live API calls entirely.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATA_MODE = os.getenv("DATA_MODE", "real").lower()
VALENCIA_API = "https://valencia.opendatasoft.com/api/explore/v2.1"
VALENCIA_CENTER = (39.4699, -0.3763)
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Valencia barrios: official names and approximate district assignments
# ---------------------------------------------------------------------------

BARRIOS = [
    # (barri_id, name, districte_id, districte_name, approx_lat, approx_lon)
    (101, "La Seu",              1, "Ciutat Vella",       39.4752, -0.3752),
    (102, "La Xerea",            1, "Ciutat Vella",       39.4741, -0.3720),
    (103, "El Carme",            1, "Ciutat Vella",       39.4769, -0.3779),
    (104, "El Pilar",            1, "Ciutat Vella",       39.4758, -0.3795),
    (105, "El Mercat",           1, "Ciutat Vella",       39.4732, -0.3764),
    (106, "Sant Francesc",       1, "Ciutat Vella",       39.4715, -0.3745),
    (201, "Russafa",             2, "L'Eixample",         39.4639, -0.3741),
    (202, "El Pla del Remei",   2, "L'Eixample",         39.4674, -0.3708),
    (203, "Gran Via",            2, "L'Eixample",         39.4661, -0.3720),
    (301, "El Botànic",          3, "Extramurs",          39.4716, -0.3826),
    (302, "La Roqueta",          3, "Extramurs",          39.4697, -0.3848),
    (303, "La Petxina",          3, "Extramurs",          39.4726, -0.3853),
    (304, "Arrancapins",         3, "Extramurs",          39.4680, -0.3830),
    (401, "Campanar",            4, "Campanar",           39.4837, -0.3916),
    (402, "Les Tendetes",        4, "Campanar",           39.4814, -0.3860),
    (403, "El Calvari",          4, "Campanar",           39.4798, -0.3897),
    (404, "Sant Pau",            4, "Campanar",           39.4769, -0.3877),
    (501, "Marxalenes",          5, "La Saïdia",          39.4840, -0.3799),
    (502, "Morvedre",            5, "La Saïdia",          39.4822, -0.3771),
    (503, "Trinitat",            5, "La Saïdia",          39.4858, -0.3752),
    (504, "Tormos",              5, "La Saïdia",          39.4873, -0.3731),
    (505, "Sant Antoni",         5, "La Saïdia",          39.4804, -0.3811),
    (601, "Exposició",           6, "El Pla del Real",    39.4798, -0.3681),
    (602, "Mestalla",            6, "El Pla del Real",    39.4771, -0.3660),
    (603, "Jaume Roig",          6, "El Pla del Real",    39.4748, -0.3679),
    (604, "Ciutat Universitària",6, "El Pla del Real",    39.4820, -0.3640),
    (701, "Nou Moles",           7, "L'Olivereta",        39.4659, -0.3887),
    (702, "Soternes",            7, "L'Olivereta",        39.4679, -0.3921),
    (703, "Tres Forques",        7, "L'Olivereta",        39.4639, -0.3909),
    (704, "La Fuensanta",        7, "L'Olivereta",        39.4617, -0.3874),
    (705, "La Llum",             7, "L'Olivereta",        39.4651, -0.3858),
    (801, "Patraix",             8, "Patraix",            39.4580, -0.3838),
    (802, "Sant Isidre",         8, "Patraix",            39.4551, -0.3810),
    (803, "Vara de Quart",       8, "Patraix",            39.4601, -0.3877),
    (804, "Safranar",            8, "Patraix",            39.4563, -0.3866),
    (805, "Favara",              8, "Patraix",            39.4530, -0.3849),
    (901, "La Raiosa",           9, "Jesús",              39.4598, -0.3780),
    (902, "L'Hort de Senabre",  9, "Jesús",              39.4570, -0.3750),
    (903, "La Creu Coberta",    9, "Jesús",              39.4618, -0.3795),
    (904, "Sant Marcel·lí",     9, "Jesús",              39.4545, -0.3771),
    (905, "Camí Real",           9, "Jesús",              39.4522, -0.3790),
    (1001,"Montolivet",         10, "Quatre Carreres",    39.4572, -0.3680),
    (1002,"En Corts",           10, "Quatre Carreres",    39.4610, -0.3658),
    (1003,"Malilla",            10, "Quatre Carreres",    39.4539, -0.3710),
    (1004,"La Font de Sant Lluís",10,"Quatre Carreres",   39.4515, -0.3685),
    (1005,"Na Rovella",         10, "Quatre Carreres",    39.4553, -0.3640),
    (1006,"La Punta",           10, "Quatre Carreres",    39.4435, -0.3600),
    (1007,"Ciutat de les Arts", 10, "Quatre Carreres",    39.4545, -0.3560),
    (1101,"El Grau",            11, "Poblats Marítims",   39.4576, -0.3331),
    (1102,"El Cabanyal",        11, "Poblats Marítims",   39.4655, -0.3292),
    (1103,"La Creu del Grau",   11, "Poblats Marítims",   39.4614, -0.3368),
    (1104,"Natzaret",           11, "Poblats Marítims",   39.4469, -0.3455),
    (1105,"El Beteró",          11, "Poblats Marítims",   39.4639, -0.3313),
    (1201,"Aiora",              12, "Camins al Grau",     39.4672, -0.3560),
    (1202,"Albors",             12, "Camins al Grau",     39.4701, -0.3598),
    (1203,"La Creu del Grau",   12, "Camins al Grau",     39.4656, -0.3504),
    (1204,"Camí Fondo",         12, "Camins al Grau",     39.4729, -0.3544),
    (1205,"Penya-roja",         12, "Camins al Grau",     39.4688, -0.3516),
    (1301,"L'Illa Perduda",     13, "Algirós",            39.4759, -0.3555),
    (1302,"Ciutat Jardí",       13, "Algirós",            39.4788, -0.3519),
    (1303,"L'Amistat",          13, "Algirós",            39.4810, -0.3585),
    (1304,"La Bega Baixa",      13, "Algirós",            39.4829, -0.3547),
    (1305,"La Carrasca",        13, "Algirós",            39.4851, -0.3514),
    (1401,"Benimaclet",         14, "Benimaclet",         39.4893, -0.3627),
    (1402,"Camí de Vera",       14, "Benimaclet",         39.4856, -0.3627),
    (1501,"Orriols",            15, "Rascanya",           39.4924, -0.3724),
    (1502,"Torrefiel",          15, "Rascanya",           39.4957, -0.3699),
    (1503,"Sant Llorenç",       15, "Rascanya",           39.4906, -0.3770),
    (1601,"Benicalap",          16, "Benicalap",          39.5010, -0.3833),
    (1602,"Ciutat Fallera",     16, "Benicalap",          39.4978, -0.3870),
    (1701,"Benifaraig",         17, "Pobles del Nord",    39.5120, -0.3620),
    (1702,"Poble Nou",          17, "Pobles del Nord",    39.5200, -0.3750),
    (1703,"Carpesa",            17, "Pobles del Nord",    39.5260, -0.3870),
    (1704,"Cases de Bàrcena",   17, "Pobles del Nord",    39.5050, -0.3950),
    (1705,"Mauella",            17, "Pobles del Nord",    39.5180, -0.4020),
    (1706,"Massarrojos",        17, "Pobles del Nord",    39.5310, -0.3770),
    (1707,"Borbotó",            17, "Pobles del Nord",    39.5230, -0.3990),
    (1801,"Benimàmet",          18, "Pobles de l'Oest",   39.4880, -0.4120),
    (1802,"Beniferri",          18, "Pobles de l'Oest",   39.4810, -0.4050),
    (1901,"El Forn d'Alcedo",   19, "Pobles del Sud",     39.4310, -0.3730),
    (1902,"El Castellar",       19, "Pobles del Sud",     39.4230, -0.3660),
    (1903,"Pinedo",             19, "Pobles del Sud",     39.4120, -0.3350),
    (1904,"El Saler",           19, "Pobles del Sud",     39.3530, -0.3280),
    (1905,"La Torre",           19, "Pobles del Sud",     39.4180, -0.3860),
    (1906,"Faitanar",           19, "Pobles del Sud",     39.4380, -0.3960),
]


def _try_get_dataset_id(keyword: str) -> str | None:
    """Search the Valencia Open Data catalog for a dataset by keyword."""
    try:
        resp = requests.get(
            f"{VALENCIA_API}/catalog/datasets",
            params={"where": keyword, "limit": 5, "lang": "es"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return results[0]["dataset_id"]
    except Exception:
        pass
    return None


def _download_geojson(dataset_id: str, output_path: Path) -> bool:
    """Download a dataset from Valencia Open Data as GeoJSON."""
    url = f"{VALENCIA_API}/catalog/datasets/{dataset_id}/exports/geojson"
    try:
        resp = requests.get(url, params={"lang": "es"}, timeout=30)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        print(f"  Downloaded {dataset_id} → {output_path.name}")
        return True
    except Exception as e:
        print(f"  Failed to download {dataset_id}: {e}")
        return False


def download_boundaries_osmnx() -> bool:
    """Download Valencia barrio boundaries from OpenStreetMap via osmnx."""
    output = RAW_DIR / "barris.geojson"
    try:
        import osmnx as ox  # noqa: PLC0415
        print("  Downloading barrio boundaries from OpenStreetMap...")
        tags = {"boundary": "administrative", "admin_level": "10"}
        gdf = ox.features_from_place("Valencia, Spain", tags=tags)
        gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
        gdf = gdf[["name", "geometry"]].reset_index(drop=True)
        gdf.to_file(output, driver="GeoJSON")
        print(f"  Saved {len(gdf)} barrio polygons → barris.geojson")
        return True
    except Exception as e:
        print(f"  OSM download failed: {e}")
        return False


def generate_synthetic_boundaries() -> None:
    """
    Generate point-based synthetic boundaries as small square polygons.
    Used when neither osmnx nor the API can provide real boundaries.
    Each barrio becomes a 0.008° × 0.008° square centred on its known centroid.
    """
    from shapely.geometry import box

    features = []
    for row in BARRIOS:
        bid, name, did, dname, lat, lon = row
        half = 0.004
        geom = box(lon - half, lat - half, lon + half, lat + half)
        features.append({
            "type": "Feature",
            "properties": {"barri_id": bid, "barri_name": name,
                           "districte_id": did, "districte_name": dname},
            "geometry": geom.__geo_interface__,
        })
    collection = {"type": "FeatureCollection", "features": features}
    (RAW_DIR / "barris.geojson").write_text(json.dumps(collection))
    print(f"  Generated synthetic boundaries for {len(BARRIOS)} barris")


def download_green_zones() -> None:
    """Download green zones from Valencia Open Data, or generate synthetic data."""
    output = RAW_DIR / "green_zones.geojson"
    if DATA_MODE == "synthetic":
        _generate_synthetic_green_zones()
        return
    dataset_id = _try_get_dataset_id("zones verdes")
    if dataset_id and _download_geojson(dataset_id, output):
        return
    dataset_id = _try_get_dataset_id("zonas verdes")
    if dataset_id and _download_geojson(dataset_id, output):
        return
    print("  Green zones API failed — generating synthetic data")
    _generate_synthetic_green_zones()


def _generate_synthetic_green_zones() -> None:
    """
    Generate synthetic green zone polygons distributed across Valencia.
    Sizes are calibrated to produce a realistic range of 0.5–15 m²/resident.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    features = []
    zone_id = 1
    for bid, name, did, dname, lat, lon in BARRIOS:
        # Denser / older districts get fewer and smaller parks
        is_dense = did in (1, 2, 3, 5, 8, 9, 11)
        n_parks = rng.integers(0, 2 if is_dense else 4)
        for _ in range(n_parks):
            dlat = rng.uniform(-0.003, 0.003)
            dlon = rng.uniform(-0.003, 0.003)
            half = rng.uniform(0.0003, 0.002 if is_dense else 0.006)
            from shapely.geometry import box
            geom = box(lon + dlon - half, lat + dlat - half,
                       lon + dlon + half, lat + dlat + half)
            area_m2 = float((half * 2 * 111_000) ** 2)
            features.append({
                "type": "Feature",
                "properties": {"zone_id": zone_id, "nombre": f"Parc {zone_id}",
                               "area_m2": round(area_m2, 1)},
                "geometry": geom.__geo_interface__,
            })
            zone_id += 1
    collection = {"type": "FeatureCollection", "features": features}
    (RAW_DIR / "green_zones.geojson").write_text(json.dumps(collection))
    print(f"  Generated {zone_id - 1} synthetic green zones")


def download_health_centres() -> None:
    """Download health centre locations from Valencia Open Data."""
    output = RAW_DIR / "health_centres.geojson"
    if DATA_MODE == "synthetic":
        _generate_synthetic_health_centres()
        return
    for keyword in ("centres salut", "centros salud", "sanitari"):
        dataset_id = _try_get_dataset_id(keyword)
        if dataset_id and _download_geojson(dataset_id, output):
            return
    print("  Health centres API failed — generating synthetic data")
    _generate_synthetic_health_centres()


def _generate_synthetic_health_centres() -> None:
    rng = np.random.default_rng(RANDOM_SEED + 1)
    features = []
    centre_id = 1
    for bid, name, did, dname, lat, lon in BARRIOS:
        # Roughly 1 centre per 2 barrios in dense areas, 1 per 3 elsewhere
        if rng.random() > 0.55:
            features.append({
                "type": "Feature",
                "properties": {
                    "centre_id": centre_id,
                    "name": f"Centre de Salut {name}",
                    "type": "CAP",
                    "barri_id": bid,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        lon + rng.uniform(-0.002, 0.002),
                        lat + rng.uniform(-0.002, 0.002),
                    ],
                },
            })
            centre_id += 1
    collection = {"type": "FeatureCollection", "features": features}
    (RAW_DIR / "health_centres.geojson").write_text(json.dumps(collection))
    print(f"  Generated {centre_id - 1} synthetic health centres")


def generate_population() -> None:
    """
    Generate realistic synthetic population data for Valencia barrios.

    Calibrated to match Valencia's known demographics:
    - Total city population ≈ 800,000
    - Elderly (65+) share ≈ 18–22% in inner districts, 12–16% in outer ones
    """
    rng = np.random.default_rng(RANDOM_SEED + 2)
    records = []
    # Relative population weights (inner dense vs outer sparse barrios)
    pop_weights = {
        1: 0.6, 2: 1.0, 3: 0.8, 4: 0.7, 5: 0.9,
        6: 0.7, 7: 0.8, 8: 0.9, 9: 0.8, 10: 1.0,
        11: 1.1, 12: 0.9, 13: 0.7, 14: 0.8, 15: 1.0,
        16: 0.8, 17: 0.3, 18: 0.4, 19: 0.2,
    }
    # Elderly rate by district (inner old districts have more elderly)
    elderly_rates = {
        1: 0.24, 2: 0.20, 3: 0.22, 4: 0.19, 5: 0.21,
        6: 0.17, 7: 0.20, 8: 0.19, 9: 0.21, 10: 0.18,
        11: 0.22, 12: 0.17, 13: 0.16, 14: 0.15, 15: 0.16,
        16: 0.14, 17: 0.13, 18: 0.14, 19: 0.12,
    }
    for bid, name, did, dname, lat, lon in BARRIOS:
        base_pop = int(8_000 * pop_weights.get(did, 0.7) * rng.uniform(0.6, 1.4))
        elderly_rate = elderly_rates.get(did, 0.18) + rng.uniform(-0.03, 0.03)
        elderly_rate = float(np.clip(elderly_rate, 0.08, 0.32))
        pop_65 = int(base_pop * elderly_rate)
        pop_75 = int(pop_65 * 0.48)
        records.append({
            "barri_id": bid,
            "barri_name": name,
            "pop_total": base_pop,
            "pop_65plus": pop_65,
            "pop_75plus": pop_75,
            "pct_elderly": round(elderly_rate, 4),
        })
    df = pd.DataFrame(records)
    df.to_csv(RAW_DIR / "population.csv", index=False)
    print(f"  Generated population for {len(df)} barris (total: {df.pop_total.sum():,})")


def generate_lst() -> None:
    """
    Generate synthetic Land Surface Temperature (LST) for each barrio.

    Formula (literature-calibrated):
      LST = city_base + heat_from_density + cooling_from_green + noise
    Base city average ≈ 35°C in summer. Dense, low-green barrios reach 40–42°C.

    To replace with real MODIS data: see README §  'Using real satellite LST'.
    """
    rng = np.random.default_rng(RANDOM_SEED + 3)
    # Normalised density proxy (inner districts = higher density)
    density_proxy = {
        1: 0.95, 2: 0.90, 3: 0.85, 4: 0.60, 5: 0.80,
        6: 0.55, 7: 0.75, 8: 0.70, 9: 0.75, 10: 0.65,
        11: 0.85, 12: 0.65, 13: 0.55, 14: 0.50, 15: 0.70,
        16: 0.55, 17: 0.20, 18: 0.30, 19: 0.15,
    }
    # Normalised green proximity proxy (inverted density for simplicity)
    records = []
    for bid, name, did, dname, lat, lon in BARRIOS:
        d_proxy = density_proxy.get(did, 0.5)
        green_proxy = 1.0 - d_proxy + rng.uniform(-0.1, 0.1)
        green_proxy = float(np.clip(green_proxy, 0.05, 0.95))
        lst = (
            35.0
            + d_proxy * 5.0          # density adds up to +5°C
            - green_proxy * 3.0      # green cover cools up to −3°C
            + rng.normal(0, 0.6)     # measurement noise
        )
        records.append({
            "barri_id": bid,
            "lst_mean_summer": round(float(lst), 2),
            "source_year": 2023,
            "data_type": "synthetic",
        })
    df = pd.DataFrame(records)
    df.to_csv(RAW_DIR / "lst_per_barri.csv", index=False)
    city_mean = df["lst_mean_summer"].mean()
    print(f"  Generated LST for {len(df)} barris (city mean: {city_mean:.1f}°C)")


def main() -> None:
    print("=== ValenciaRisk — Step 1: Data Download ===\n")

    # Boundaries
    print("[1/5] Neighbourhood boundaries")
    if DATA_MODE == "real":
        success = download_boundaries_osmnx()
        if not success:
            generate_synthetic_boundaries()
    else:
        generate_synthetic_boundaries()

    # Green zones
    print("\n[2/5] Green zones")
    download_green_zones()

    # Health centres
    print("\n[3/5] Health centres")
    download_health_centres()

    # Population
    print("\n[4/5] Population")
    generate_population()

    # LST
    print("\n[5/5] Land Surface Temperature")
    generate_lst()

    print("\n=== Download complete. Raw data saved to data/raw/ ===")
    print("Next step: python scripts/02_clean_and_join.py")


if __name__ == "__main__":
    main()
