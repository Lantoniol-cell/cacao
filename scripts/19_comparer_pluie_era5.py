"""Thematique 2 : compare la pluie NASA POWER a la pluie ERA5 pure, point par point.

Une rupture visible dans le ratio NASA/ERA5 dit qu'une des deux series a change, pas
laquelle. Il faudrait une troisieme source pour trancher.

Sorties :
- outputs/metriques/t2_pluie_nasa_era5.csv : ratio et correlations par pays et par periode
- outputs/metriques/t2_pluie_extremes_era5.csv : jours NASA > 300 mm et valeur ERA5 du jour

Usage : .venv/Scripts/python.exe scripts/19_comparer_pluie_era5.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIN = "2026-10-30"
SEUIL = 300
PERIODES = {"2005-2016": ("2005", "2016"), "2017-2019": ("2017", "2019"),
            "2020-2023": ("2020", "2023"), "2024-2026": ("2024", FIN)}
pd.set_option("display.width", 200, "display.max_columns", None)


def main() -> None:
    ids = sorted(p.stem for p in (ROOT / "data/raw/t2_climat/era5").glob("*.csv"))
    nasa = pd.concat({i: pd.read_csv(ROOT / f"data/raw/t2_climat/power/{i}.csv", index_col="date",
                                     parse_dates=True)["PRECTOTCORR"] for i in ids}, axis=1).loc[:FIN]
    era = pd.concat({i: pd.read_csv(ROOT / f"data/raw/t2_climat/era5/{i}.csv", index_col="date",
                                    parse_dates=True)["pluie"] for i in ids}, axis=1).loc[:FIN]
    pays = pd.Index([i[:3] for i in ids])
    print(f"{len(ids)} points, pays : {pays.value_counts().to_dict()}, "
          f"manquants ERA5 : {int(era.isna().sum().sum())}")

    nat_n, nat_e = nasa.T.groupby(pays).mean().T, era.T.groupby(pays).mean().T
    lignes = []
    for nom, (d, f) in PERIODES.items():
        n, e = nat_n.loc[d:f], nat_e.loc[d:f]
        mn, me = n.resample("MS").sum(), e.resample("MS").sum()
        for c in n:
            lignes.append({"pays": c, "periode": nom, "ratio": n[c].mean() / e[c].mean(),
                           "corr_jour": n[c].corr(e[c]), "corr_mois": mn[c].corr(me[c]),
                           "max_nasa": nasa.loc[d:f, pays == c].max().max(),
                           "max_era5": era.loc[d:f, pays == c].max().max()})
    res = pd.DataFrame(lignes)
    res.round(3).to_csv(ROOT / "outputs/metriques/t2_pluie_nasa_era5.csv", index=False)
    for v in ("ratio", "corr_mois", "corr_jour", "max_nasa", "max_era5"):
        print(f"\n{v} :")
        print(res.pivot(index="pays", columns="periode", values=v)[list(PERIODES)].round(2).to_string())

    ext = pd.concat([nasa.stack().rename("nasa"), era.stack().rename("era5")], axis=1).dropna()
    ext = ext[ext["nasa"] > SEUIL].sort_values("nasa", ascending=False).round(1)
    ext.to_csv(ROOT / "outputs/metriques/t2_pluie_extremes_era5.csv")
    print(f"\nJours-point NASA > {SEUIL} mm : {len(ext)}, valeur ERA5 mediane {ext['era5'].median()} mm, "
          f"maximum ERA5 ces jours-la {ext['era5'].max()} mm")


if __name__ == "__main__":
    main()
