"""Collecte l'indice ENSO (NOAA ONI) et les intrants FAOSTAT : pesticides et engrais.

ENSO : indice ONI, moyenne glissante de trois mois, donc publie avec retard.
Intrants : series annuelles par pays pour les 9 pays. Ce sont des usages nationaux toutes
cultures confondues, pas des mesures sur le cacao ni une mesure de pollution des sols.

Sorties :
- data/raw/t2_climat/oni.txt
- data/raw/t3_offre/faostat_pesticides.csv, data/raw/t3_offre/faostat_engrais.csv

Usage : .venv/Scripts/python.exe scripts/24_collecter_enso_intrants.py
"""
import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
BULK = "https://bulks-faostat.fao.org/production/{}_E_All_Data_(Normalized).zip"
JEUX = {"faostat_pesticides.csv": "Inputs_Pesticides_Use", "faostat_engrais.csv": "Inputs_FertilizersNutrient"}
ESSAIS = 5
PAYS = ["Côte d'Ivoire", "Ghana", "Indonesia", "Ecuador", "Cameroon", "Brazil", "Nigeria", "Peru", "Dominican Republic"]


def obtenir(url: str) -> requests.Response:
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(url, timeout=(20, 300))
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"    essai {essai} echoue : {str(e)[:90]} | attente {10 * essai} s", flush=True)
            time.sleep(10 * essai)
    raise RuntimeError(f"echec apres tous les essais : {url}")


def main() -> None:
    r = obtenir(ONI)
    (ROOT / "data/raw/t2_climat/oni.txt").write_text(r.text, encoding="utf-8")
    print("ONI :", len(r.text.splitlines()) - 1, "lignes, dernieres :", r.text.splitlines()[-2:])

    for sortie, nom in JEUX.items():
        if (ROOT / "data/raw/t3_offre" / sortie).exists():
            continue
        r = obtenir(BULK.format(nom))
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            fichier = next(n for n in z.namelist() if n.endswith("All_Data_(Normalized).csv"))
            d = pd.read_csv(z.open(fichier), encoding="utf-8")
        d = d[d["Area"].isin(PAYS)]
        d.to_csv(ROOT / "data/raw/t3_offre" / sortie, index=False)
        print(f"{sortie} : {len(d)} lignes, {d['Area'].nunique()} pays, {d['Year'].min()}-{d['Year'].max()}, "
              f"{d['Item'].nunique()} produits, elements : {d['Element'].unique().tolist()[:6]}")


if __name__ == "__main__":
    main()
