"""Thematique 2 : telecharge la pluie ERA5 pure (Open-Meteo) sur les 349 points.

Le parametre models=era5 est obligatoire. Sans lui, l'API melange plusieurs modeles et la
serie change de source en 2017 (mesure du 2026-11-06 sur IDN_013).

Une requete coute 57 unites et l'API en accepte 5 000 par heure : le script attend 42 s
entre deux points, soit environ 4 h au total. Il reprend ou il s'est arrete. Si l'API
refuse pour un quota, il attend sa fin, ou s'arrete proprement si elle est trop lointaine.

Sortie : data/raw/t2_climat/era5/<id>.csv

Usage : .venv/Scripts/python.exe scripts/18_collecter_pluie_era5.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/era5"
URL = "https://archive-api.open-meteo.com/v1/archive"
DEBUT, FIN = "2005-01-01", "2026-10-30"
PAUSE = 42
ATTENTE_MAX = 3700
ESSAIS = 5


class QuotaLong(Exception):
    """Le quota ne se libere pas dans un delai raisonnable."""


def telecharger(lat: float, lon: float) -> pd.DataFrame:
    params = {"latitude": lat, "longitude": lon, "start_date": DEBUT, "end_date": FIN,
              "daily": "precipitation_sum", "models": "era5", "timezone": "UTC"}
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(URL, params=params, timeout=(20, 180))
            if r.status_code == 429:
                fin_quota = float(r.headers.get("X-RateLimit-Reset", time.time() + 3600))
                attente = max(fin_quota - time.time(), 0) + 5
                print(f"    quota atteint : {r.text[:120]} | attente {attente:.0f} s", flush=True)
                if attente > ATTENTE_MAX:
                    raise QuotaLong(r.text[:120])
                time.sleep(attente)
                continue
            r.raise_for_status()
            j = r.json()
            df = pd.DataFrame(j["daily"])
            df["time"] = pd.to_datetime(df["time"])
            df = df.rename(columns={"time": "date", "precipitation_sum": "pluie"}).set_index("date")
            df["grille_lat"], df["grille_lon"] = j["latitude"], j["longitude"]
            return df
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente {30 * essai} s", flush=True)
            time.sleep(30 * essai)
    raise RuntimeError("echec apres tous les essais")


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    DEST.mkdir(parents=True, exist_ok=True)
    echecs = []
    for i, p in enumerate(points.itertuples(), 1):
        cible = DEST / f"{p.id}.csv"
        if cible.exists():
            continue
        try:
            telecharger(p.lat, p.lon).to_csv(cible)
            print(f"{i}/{len(points)} {p.id} ok", flush=True)
        except RuntimeError as e:
            echecs.append(p.id)
            print(f"{i}/{len(points)} {p.id} ECHEC : {e}", flush=True)
        except QuotaLong as e:
            print(f"Arret, quota long : {e}. Relancer plus tard, le script reprendra.", flush=True)
            sys.exit(2)
        time.sleep(PAUSE)
    print(f"Termine : {len(list(DEST.glob('*.csv')))} points sur {len(points)}, echecs : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
