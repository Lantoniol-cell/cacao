"""Thematique 2 : construit les indices de pluie retenus par l'utilisatrice.

ERA5 quotidien : cumuls sur 7 et 30 jours, ecart a la normale passee du meme mois, en
ecarts-types. Vide les trois premieres annees, faute de passe.
CHIRPS mensuel : cumuls sur 1, 3 et 6 mois, ecart a la normale fixe 1991-2004, anterieure
a l'echantillon.
Chaque point est traite seul, puis agrege par pays (poids MapSPAM 2010) et au niveau
mondial (parts FAOSTAT de l'annee N-2, deja calculees par scripts/17_indices_meteo.py).

Delais a appliquer a l'integration dans la grille :
- ERA5 : 7 jours, retard observe sur l'API le 2026-11-06 (dernier jour valide 2026-10-30)
- CHIRPS : colonne disponible_le, le 25 du mois suivant, marge au-dessus de la troisieme
  semaine annoncee par le Climate Hazards Center

Sorties :
- data/processed/pluie_era5_pays.parquet
- data/processed/pluie_chirps_pays.parquet

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/27_indices_pluie.py
"""
from pathlib import Path

import pandas as pd

from cacao.meteo import anomalie_passee, anomalie_reference

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
FENETRES_JOURS = [7, 30]
FENETRES_MOIS = [1, 3, 6]
FIN_ERA5 = "2026-10-30"


def agreger(table: pd.DataFrame, poids: pd.Series, prefixe: str, part: pd.DataFrame) -> pd.DataFrame:
    """Moyenne ponderee par pays et monde, en ignorant les valeurs vides d'un point."""
    p = poids[table.columns]
    pays = pd.Index([i[:3] for i in table.columns])
    somme_valeurs = table.mul(p).T.groupby(pays).sum(min_count=1).T
    somme_poids = table.notna().mul(p).T.groupby(pays).sum().T
    nat = somme_valeurs / somme_poids.where(somme_poids > 0)
    w = part[nat.columns].reindex(nat.index.year)
    w.index = nat.index
    nat["MONDE"] = (nat * w).sum(axis=1, min_count=len(nat.columns)) / w.sum(axis=1)
    return nat.add_prefix(prefixe)


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    part = pd.read_csv(ROOT / "outputs/metriques/t2_poids_pays.csv", index_col=0)

    era = pd.concat({i: pd.read_csv(BASE / f"era5/{i}.csv", index_col="date", parse_dates=True)["pluie"]
                     for i in points.index}, axis=1).loc[:FIN_ERA5]
    if era.isna().any().any():
        raise ValueError("Valeurs ERA5 manquantes")
    sorties = []
    for n in FENETRES_JOURS:
        anom = era.rolling(n, min_periods=n).sum().apply(anomalie_passee)
        sorties.append(agreger(anom, points["poids"], f"ERA5_ANOM{n}J_", part))
        print(f"ERA5 {n} jours : fait", flush=True)
    res = pd.concat(sorties, axis=1)
    res.to_parquet(ROOT / "data/processed/pluie_era5_pays.parquet")
    print(f"ERA5 : {res.shape}, {res.index.min().date()} -> {res.index.max().date()}, "
          f"premier jour complet {res.dropna().index.min().date()}")

    chi = pd.concat({i: pd.read_csv(BASE / f"chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"]
                     for i in points.index}, axis=1).dropna(axis=1, how="all").dropna(how="all")
    sorties = []
    for n in FENETRES_MOIS:
        cumul = chi.rolling(n, min_periods=n).sum()
        anom = cumul.apply(lambda s: anomalie_reference(s, "1991", "2004")).loc["2005":]
        sorties.append(agreger(anom, points["poids"], f"CHIRPS_ANOM{n}M_", part))
    res = pd.concat(sorties, axis=1)
    res["disponible_le"] = res.index + pd.offsets.MonthBegin(1) + pd.Timedelta(days=24)
    res.to_parquet(ROOT / "data/processed/pluie_chirps_pays.parquet")
    print(f"CHIRPS : {res.shape}, {res.index.min().date()} -> {res.index.max().date()}, "
          f"{chi.shape[1]} points, vides : {int(res.isna().sum().sum())}")
    print(res.filter(like="MONDE").tail(4).round(2).to_string())


if __name__ == "__main__":
    main()
