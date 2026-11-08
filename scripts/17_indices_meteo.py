"""Thematique 2 : construit les indices meteo quotidiens par pays et l'indice mondial.

Indice pays : moyenne des points NASA POWER, ponderee par la densite MapSPAM 2010.
Indice mondial : moyenne des pays, ponderee par leur part FAOSTAT de l'annee N-2.
Le poids de N-2 evite d'utiliser une production pas encore publiee en N. Ce sont des
chiffres FAOSTAT revises, pas ceux connus a l'epoque.

Les valeurs restent brutes : aucun ecretage ici. Les jours non complets sont retires.

Sorties :
- data/processed/meteo_pays.parquet : colonnes <VARIABLE>_<PAYS> et <VARIABLE>_MONDE
- outputs/metriques/t2_poids_pays.csv : poids mondiaux par annee

Usage : .venv/Scripts/python.exe scripts/17_indices_meteo.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RETARD_POIDS = 2
NOMS = {"CIV": "Côte d'Ivoire", "GHA": "Ghana", "IDN": "Indonesia", "ECU": "Ecuador", "CMR": "Cameroon",
        "BRA": "Brazil", "NGA": "Nigeria", "PER": "Peru", "DOM": "Dominican Republic"}
pd.set_option("display.width", 200, "display.max_columns", None)


def poids_mondiaux(annees: pd.Index) -> pd.DataFrame:
    fao = pd.read_csv(ROOT / "data/raw/t3_offre/faostat_cacao.csv")
    fao = fao[(fao["Element"] == "Production") & fao["Area"].isin(NOMS.values())]
    prod = fao.pivot(index="Year", columns="Area", values="Value").rename(columns={v: k for k, v in NOMS.items()})
    prod = prod[list(NOMS)]
    part = prod.div(prod.sum(axis=1), axis=0)
    part = part.reindex(annees - RETARD_POIDS)
    if part.isna().any().any():
        raise ValueError("Poids FAOSTAT manquants pour une annee demandee")
    part.index = annees
    return part


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    brut = {i: pd.read_csv(ROOT / f"data/raw/t2_climat/power/{i}.csv", index_col="date", parse_dates=True)
            for i in points.index}
    variables = list(next(iter(brut.values())).columns)
    pays = {}
    for v in variables:
        m = pd.concat({i: d[v] for i, d in brut.items()}, axis=1).dropna()
        for iso, poids in points.groupby("pays")["poids"]:
            pays[f"{v}_{iso}"] = m[poids.index].mul(poids).sum(axis=1)
    res = pd.DataFrame(pays).sort_index()

    annees = res.index.year.unique().sort_values()
    part = poids_mondiaux(annees)
    poids_jour = part.reindex(res.index.year)
    for v in variables:
        res[f"{v}_MONDE"] = sum(res[f"{v}_{iso}"].to_numpy() * poids_jour[iso].to_numpy() for iso in NOMS)

    res.to_parquet(ROOT / "data/processed/meteo_pays.parquet")
    part.round(4).to_csv(ROOT / "outputs/metriques/t2_poids_pays.csv")
    print(f"Indices : {res.shape[0]} jours, {res.shape[1]} colonnes, {res.index.min().date()} -> "
          f"{res.index.max().date()}, manquants : {int(res.isna().sum().sum())}")
    print(part.iloc[[0, 5, 10, 15, 19, -1]].round(3).to_string())
    print(res.filter(like="_MONDE").describe().T[["mean", "min", "max"]].round(2).to_string())


if __name__ == "__main__":
    main()
