"""Thematique 2 : telecharge un controle Open-Meteo (ERA5) sur quelques points.

Points choisis : le point le plus lourd de chaque pays, plus ceux ou NASA POWER donne
les pluies quotidiennes les plus fortes. ERA5 ne sert qu'a controler NASA POWER : il
n'entre pas dans les donnees du modele.

Une requete sur 2005-2026 coute environ 342 unites et l'API en accepte 600 par minute :
le script attend 40 s entre deux points. Il reprend ou il s'est arrete.

Sortie : data/raw/t2_climat/openmeteo/<id>.csv

Usage : .venv/Scripts/python.exe scripts/15_collecter_controle_openmeteo.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/era5_controle"  # l'ancien dossier openmeteo melange plusieurs modeles
URL = "https://archive-api.open-meteo.com/v1/archive"
VARIABLES = ["precipitation_sum", "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
             "relative_humidity_2m_mean", "soil_moisture_0_to_100cm_mean"]
DEBUT, FIN = "2005-01-01", "2026-10-31"
EXTREMES = ["IDN_013", "CIV_020", "CIV_012", "IDN_028", "CMR_035"]
PAUSE = 40
ESSAIS = 4


def telecharger(lat: float, lon: float) -> pd.DataFrame:
    params = {"latitude": lat, "longitude": lon, "start_date": DEBUT, "end_date": FIN,
              "daily": ",".join(VARIABLES), "models": "era5", "timezone": "UTC"}
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(URL, params=params, timeout=(20, 180))
            r.raise_for_status()
            df = pd.DataFrame(r.json()["daily"])
            df["time"] = pd.to_datetime(df["time"])
            return df.rename(columns={"time": "date"}).set_index("date")
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente 70 s", flush=True)
            time.sleep(70)
    raise RuntimeError("echec apres tous les essais")


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    lourds = points.loc[points.groupby("pays")["poids"].idxmax(), "id"].tolist()
    choix = points[points["id"].isin(lourds + EXTREMES)]
    DEST.mkdir(parents=True, exist_ok=True)
    echecs = []
    for i, p in enumerate(choix.itertuples(), 1):
        cible = DEST / f"{p.id}.csv"
        if cible.exists():
            continue
        try:
            telecharger(p.lat, p.lon).to_csv(cible)
            print(f"{i}/{len(choix)} {p.id} ok", flush=True)
        except RuntimeError as e:
            echecs.append(p.id)
            print(f"{i}/{len(choix)} {p.id} ECHEC : {e}", flush=True)
        time.sleep(PAUSE)
    print(f"Termine : {len(list(DEST.glob('*.csv')))} points sur {len(choix)}, echecs : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
