"""Thematique 2 : compare NASA POWER a Open-Meteo (ERA5) sur les points de controle.

ERA5 et MERRA-2 sont deux reanalyses distinctes : un ecart ne dit pas laquelle a raison,
mais une rupture qui n'apparait que dans une source signale un probleme de cette source.

Sorties :
- outputs/metriques/t2_controle_openmeteo.csv : accord par variable et par periode
- outputs/metriques/t2_pluies_extremes.csv : plus fortes pluies NASA et valeur ERA5 du meme jour

Usage : .venv/Scripts/python.exe scripts/16_controler_meteo.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAIRES = {"PRECTOTCORR": "precipitation_sum", "T2M": "temperature_2m_mean",
          "T2M_MAX": "temperature_2m_max", "T2M_MIN": "temperature_2m_min",
          "RH2M": "relative_humidity_2m_mean", "GWETROOT": "soil_moisture_0_to_100cm_mean"}
PERIODES = {"2005-2019": ("2005-01-01", "2019-12-31"), "2020-2023": ("2020-01-01", "2023-12-31"),
            "2024-2026": ("2024-01-01", "2026-10-31")}
pd.set_option("display.width", 200, "display.max_columns", None)


def lire(source: str, ident: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / f"data/raw/t2_climat/{source}/{ident}.csv", index_col="date", parse_dates=True)


def main() -> None:
    ids = sorted(p.stem for p in (ROOT / "data/raw/t2_climat/era5_controle").glob("*.csv"))
    lignes, extremes = [], []
    for ident in ids:
        nasa, era = lire("power", ident), lire("era5_controle", ident)
        for var_n, var_e in PAIRES.items():
            a = pd.concat([nasa[var_n], era[var_e]], axis=1, keys=["n", "e"]).dropna()
            for nom, (d, f) in PERIODES.items():
                x = a.loc[d:f]
                m = x.resample("MS").sum() if var_n == "PRECTOTCORR" else x.resample("MS").mean()
                lignes.append({"id": ident, "pays": ident[:3], "variable": var_n, "periode": nom,
                               "corr_jour": x["n"].corr(x["e"]), "corr_mois": m["n"].corr(m["e"]),
                               "moy_nasa": x["n"].mean(), "moy_era5": x["e"].mean(),
                               "max_nasa": x["n"].max(), "max_era5": x["e"].max()})
        p = pd.concat([nasa["PRECTOTCORR"], era["precipitation_sum"]], axis=1, keys=["nasa", "era5"]).dropna()
        extremes.append(p.nlargest(5, "nasa").assign(id=ident))

    res = pd.DataFrame(lignes)
    res.round(3).to_csv(ROOT / "outputs/metriques/t2_controle_openmeteo.csv", index=False)
    ext = pd.concat(extremes).sort_values("nasa", ascending=False).reset_index()[["id", "date", "nasa", "era5"]]
    ext[["nasa", "era5"]] = ext[["nasa", "era5"]].round(1)
    ext.to_csv(ROOT / "outputs/metriques/t2_pluies_extremes.csv", index=False)

    print(f"{len(ids)} points compares\n")
    print(res.groupby(["variable", "periode"], sort=False)[["corr_jour", "corr_mois", "moy_nasa", "moy_era5"]]
          .median().round(3).to_string())
    pluie = res[res["variable"] == "PRECTOTCORR"].copy()
    pluie["ratio"] = pluie["moy_nasa"] / pluie["moy_era5"]
    print("\nRatio pluie moyenne NASA / ERA5 par pays et periode :")
    print(pluie.pivot_table(index="pays", columns="periode", values="ratio")[list(PERIODES)].round(2).to_string())
    print("\nCorrelation mensuelle de la pluie par pays et periode :")
    print(pluie.pivot_table(index="pays", columns="periode", values="corr_mois")[list(PERIODES)].round(2).to_string())
    print("\nPlus fortes pluies NASA et ERA5 du meme jour :")
    print(ext.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
