"""Compare la production de cacao par pays : MapSPAM contre FAOSTAT.

Sortie : outputs/metriques/t3_comparaison_faostat_mapspam.csv

Usage : .venv/Scripts/python.exe scripts/08_comparer_faostat_mapspam.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTRAIT = ROOT / "MapSPAM zones de production/extrait"
SORTIE = ROOT / "outputs/metriques/t3_comparaison_faostat_mapspam.csv"
PAYS = {  # nom FAOSTAT : (iso3, nom MapSPAM 2020)
    "Ivoire": ("CIV", "Cote dIvoire"), "Ghana": ("GHA", "Ghana"), "Indonesia": ("IDN", "Indonesia"),
    "Ecuador": ("ECU", "Ecuador"), "Cameroon": ("CMR", "Cameroon"), "Brazil": ("BRA", "Brazil"),
    "Nigeria": ("NGA", "Nigeria"), "Peru": ("PER", "Peru"),
}
pd.set_option("display.width", 200, "display.max_columns", None)


def mapspam_iso(fichier: Path) -> tuple[pd.Series, float]:
    d = pd.read_csv(fichier, usecols=["iso3", "coco_a"], encoding="latin-1")
    d["iso3"] = d["iso3"].str.strip('"')
    g = d.groupby("iso3")["coco_a"].sum()
    return g, float(g.sum())


def mapspam_2020() -> tuple[pd.Series, float]:
    f = next(EXTRAIT.rglob("spam2020V2r2_global_P_TA.csv"))
    d = pd.read_csv(f, usecols=["ADM0_NAME", "coco"], encoding="utf-8", encoding_errors="replace")
    g = d.groupby("ADM0_NAME")["coco"].sum()
    return g, float(g.sum())


def main() -> None:
    fao = pd.read_csv(ROOT / "data/raw/t3_offre/faostat_cacao.csv")
    prod = fao[fao["Element"] == "Production"].pivot_table(index="Year", columns="Area", values="Value")

    def fao_val(pays: str, annee: int, moy: bool = False) -> float:
        col = next(c for c in prod.columns if pays in c)
        fen = range(annee - 1, annee + 2) if moy else [annee]
        return float(prod.loc[[a for a in fen if a in prod.index], col].mean())

    lignes = []
    sources = [
        (2005, *mapspam_iso(next(EXTRAIT.rglob("spam2005V3r2_global_P_TA.csv"))), "iso"),
        (2010, *mapspam_iso(next(EXTRAIT.rglob("spam2010V2r0_global_P_TA.csv"))), "iso"),
        (2020, *mapspam_2020(), "nom"),
    ]
    for annee, serie, total, cle in sources:
        for pays, (iso, nom) in PAYS.items():
            spam = float(serie.get(iso if cle == "iso" else nom, float("nan")))
            f1, f3 = fao_val(pays, annee), fao_val(pays, annee, True)
            lignes.append({"millesime": annee, "pays": pays, "mapspam_t": round(spam),
                           "faostat_annee_t": round(f1), "faostat_moy3_t": round(f3),
                           "ecart_moy3_pct": round((spam / f3 - 1) * 100, 1)})
        f3 = fao_val("World", annee, True)
        lignes.append({"millesime": annee, "pays": "MONDE", "mapspam_t": round(total),
                       "faostat_annee_t": round(fao_val("World", annee)), "faostat_moy3_t": round(f3),
                       "ecart_moy3_pct": round((total / f3 - 1) * 100, 1)})

    r = pd.DataFrame(lignes)
    r.to_csv(SORTIE, index=False)
    print(r.to_string(index=False))

    print("\nParts mondiales (%) :")
    for a in (2005, 2010, 2020):
        m = r[r["millesime"] == a].set_index("pays")
        parts = pd.DataFrame({"mapspam": m["mapspam_t"] / m.loc["MONDE", "mapspam_t"] * 100,
                              "faostat": m["faostat_moy3_t"] / m.loc["MONDE", "faostat_moy3_t"] * 100})
        print(a, parts.drop("MONDE").round(1).T.to_string())

    print("\nFAOSTAT, derniere annee et drapeaux pour la Cote d'Ivoire et le monde :")
    p = fao[(fao["Element"] == "Production") & (fao["Year"] >= 2018)
            & (fao["Area"].str.contains("Ivoire|^World$"))]
    print(p.pivot_table(index="Year", columns="Area", values="Value").round(0))
    print("Drapeaux :", p["Flag"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
