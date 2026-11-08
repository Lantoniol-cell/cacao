"""Module d'impact agronomique (protocole.md, point 12) : meteo annuelle par pays.

Pour chaque pays, moyenne des points ponderee par MapSPAM 2010 (poids de
points_meteo_retenus.parquet), en ignorant un point vide :
- pluie : total annuel CHIRPS, 1991 a 2025 (annees completes seulement) ;
- temperature : moyenne annuelle de T2M_MAX NASA POWER, 2005 a 2025.
Puis production FAOSTAT et son code de qualite, par pays et par an.

Sortie : data/processed/impact_panel.parquet (une ligne par pays et par an)

Usage : .venv/Scripts/python.exe scripts/41_meteo_annuelle.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
NOMS_FAO = {"Côte d'Ivoire": "CIV", "Ghana": "GHA", "Indonesia": "IDN", "Ecuador": "ECU", "Cameroon": "CMR",
            "Brazil": "BRA", "Nigeria": "NGA", "Peru": "PER", "Dominican Republic": "DOM"}


def par_pays(table: pd.DataFrame, poids: pd.Series) -> pd.DataFrame:
    p = poids[table.columns]
    pays = pd.Index([c[:3] for c in table.columns])
    return table.mul(p).T.groupby(pays).sum(min_count=1).T / table.notna().mul(p).T.groupby(pays).sum().T


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")

    chi = pd.concat({i: pd.read_csv(BASE / f"chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"]
                     for i in points.index}, axis=1).dropna(axis=1, how="all")
    mois = chi.notna().any(axis=1).groupby(chi.index.year).sum()
    pluie = par_pays(chi, points["poids"]).groupby(chi.index.year).sum(min_count=12)
    pluie = pluie.loc[mois[mois == 12].index]

    nasa = pd.concat({i: pd.read_csv(BASE / f"power/{i}.csv", index_col="date", parse_dates=True)["T2M_MAX"]
                      for i in points.index}, axis=1)
    nasa = par_pays(nasa.where(nasa > -900), points["poids"])
    jours = nasa.notna().all(axis=1).groupby(nasa.index.year).sum()
    tmax = nasa.groupby(nasa.index.year).mean()
    tmax = tmax.loc[jours[jours >= 360].index]

    f = pd.read_csv(ROOT / "data/raw/t3_offre/faostat_cacao.csv")
    f = f[f["Area"].isin(NOMS_FAO) & (f["Element"] == "Production")].assign(pays=lambda x: x["Area"].map(NOMS_FAO))
    prod = f.rename(columns={"Year": "annee", "Value": "production_t", "Flag": "code_fao"})[["pays", "annee", "production_t", "code_fao"]]

    meteo = pd.concat({"pluie_mm": pluie.stack(), "tmax_c": tmax.stack()}, axis=1).rename_axis(["annee", "pays"]).reset_index()
    panel = prod.merge(meteo, on=["pays", "annee"], how="outer").sort_values(["pays", "annee"])
    panel = panel[(panel["annee"] >= 1991) & (panel["annee"] <= 2025)]
    panel.to_parquet(ROOT / "data/processed/impact_panel.parquet", index=False)
    print(f"Panel : {panel.shape}, annees {panel['annee'].min()}-{panel['annee'].max()}")
    print(panel.groupby("pays").agg(prod=("production_t", "count"), pluie=("pluie_mm", "count"), tmax=("tmax_c", "count"),
                                    pluie_moy=("pluie_mm", "mean"), tmax_moy=("tmax_c", "mean")).round(0).to_string())
    print("Codes FAO de la production :", panel["code_fao"].value_counts().to_dict())


if __name__ == "__main__":
    main()
