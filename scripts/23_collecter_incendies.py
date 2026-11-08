"""Thematique 6 : collecte les feux detectes par satellite (NASA FIRMS, MODIS) dans les zones de cacao.

Archives annuelles par pays, 2005 a l'annee derniere. On ne garde que les detections
tombees dans une maille de 0,25 degre portant du cacao selon MapSPAM 2010. Une detection
est une anomalie de chaleur : elle ne prouve pas qu'une plantation a brule.

Sortie : data/raw/t2_climat/firms/<ISO>_<annee>.csv

Usage : .venv/Scripts/python.exe scripts/23_collecter_incendies.py
"""
import io
import sys
import time
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/firms"
URL = "https://firms.modaps.eosdis.nasa.gov/data/country/modis/{a}/modis_{a}_{n}.csv"
NOMS = {"CIV": ["Cote_d_Ivoire"],
        "GHA": ["Ghana"], "IDN": ["Indonesia"], "ECU": ["Ecuador"], "CMR": ["Cameroon"], "BRA": ["Brazil"],
        "NGA": ["Nigeria"], "PER": ["Peru"], "DOM": ["Dominican_Republic"]}
ANNEES = range(2005, pd.Timestamp.today().year)
COLONNES = ["latitude", "longitude", "acq_date", "satellite", "confidence", "frp", "daynight", "type", "version"]
MAILLE = 0.25
ESSAIS = 4


def cellule(lat, lon) -> pd.Series:
    return (np.floor(lat / MAILLE).astype(int).astype(str) + "_" + np.floor(lon / MAILLE).astype(int).astype(str))


def lire(iso: str, annee: int) -> pd.DataFrame | None:
    for nom in NOMS[iso]:
        url = URL.format(a=annee, n=quote(nom))
        for essai in range(1, ESSAIS + 1):
            try:
                r = requests.get(url, timeout=(20, 300))
                if r.status_code == 404:
                    break
                r.raise_for_status()
                return pd.read_csv(io.StringIO(r.text), usecols=COLONNES)
            except (requests.RequestException, ValueError) as e:
                print(f"    {iso} {annee} essai {essai} echoue : {str(e)[:80]}", flush=True)
                time.sleep(15 * essai)
    return None


def main() -> None:
    cacao = pd.read_parquet(ROOT / "data/interim/points_meteo_cacao.parquet")
    cacao = cacao[cacao["millesime"] == 2010]
    cellules = {iso: set(cellule(d["lat"], d["lon"])) for iso, d in cacao.groupby("pays") if iso in NOMS}
    DEST.mkdir(parents=True, exist_ok=True)
    echecs = []
    for iso in NOMS:
        for annee in ANNEES:
            cible = DEST / f"{iso}_{annee}.csv"
            if cible.exists():
                continue
            d = lire(iso, annee)
            if d is None:
                echecs.append(f"{iso}_{annee}")
                print(f"{iso} {annee} ECHEC", flush=True)
                continue
            garde = d[cellule(d["latitude"], d["longitude"]).isin(cellules[iso])]
            garde.to_csv(cible, index=False)
            print(f"{iso} {annee} : {len(garde)} gardees sur {len(d)}", flush=True)
            time.sleep(1)
    print(f"Termine : {len(list(DEST.glob('*.csv')))} fichiers, {len(echecs)} echecs : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
