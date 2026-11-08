"""Thematique 1 : detecte les anomalies des series brutes, sans les modifier.

Un point suspect est un saut quotidien > seuil suivi d'un retour quasi complet
le lendemain (aller-retour), signe habituel d'une erreur de cotation.
Sortie : outputs/metriques/t1_anomalies.csv

Usage : .venv/Scripts/python.exe scripts/02_controler_t1.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BRUT = ROOT / "data" / "raw" / "t1_marches"
SORTIE = ROOT / "outputs" / "metriques" / "t1_anomalies.csv"
SEUIL_LOG = 0.15          # environ 16 % en un jour
TOLERANCE_RETOUR = 0.5    # le lendemain annule au moins la moitie du saut

pd.set_option("display.width", 200, "display.max_columns", None, "display.max_rows", 500)


def charger(fichier: Path) -> pd.DataFrame:
    return pd.read_csv(fichier, index_col="date", parse_dates=True)


def allers_retours(close: pd.Series) -> pd.DataFrame:
    positif = close[close > 0]
    r = np.log(positif).diff()
    suivant = r.shift(-1)
    masque = (r.abs() > SEUIL_LOG) & (np.sign(suivant) == -np.sign(r)) \
        & (suivant.abs() >= TOLERANCE_RETOUR * r.abs())
    return pd.DataFrame({
        "date": r.index[masque],
        "avant": positif.shift(1)[masque].values,
        "valeur": positif[masque].values,
        "apres": positif.shift(-1)[masque].values,
    })


def main() -> None:
    lignes = []
    print("=== Allers-retours et sauts par serie ===")
    for f in sorted(BRUT.glob("*.csv")):
        df = charger(f)
        close = df["Close"].dropna()
        ar = allers_retours(close).assign(serie=f.stem)
        lignes.append(ar)
        r = np.log(close[close > 0]).diff().abs()
        print(f"{f.stem:12} allers-retours={len(ar):4d}  sauts>16%={int((r > SEUIL_LOG).sum()):4d}  "
              f"derniere date={close.index.max().date()}")
    resultat = pd.concat(lignes, ignore_index=True)
    resultat.to_csv(SORTIE, index=False)

    print("\n=== Detail des allers-retours (20 premiers par serie) ===")
    for serie, g in resultat.groupby("serie"):
        print(f"\n{serie} ({len(g)})")
        print(g.drop(columns="serie").head(20).to_string(index=False))

    print("\n=== Cacao : 12 plus forts mouvements, volume et open interest absent ===")
    cc = charger(BRUT / "CC_F.csv")
    cc["r"] = cc["Close"].pct_change()
    top = cc["r"].abs().nlargest(12).index.sort_values()
    print(cc.loc[top, ["Open", "High", "Low", "Close", "Volume", "r"]].round(3))
    print("\nAutour du 2024-09-16 :")
    print(cc.loc["2024-09-11":"2024-09-19", ["Open", "High", "Low", "Close", "Volume", "r"]].round(3))
    print("\nJours de volume nul :", int((cc["Volume"] == 0).sum()), "sur", len(cc))
    print("Volume nul par annee :", cc[cc["Volume"] == 0].groupby(cc[cc["Volume"] == 0].index.year).size().to_dict())
    print("Fin d'annee (Close) :", cc["Close"].resample("YE").last().round(0).astype(int).to_dict())

    print("\n=== Parite EUR/XOF : valeurs distinctes ===")
    xof = charger(BRUT / "EURXOF_X.csv")["Close"]
    print(xof.round(3).value_counts().head(8))
    print(xof.tail(4))

    print("\n=== MDLZ autour de la scission ===")
    m = charger(BRUT / "MDLZ.csv")
    print(m.loc["2012-09-27":"2012-10-04", ["Close", "Adj Close"]].round(2))

    print("\n=== Dernieres lignes de change ===")
    print(charger(BRUT / "EURUSD_X.csv").tail(2)[["Open", "High", "Low", "Close"]].round(4))


if __name__ == "__main__":
    main()
