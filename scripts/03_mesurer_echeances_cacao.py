"""Mesure les changements d'echeance suspects de CC=F, sans modifier les donnees.

Yahoo garde parfois l'echeance proche alors que le marche est deja passe a la
suivante : le volume s'effondre, puis remonte d'un coup. Un jour suspect est un
jour de volume >= 1000 precede de 3 seances sous 100 contrats.
Sortie : outputs/metriques/t1_echeances_cacao.csv

Usage : .venv/Scripts/python.exe scripts/03_mesurer_echeances_cacao.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SORTIE = ROOT / "outputs" / "metriques" / "t1_echeances_cacao.csv"
FAIBLE, FORT, FENETRE = 100, 1000, 3


def main() -> None:
    cc = pd.read_csv(ROOT / "data/raw/t1_marches/CC_F.csv", index_col="date", parse_dates=True)
    cc["r"] = np.log(cc["Close"]).diff()
    faible = cc["Volume"] < FAIBLE
    print(f"Seances sous {FAIBLE} contrats : {int(faible.sum())} sur {len(cc)} ({faible.mean():.1%})")

    avant = faible.shift(1).rolling(FENETRE).sum() == FENETRE
    suspect = avant & (cc["Volume"] >= FORT)
    table = cc.loc[suspect, ["Close", "Volume", "r"]].copy()
    # Le saut peut tomber le jour meme ou le suivant : on retient le plus grand.
    table["r_lendemain"] = cc["r"].shift(-1)[suspect]
    table["saut_max_pct"] = (np.exp(table[["r", "r_lendemain"]].abs().max(axis=1)) - 1) * 100
    table.to_csv(SORTIE)

    print(f"Passages suspects : {len(table)}, soit {len(table) / cc.index.year.nunique():.1f} par an")
    print("Par annee :", table.groupby(table.index.year).size().to_dict())
    print("Saut max moyen par periode (%) :")
    for debut, fin in [("2005", "2022"), ("2023", "2026")]:
        s = table.loc[debut:fin, "saut_max_pct"]
        print(f"  {debut}-{fin} : moyenne {s.mean():.1f}, max {s.max():.1f}, n={len(s)}")
    print("\n8 plus grands sauts :")
    print(table.nlargest(8, "saut_max_pct").sort_index().round(3))

    hebdo = cc["Close"].resample("W-FRI").last()
    semaines = np.sign(np.log(hebdo).diff().dropna())
    corrige = cc["r"].copy()
    jours = set(table.index) | set(cc.index[cc.index.searchsorted(table.index) + 1])
    corrige.loc[corrige.index.isin(jours)] = 0.0
    alt = np.sign(corrige.resample("W-FRI").sum().reindex(semaines.index))
    diff = semaines[(semaines != alt) & (alt != 0)]
    print(f"\nSemaines dont le sens change si ces jours sont neutralises : {len(diff)} sur {len(semaines)}")
    print("Dont 2023-2026 :", int((diff.index.year >= 2023).sum()))


if __name__ == "__main__":
    main()
