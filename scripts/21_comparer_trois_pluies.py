"""Thematique 2 : compare NASA POWER, ERA5 et CHIRPS sur la pluie mensuelle par pays.

Les trois series sont cumulees par mois au meme point, puis moyennees par pays avec les
poids MapSPAM 2010, sur les seuls points presents dans les trois sources.
Si le ratio NASA/CHIRPS casse et pas ERA5/CHIRPS, la rupture vient de NASA, et inversement.

Sortie : outputs/metriques/t2_trois_pluies.csv

Usage : .venv/Scripts/python.exe scripts/21_comparer_trois_pluies.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
PERIODES = {"2005-2016": ("2005", "2016"), "2017-2019": ("2017", "2019"),
            "2020-2023": ("2020", "2023"), "2024-2026": ("2024", "2026")}
pd.set_option("display.width", 200, "display.max_columns", None)


def national(table: pd.DataFrame, poids: pd.Series) -> pd.DataFrame:
    poids = poids[table.columns]
    pays = pd.Index([i[:3] for i in table.columns])
    somme = poids.groupby(pays).transform("sum")
    return table.mul(poids / somme).T.groupby(pays).sum(min_count=1).T


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    ids = sorted(set(p.stem for p in (BASE / "era5").glob("*.csv")) & set(p.stem for p in (BASE / "chirps").glob("*.csv")))
    nasa = pd.concat({i: pd.read_csv(BASE / f"power/{i}.csv", index_col="date", parse_dates=True)["PRECTOTCORR"]
                      for i in ids}, axis=1).loc[:"2026-10-30"].resample("MS").sum(min_count=28)
    era = pd.concat({i: pd.read_csv(BASE / f"era5/{i}.csv", index_col="date", parse_dates=True)["pluie"]
                     for i in ids}, axis=1).resample("MS").sum(min_count=28)
    chi = pd.concat({i: pd.read_csv(BASE / f"chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"]
                     for i in ids}, axis=1)
    vides = chi.columns[chi.isna().all()]
    if len(vides):
        print("Points sans donnee CHIRPS, retires (pixels hors terre probables) :", list(vides))
    chi, nasa, era = chi.drop(columns=vides), nasa.drop(columns=vides), era.drop(columns=vides)
    communs = nasa.index.intersection(era.index).intersection(chi.index[chi.notna().all(axis=1)])
    print(f"{chi.shape[1]} points, {len(communs)} mois communs, {communs.min().date()} -> {communs.max().date()}")
    n, e, c = (national(t.loc[communs], points["poids"]) for t in (nasa, era, chi))

    lignes = []
    for nom, (d, f) in PERIODES.items():
        for iso in n:
            a, b, k = n.loc[d:f, iso], e.loc[d:f, iso], c.loc[d:f, iso]
            lignes.append({"pays": iso, "periode": nom, "nasa_chirps": a.sum() / k.sum(),
                           "era5_chirps": b.sum() / k.sum(), "corr_nasa": a.corr(k), "corr_era5": b.corr(k)})
    res = pd.DataFrame(lignes)
    res.round(3).to_csv(ROOT / "outputs/metriques/t2_trois_pluies.csv", index=False)
    for v in ("nasa_chirps", "era5_chirps", "corr_nasa", "corr_era5"):
        print(f"\n{v} :")
        print(res.pivot(index="pays", columns="periode", values=v)[list(PERIODES)].round(2).to_string())


if __name__ == "__main__":
    main()
