"""Extrait les tableaux ICCO lisibles et les compare a FAOSTAT et MapSPAM.

Chaque ligne garde sa date de publication : c'est ce qui etait connu ce jour-la.
Une saison ICCO comme 2022/23 est comparee a l'annee FAOSTAT 2023 : c'est une
convention de lecture, pas une equivalence exacte.

Sorties :
- data/interim/icco_production_editions.csv
- outputs/metriques/t3_comparaison_icco.csv

Usage : .venv/Scripts/python.exe scripts/10_comparer_icco.py
"""
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ICCO = ROOT / "data/raw/t3_offre/icco"
PAYS = ["Cameroon", "Côte d'Ivoire", "Ghana", "Nigeria", "Brazil", "Ecuador", "Indonesia",
        "Papua New Guinea", "World total"]
pd.set_option("display.width", 200, "display.max_columns", None, "display.max_rows", 200)


def lire_edition(pdf: Path) -> list[dict]:
    texte = "\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
    if "Indonesia" not in texte:
        return []
    texte = texte.replace("’", "'")
    saisons = sorted(set(re.findall(r"(\d{4})\s*/\s*(\d{2})", texte.split("Africa")[0])))
    annees = [int(a) for a, _ in saisons]
    if annees != list(range(annees[0], annees[0] + len(annees))):
        raise ValueError(f"{pdf.name} : saisons non consecutives {saisons}")
    saisons = [f"{a}/{b}" for a, b in saisons]
    trouve = re.search(r"Published\s*:\s*([\d\s-]{10,14}\d)", texte)
    date_publication = re.sub(r"\s", "", trouve[1])  # le PDF coupe parfois les chiffres
    lignes = []
    for brut in texte.splitlines():
        for pays in PAYS:
            if brut.strip().startswith(pays):
                reste = re.sub(r"^\d+\s", " ", brut.strip()[len(pays):])  # note de bas de page collee
                reste = re.sub(r"\d+(\.\s?\d*)?\s?%", " ", reste)  # retire les parts en %
                valeurs = [float(v) for v in re.findall(r"\d+", reste)]
                if len(valeurs) != len(saisons):
                    raise ValueError(f"{pdf.name} : {brut!r} ne correspond pas a {saisons}")
                for s, v in zip(saisons, valeurs):
                    lignes.append({"edition": pdf.stem.replace("Production_QBCS-", ""),
                                   "publie": pd.to_datetime(date_publication, format="%d-%m-%Y"),
                                   "saison": s, "pays": pays, "kt": v})
    return lignes


def main() -> None:
    lignes = [l for f in sorted(ICCO.glob("*.pdf")) for l in lire_edition(f)]
    icco = pd.DataFrame(lignes).sort_values(["publie", "pays", "saison"])
    icco.to_csv(ROOT / "data/interim/icco_production_editions.csv", index=False)
    print(f"{icco['edition'].nunique()} editions, {len(icco)} valeurs, "
          f"publiees du {icco['publie'].min().date()} au {icco['publie'].max().date()}")
    print("Saisons :", sorted(icco["saison"].unique()))

    derniere = icco.sort_values("publie").groupby(["saison", "pays"]).tail(1)
    tab = derniere.pivot(index="pays", columns="saison", values="kt")
    print("\n=== ICCO, derniere edition disponible par saison (kt) ===")
    print(tab.reindex(PAYS).astype("Int64"))

    fao = pd.read_csv(ROOT / "data/raw/t3_offre/faostat_cacao.csv")
    prod = fao[fao["Element"] == "Production"].pivot_table(index="Year", columns="Area", values="Value") / 1000
    noms = {"Cameroon": "Cameroon", "Côte d'Ivoire": "Côte d'Ivoire", "Ghana": "Ghana", "Nigeria": "Nigeria",
            "Brazil": "Brazil", "Ecuador": "Ecuador", "Indonesia": "Indonesia",
            "Papua New Guinea": "Papua New Guinea", "World total": "World"}
    lignes = []
    for s in ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24"]:
        annee = int(s[:4]) + 1
        for pays, nom in noms.items():
            if s in tab.columns and annee in prod.index:
                i, f = tab.loc[pays, s], prod.loc[annee, nom]
                lignes.append({"saison": s, "annee_fao": annee, "pays": pays, "icco_kt": i,
                               "faostat_kt": round(f), "fao_sur_icco": round(f / i, 2)})
    comp = pd.DataFrame(lignes)
    comp.to_csv(ROOT / "outputs/metriques/t3_comparaison_icco.csv", index=False)
    print("\n=== FAOSTAT divise par ICCO ===")
    print(comp.pivot(index="pays", columns="saison", values="fao_sur_icco").reindex(PAYS))
    print("\n=== Detail 2023/24 ===")
    print(comp[comp["saison"] == "2023/24"].to_string(index=False))

    print("\n=== Moyenne 2020/21 et 2021/22 contre MapSPAM 2020 (kt), 2019/20 absente ===")
    spam = pd.read_csv(ROOT / "outputs/metriques/t3_comparaison_faostat_mapspam.csv")
    spam = spam[spam["millesime"] == 2020].set_index("pays")["mapspam_t"] / 1000
    alias = {"Côte d'Ivoire": "Ivoire", "World total": "MONDE"}
    for pays in ["Côte d'Ivoire", "Ghana", "Nigeria", "Cameroon", "Brazil", "Ecuador", "Indonesia", "World total"]:
        sous = comp[(comp["pays"] == pays) & comp["saison"].isin(["2019/20", "2020/21", "2021/22"])]
        m = spam[alias.get(pays, pays)]
        print(f"{pays:15} ICCO {sous['icco_kt'].mean():6.0f}  FAOSTAT {sous['faostat_kt'].mean():6.0f}  MapSPAM {m:6.0f}")

    print("\n=== Revisions : premiere et derniere valeur publiees ===")
    for pays in ["Côte d'Ivoire", "Ghana", "World total"]:
        g = icco[(icco["pays"] == pays) & icco["saison"].isin(["2021/22", "2022/23", "2023/24"])]
        for s, x in g.sort_values("publie").groupby("saison"):
            print(f"{pays:15} {s} : {x['kt'].iloc[0]:6.0f} ({x['publie'].iloc[0].date()}) -> "
                  f"{x['kt'].iloc[-1]:6.0f} ({x['publie'].iloc[-1].date()}), {len(x)} editions")


if __name__ == "__main__":
    main()
