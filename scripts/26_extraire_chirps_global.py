"""Thematique 2 : extrait les 349 points du fichier mondial CHIRPS v2.0 mensuel.

Lit la grille mois par mois et prend le pixel de 0,05 degre le plus proche de chaque
point. Une lecture point par point du fichier s'est revelee beaucoup trop lente.
Remplace les fichiers partiels de scripts/20_collecter_chirps.py. Le code de valeur
manquante du fichier devient une valeur vide.

Sortie : data/raw/t2_climat/chirps/<id>.csv (colonnes mois, pluie)

Usage : .venv/Scripts/python.exe -u scripts/26_extraire_chirps_global.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/t2_climat/chirps_global/chirps-v2.0.monthly.nc"
DEST = ROOT / "data/raw/t2_climat/chirps"
DEBUT = "1991-01-01"  # 1991-2004 sert de normale, avant le debut de l'echantillon


def proches(grille: np.ndarray, valeurs: np.ndarray) -> np.ndarray:
    return np.abs(grille[:, None] - valeurs[None, :]).argmin(axis=0)


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    t0 = time.time()
    with xr.open_dataset(SOURCE) as ds:
        print(dict(ds.sizes), list(ds.data_vars), flush=True)
        temps = pd.to_datetime(ds["time"].values)
        rang = np.where(temps >= pd.Timestamp(DEBUT))[0]
        iy = proches(ds["latitude"].values, points["lat"].to_numpy())
        ix = proches(ds["longitude"].values, points["lon"].to_numpy())
        lignes = []
        for n, t in enumerate(rang, 1):
            grille = ds["precip"].isel(time=int(t)).values
            lignes.append(grille[iy, ix])
            if n % 20 == 0:
                print(f"{n}/{len(rang)} mois ({(time.time() - t0) / 60:.1f} min)", flush=True)
    table = pd.DataFrame(lignes, index=temps[rang].to_period("M").to_timestamp(), columns=points.index)
    table = table.where(table >= 0)
    table.index.name = "mois"
    print(f"{table.shape[0]} mois, {table.shape[1]} points, {table.index.min().date()} -> {table.index.max().date()}, "
          f"points sans donnee : {int(table.isna().all().sum())}, valeurs vides : {int(table.isna().sum().sum())}")
    for i in table.columns:
        table[[i]].rename(columns={i: "pluie"}).to_csv(DEST / f"{i}.csv")


if __name__ == "__main__":
    main()
