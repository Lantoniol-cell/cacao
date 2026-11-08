"""Compare MapSPAM et FAOSTAT pour le cacao en Indonesie.

MapSPAM 2017 ne couvre que l'Afrique subsaharienne : il n'apparait pas ici.
Le rendement MapSPAM est calcule comme production / surface recoltee.
Sortie : outputs/metriques/t3_indonesie_faostat_mapspam.csv

Usage : .venv/Scripts/python.exe scripts/11_indonesie_faostat_mapspam.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPAM = ROOT / "MapSPAM zones de production"
SORTIE = ROOT / "outputs/metriques/t3_indonesie_faostat_mapspam.csv"
pd.set_option("display.width", 200, "display.max_columns", None, "display.max_rows", 100)


def somme_iso(motif: str) -> float:
    d = pd.read_csv(next(SPAM.rglob(motif)), usecols=["iso3", "coco_a"], encoding="latin-1")
    return float(d.loc[d["iso3"].str.strip('"') == "IDN", "coco_a"].sum())


def somme_2020(motif: str) -> float:
    d = pd.read_csv(next(SPAM.rglob(motif)), usecols=["ADM0_NAME", "coco"], encoding="utf-8",
                    encoding_errors="replace")
    return float(d.loc[d["ADM0_NAME"] == "Indonesia", "coco"].sum())


def main() -> None:
    spam = {
        2005: (somme_iso("spam2005V3r2_global_P_TA.csv"), somme_iso("spam2005V3r2_global_H_TA.csv")),
        2010: (somme_iso("spam2010V2r0_global_P_TA.csv"), somme_iso("spam2010V2r0_global_H_TA.csv")),
        2020: (somme_2020("spam2020V2r2_global_P_TA.csv"), somme_2020("spam2020V2r2_global_H_TA.csv")),
    }
    fao = pd.read_csv(ROOT / "data/raw/t3_offre/faostat_cacao.csv")
    idn = fao[fao["Area"] == "Indonesia"].pivot_table(index="Year", columns="Element", values="Value")

    lignes = []
    for annee, (prod, surface) in spam.items():
        f = idn.loc[annee - 1:annee + 1]
        lignes.append({
            "millesime": annee,
            "spam_production_t": round(prod),
            "fao_annee_t": round(idn.loc[annee, "Production"]),
            "fao_moy3_t": round(f["Production"].mean()),
            "ecart_production_pct": round((prod / f["Production"].mean() - 1) * 100, 1),
            "spam_surface_ha": round(surface),
            "fao_surface_moy3_ha": round(f["Area harvested"].mean()),
            "ecart_surface_pct": round((surface / f["Area harvested"].mean() - 1) * 100, 1),
            "spam_rendement_kg_ha": round(prod / surface * 1000),
            "fao_rendement_moy3_kg_ha": round(f["Production"].mean() / f["Area harvested"].mean() * 1000),
        })
    r = pd.DataFrame(lignes)
    r.to_csv(SORTIE, index=False)
    print(r.T.to_string())
    print("\nFAOSTAT Indonesie, annees autour des millesimes :")
    print(idn.loc[[2004, 2005, 2006, 2009, 2010, 2011, 2019, 2020, 2021, 2022, 2023, 2024]].round(0))


if __name__ == "__main__":
    main()
