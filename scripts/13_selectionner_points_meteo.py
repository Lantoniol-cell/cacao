"""Choisit les points meteo a partir de MapSPAM 2010, la carte de reference.

1. Dans chaque pays, on garde les mailles de 0,25 degre les plus denses jusqu'a 80 %
   de la production.
2. Si le total depasse le budget, on les regroupe par k-means pondere, pays par pays.
   Le poids d'un point est la part de densite du groupe : il somme a 1 par pays.

Sortie : data/interim/points_meteo_retenus.parquet

Usage : .venv/Scripts/python.exe scripts/13_selectionner_points_meteo.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[1]
ISO = ["CIV", "GHA", "IDN", "ECU", "CMR", "BRA", "NGA", "PER", "DOM"]
MILLESIME = 2010
COUVERTURE = 0.80
BUDGET = 350
MINIMUM_PAR_PAYS = 10
GRAINE = 42
KM_PAR_DEGRE = 111.32
pd.set_option("display.width", 200, "display.max_columns", None)


def selection_80(p: pd.DataFrame) -> pd.DataFrame:
    p = p.sort_values("densite", ascending=False)
    n = int((p["densite"].cumsum() < COUVERTURE).sum()) + 1
    return p.iloc[:n]


def repartir(tailles: pd.Series) -> pd.Series:
    """Repartit le budget selon la racine du nombre de mailles, avec un minimum."""
    part = np.sqrt(tailles) / np.sqrt(tailles).sum()
    alloc = (part * (BUDGET - MINIMUM_PAR_PAYS * len(tailles))).astype(int) + MINIMUM_PAR_PAYS
    reste = BUDGET - alloc.sum()
    for iso in (part * BUDGET % 1).sort_values(ascending=False).index[:reste]:
        alloc[iso] += 1
    return alloc.clip(upper=tailles)


def regrouper(p: pd.DataFrame, k: int) -> tuple[pd.DataFrame, float, float]:
    cos = np.cos(np.radians(p["lat"].mean()))
    xy = np.c_[p["lat"], p["lon"] * cos]
    km = KMeans(n_clusters=k, n_init=10, random_state=GRAINE).fit(xy, sample_weight=p["densite"])
    g = p.assign(groupe=km.labels_)
    centres = g.groupby("groupe").apply(lambda d: pd.Series({
        "lat": np.average(d["lat"], weights=d["densite"]),
        "lon": np.average(d["lon"], weights=d["densite"]),
        "poids": d["densite"].sum(), "mailles": len(d)}), include_groups=False).reset_index(drop=True)
    centres["poids"] /= centres["poids"].sum()
    dist = np.hypot(xy[:, 0] - km.cluster_centers_[km.labels_, 0],
                    xy[:, 1] - km.cluster_centers_[km.labels_, 1]) * KM_PAR_DEGRE
    return centres, float(np.average(dist, weights=p["densite"])), float(dist.max())


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_cacao.parquet")
    points = points[(points["millesime"] == MILLESIME) & points["pays"].isin(ISO)]
    choisis = {iso: selection_80(points[points["pays"] == iso]) for iso in ISO}
    tailles = pd.Series({iso: len(d) for iso, d in choisis.items()})
    print(f"Mailles couvrant 80 % ({MILLESIME}) : {tailles.to_dict()} | total {tailles.sum()}")

    alloc = repartir(tailles) if tailles.sum() > BUDGET else tailles
    lignes, bilan = [], []
    for iso in ISO:
        c, moy, maxi = regrouper(choisis[iso], int(alloc[iso]))
        lignes.append(c.assign(pays=iso))
        bilan.append({"pays": iso, "mailles_80": tailles[iso], "points": len(c),
                      "dist_moy_km": round(moy, 1), "dist_max_km": round(maxi, 1)})
    res = pd.concat(lignes, ignore_index=True)
    res["id"] = res["pays"] + "_" + res.groupby("pays").cumcount().astype(str).str.zfill(3)
    res = res[["id", "pays", "lat", "lon", "poids", "mailles"]].round({"lat": 4, "lon": 4})
    res.to_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")

    print(pd.DataFrame(bilan).to_string(index=False))
    print(f"Total points : {len(res)} | somme des poids par pays : "
          f"{res.groupby('pays')['poids'].sum().round(6).unique().tolist()}")
    natif = (np.round(res["lat"] / 0.5), np.round(res["lon"] / 0.625))
    print("Cellules natives MERRA-2 distinctes (0,5 x 0,625 degre) :",
          len(set(zip(natif[0], natif[1]))))


if __name__ == "__main__":
    main()
