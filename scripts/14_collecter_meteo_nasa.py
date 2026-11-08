"""Thematique 2 : telecharge la meteo quotidienne NASA POWER pour chaque point.

Chaque point est enregistre tel que recu dans data/raw/t2_climat/power/<id>.csv.
Le script reprend ou il s'est arrete, attend entre deux requetes et note les echecs
sans jamais remplacer une valeur. Le code -999 de la NASA devient une valeur vide.

Usage : .venv/Scripts/python.exe scripts/14_collecter_meteo_nasa.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/power"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
VARIABLES = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "GWETROOT", "GWETTOP"]
DEBUT = "20050101"
PAUSE = 1.0
ESSAIS = 5


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
            attente = 10 * essai
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente {attente} s", flush=True)
            time.sleep(attente)
    raise RuntimeError("echec apres tous les essais")


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    DEST.mkdir(parents=True, exist_ok=True)
    fin = pd.Timestamp.today().strftime("%Y%m%d")
    echecs = []
    debut = time.time()
    for i, p in enumerate(points.itertuples(), 1):
        cible = DEST / f"{p.id}.csv"
        if cible.exists():
            continue
        try:
            telecharger(p.lat, p.lon, fin).to_csv(cible)
            print(f"{i}/{len(points)} {p.id} ok ({(time.time() - debut) / 60:.1f} min)", flush=True)
        except RuntimeError as e:
            echecs.append(p.id)
            print(f"{i}/{len(points)} {p.id} ECHEC : {e}", flush=True)
        time.sleep(PAUSE)
    print(f"\nTermine : {len(list(DEST.glob('*.csv')))} points sur {len(points)}, {len(echecs)} echec(s) : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
