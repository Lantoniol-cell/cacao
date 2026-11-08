"""Thematique 2 : telecharge la pluie mensuelle CHIRPS v2.0 sur les 349 points.

CHIRPS sert de troisieme source pour departager NASA POWER et ERA5. Lecture via l'IRI
Data Library, au pixel de 0,05 degre le plus proche. Le script reprend ou il s'est
arrete et note les echecs.

Sortie : data/raw/t2_climat/chirps/<id>.csv

Usage : .venv/Scripts/python.exe scripts/20_collecter_chirps.py
"""
import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t2_climat/chirps"
URL = ("https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.monthly/.global/.precipitation/"
       "X/{lon}/VALUE/Y/{lat}/VALUE/T/(Jan%202005)/(Dec%202026)/RANGE/"
       "T+exch+table-+text+text+-table+.tsv")
PAUSE = 1.0
ESSAIS = 5


def telecharger(lat: float, lon: float) -> pd.DataFrame:
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(URL.format(lat=lat, lon=lon), timeout=(20, 120))
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), sep="\t", skiprows=[1])
            df.columns = ["mois", "pluie"]
            df["mois"] = pd.to_datetime(df["mois"], format="%b %Y")
            df = df.set_index("mois")
            if df.empty or df["pluie"].isna().all():
                raise ValueError("reponse vide")
            return df
        except (requests.RequestException, ValueError, pd.errors.ParserError) as e:
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente {10 * essai} s", flush=True)
            time.sleep(10 * essai)
    raise RuntimeError("echec apres tous les essais")


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    # Le serveur est lent : on passe de pays en pays, du point le plus lourd au plus leger,
    # pour avoir vite un echantillon utile sur les 9 pays.
    rang = points.groupby("pays")["poids"].rank(method="first", ascending=False)
    points = points.assign(rang=rang).sort_values(["rang", "pays"])
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
        time.sleep(PAUSE)
    print(f"Termine : {len(list(DEST.glob('*.csv')))} points sur {len(points)}, echecs : {echecs}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
