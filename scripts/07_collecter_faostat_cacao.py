"""Thematique 3 : telecharge FAOSTAT et isole les lignes du cacao en feves.

L'archive complete est conservee telle quelle dans data/raw/t3_offre/.
Sortie : data/raw/t3_offre/faostat_cacao.csv

Usage : .venv/Scripts/python.exe scripts/07_collecter_faostat_cacao.py
"""
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t3_offre"
URL = "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip"
ARCHIVE = DEST / "faostat_production_cultures.zip"
SORTIE = DEST / "faostat_cacao.csv"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        with requests.get(URL, stream=True, timeout=(20, 120)) as r:
            r.raise_for_status()
            with ARCHIVE.open("wb") as f:
                for bloc in r.iter_content(1 << 20):
                    f.write(bloc)
    print(f"Archive : {ARCHIVE.stat().st_size / 1e6:.1f} Mo")

    with zipfile.ZipFile(ARCHIVE) as z:
        print("Contenu :", z.namelist())
        nom = next(n for n in z.namelist() if n.endswith("All_Data_(Normalized).csv"))
        morceaux = []
        with z.open(nom) as f:
            for bloc in pd.read_csv(f, encoding="utf-8", chunksize=500_000, low_memory=False):
                morceaux.append(bloc[bloc["Item"].str.fullmatch(r"Cocoa beans|Cocoa, beans", na=False)])
    cacao = pd.concat(morceaux, ignore_index=True)
    cacao.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"{len(cacao)} lignes cacao, annees {cacao['Year'].min()} a {cacao['Year'].max()}")
    print("Elements :", cacao["Element"].value_counts().to_dict())
    print("Unites :", cacao["Unit"].unique().tolist())
    print("Colonnes :", cacao.columns.tolist())


if __name__ == "__main__":
    main()
