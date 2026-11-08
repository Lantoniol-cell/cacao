"""Thematique 2 : controle de qualite des previsions GEFS avant leur integration.

Trois regimes de donnees, a verifier un par un :
- reprevision GEFSv12 : 2005 a 2019 ;
- ancien GEFS operationnel, format pgrb2a : 2020-01-01 a 2020-09-22 ;
- GEFSv12 operationnel, format pgrb2s : depuis 2020-09-23.

Controles, par pays (moyenne des points ponderee par MapSPAM) et par regime :
1. Pluie du jour 1 face a la pluie ERA5 du meme jour : rapport des moyennes, correlation.
2. Somme mensuelle de la pluie du jour 1 face a CHIRPS : rapport, correlation.
3. Tmax du jour 1 face a T2M_MAX de la NASA : biais moyen en degres, correlation.
4. Pluie moyenne selon le jour d'echeance, pour voir une derive avec l'echeance.

Le jour d'echeance 1 couvre les heures 0 a 24 apres l'emission de 00 UTC, donc le jour
d'emission lui-meme. Pas de correction de biais ici : ce script ne fait que mesurer.

Sorties : outputs/metriques/gefs_controle.csv, outputs/metriques/gefs_echeances.csv

Usage : .venv/Scripts/python.exe scripts/35_controler_gefs.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
REGIMES = {"reprevision": ("2005-01-01", "2019-12-31"), "ancien": ("2020-01-01", "2020-09-22"),
           "nouveau": ("2020-09-23", "2026-12-31")}
pd.set_option("display.width", 220, "display.max_columns", None)


def charger(dossier: str) -> tuple[pd.DatetimeIndex, np.ndarray]:
    d = BASE / dossier
    ordre = (d / "points.txt").read_text(encoding="utf-8").split()
    attendu = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")["id"].tolist()
    if ordre != attendu:
        raise ValueError(f"Ordre des points different dans {dossier}")
    fichiers = sorted(d.glob("*.npy"))
    dates = pd.to_datetime([f.stem for f in fichiers], format="%Y%m%d")
    return dates, np.stack([np.load(f) for f in fichiers])


def par_pays(table: pd.DataFrame, poids: pd.Series) -> pd.DataFrame:
    """Moyenne ponderee par pays, en ignorant un point vide."""
    p = poids[table.columns]
    pays = pd.Index([c[:3] for c in table.columns])
    return table.mul(p).T.groupby(pays).sum(min_count=1).T / table.notna().mul(p).T.groupby(pays).sum().T


def comparer(a: pd.DataFrame, b: pd.DataFrame, nom: str, mode: str) -> list[dict]:
    lignes = []
    for regime, (debut, fin) in REGIMES.items():
        x, y = a.loc[debut:fin], b.loc[debut:fin]
        x, y = x.align(y, join="inner")
        for pays in x.columns:
            s = pd.concat([x[pays], y[pays]], axis=1).dropna()
            if len(s) < 8:  # l'ancien regime ne compte que 8 mois complets
                continue
            ecart = s.iloc[:, 0].mean() / s.iloc[:, 1].mean() if mode == "rapport" else (s.iloc[:, 0] - s.iloc[:, 1]).mean()
            lignes.append({"controle": nom, "regime": regime, "pays": pays, "n": len(s), mode: round(ecart, 3),
                           "correlation": round(s.iloc[:, 0].corr(s.iloc[:, 1]), 3)})
    return lignes


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    ids = points.index
    dp, pluie = charger("gefs")
    dt, tmax = charger("gefs_tmax")
    print(f"Pluie {pluie.shape}, Tmax {tmax.shape}, dates identiques : {dp.equals(dt)}")
    print(f"Vides pluie : {int(np.isnan(pluie).sum())}, Tmax : {int(np.isnan(tmax).sum())}, "
          f"pluie negative : {int((pluie < 0).sum())}, Tmax infinie : {int(np.isinf(tmax).sum())}")
    print(f"Pluie max {np.nanmax(pluie):.0f} mm/j ; Tmax de {np.nanmin(tmax) - 273.15:.1f} a {np.nanmax(tmax) - 273.15:.1f} C")

    g1 = par_pays(pd.DataFrame(pluie[:, 0, :], index=dp, columns=ids), points["poids"])
    t1 = par_pays(pd.DataFrame(tmax[:, 0, :] - 273.15, index=dt, columns=ids), points["poids"])

    era = pd.concat({i: pd.read_csv(BASE / f"era5/{i}.csv", index_col="date", parse_dates=True)["pluie"] for i in ids}, axis=1)
    era = par_pays(era, points["poids"])
    chi = pd.concat({i: pd.read_csv(BASE / f"chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"] for i in ids}, axis=1)
    chi = par_pays(chi.dropna(axis=1, how="all"), points["poids"])
    nasa = pd.concat({i: pd.read_csv(BASE / f"power/{i}.csv", index_col="date", parse_dates=True)["T2M_MAX"] for i in ids}, axis=1)
    nasa = par_pays(nasa.where(nasa > -900), points["poids"])

    # Mois complets seulement pour la somme mensuelle.
    compte = g1.notna().resample("MS").sum()
    g1m = g1.resample("MS").sum(min_count=1).where(compte >= compte.index.days_in_month.to_numpy()[:, None])

    lignes = (comparer(g1, era, "pluie J1 / ERA5 jour", "rapport")
              + comparer(g1m, chi, "pluie J1 mensuelle / CHIRPS", "rapport")
              + comparer(t1, nasa, "Tmax J1 - NASA T2M_MAX", "biais"))
    t = pd.DataFrame(lignes)
    t.to_csv(ROOT / "outputs/metriques/gefs_controle.csv", index=False)
    for nom, x in t.groupby("controle", sort=False):
        col = "rapport" if "rapport" in x and x["rapport"].notna().any() else "biais"
        print(f"\n{nom} ({col}, puis correlation)")
        print(x.pivot(index="pays", columns="regime", values=col).reindex(columns=list(REGIMES)).round(2).to_string())
        print(x.pivot(index="pays", columns="regime", values="correlation").reindex(columns=list(REGIMES)).round(2).to_string())
        print("n :", x.groupby("regime")["n"].max().to_dict())

    ech = []
    for regime, (debut, fin) in REGIMES.items():
        m = (dp >= debut) & (dp <= fin)
        ech.append(pd.Series(np.nanmean(pluie[m], axis=(0, 2)), index=range(1, 11), name=f"pluie_{regime}"))
        ech.append(pd.Series(np.nanmean(tmax[m], axis=(0, 2)) - 273.15, index=range(1, 11), name=f"tmax_{regime}"))
    e = pd.concat(ech, axis=1).rename_axis("jour_echeance")
    e.to_csv(ROOT / "outputs/metriques/gefs_echeances.csv")
    print("\nMoyenne selon le jour d'echeance, tous points :")
    print(e.round(2).to_string())


if __name__ == "__main__":
    main()
