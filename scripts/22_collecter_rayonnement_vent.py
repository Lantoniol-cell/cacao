"""Thematique 2 : complete NASA POWER avec le rayonnement solaire et le vent.

Meme methode que scripts/14_collecter_meteo_nasa.py, dans un dossier separe pour ne pas
toucher aux fichiers deja controles. Le code de valeur manquante devient une valeur vide.

Sortie : data/raw/t2_climat/power_complement/<id>.csv

Usage : .venv/Scripts/python.exe scripts/22_collecter_rayonnement_vent.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/power_complement"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
VARIABLES = ["ALLSKY_SFC_SW_DWN", "WS2M"]
DEBUT = "20050101"
PAUSE = 1.0
ESSAIS = 6


def telecharger(lat: float, lon: float, fin: str) -> pd.DataFrame:
    params = {"parameters": ",".join(VARIABLES), "community": "AG", "latitude": lat, "longitude": lon,
              "start": DEBUT, "end": fin, "format": "JSON"}
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(URL, params=params, timeout=(20, 180))
            r.raise_for_status()
            j = r.json()
            df = pd.DataFrame(j["properties"]["parameter"])
            df.index = pd.to_datetime(df.index, format="%Y%m%d")
            df.index.name = "date"
            return df.mask(df == float(j["header"]["fill_value"]))
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente {10 * essai} s", flush=True)
            time.sleep(10 * essai)
    raise RuntimeError("echec apres tous les essais")


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    DEST.mkdir(parents=True, exist_ok=True)
    fin = pd.Timestamp.today().strftime("%Y%m%d")
    echecs = []
    for i, p in enumerate(points.itertuples(), 1):
        cible = DEST / f"{p.id}.csv"
        if cible.exists():
            continue
        try:
            telecharger(p.lat, p.lon, fin).to_csv(cible)
            print(f"{i}/{len(points)} {p.id} ok", flush=True)
        except RuntimeError as e:
            echecs.append(p.id)
            print(f"{i}/{len(points)} {p.id} ECHEC : {e}", flush=True)
        time.sleep(PAUSE)
    print(f"Termine : {len(list(DEST.glob('*.csv')))} points sur {len(points)}, echecs : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
