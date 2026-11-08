"""Construit la grille quotidienne de la thematique 1, sur les seances de CC=F.

Sorties :
- data/processed/grille_quotidienne_t1.parquet
- outputs/metriques/t1_nettoyage_change.csv

Usage : .venv/Scripts/python.exe scripts/06_construire_grille_quotidienne.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cacao.grille import (aligner, cibles, cibles_sans_sauts, erreurs_de_cotation,  # noqa: E402
                          jours_de_saut, passage_dans_horizon)

BRUT = ROOT / "data/raw/t1_marches"
HORIZONS = [1, 5, 20, 60, 120]
ECARTES = {"EURXOF=X"}  # valeurs incompatibles avec une parite fixe
# Revue du 2026-11-07 : IDR fige a 9 612 au milieu de cotations a 11 800 ; NGN divise par 100
# en janvier 2011 ; NGN a 232 au lieu de 322 en juin 2017. Forme : debut, fin, borne basse, borne haute.
ABERRANTS = {"IDR=X": [("2013-11-01", "2013-12-31", 0, 10000)],
             "NGN=X": [("2011-01-20", "2011-01-31", 0, 10), ("2017-06-14", "2017-06-20", 200, 250)]}


def cotations_aberrantes(s: pd.Series, ticker: str) -> pd.Series:
    """Valeurs retirees apres revue, sur des plages hors de tout niveau voisin."""
    masque = pd.Series(False, index=s.index)
    for debut, fin, bas, haut in ABERRANTS.get(ticker, []):
        p = s.loc[debut:fin]
        masque.loc[p.index[(p > bas) & (p < haut)]] = True
    return masque


def fichier(ticker: str) -> Path:
    return BRUT / (ticker.replace("=", "_").replace("^", "idx_") + ".csv")


def colonne(ticker: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", ticker.lower().replace("^", "")).strip("_")


def main() -> None:
    config = yaml.safe_load((ROOT / "config/t1_marches.yaml").read_text(encoding="utf-8"))
    cc = pd.read_csv(fichier("CC=F"), index_col="date", parse_dates=True)
    axe = cc.index
    grille = pd.DataFrame({
        "cacao_close": cc["Close"],
        "cacao_volume": cc["Volume"],
        "volume_nul": (cc["Volume"] == 0).astype(int),
        "volume_faible": (cc["Volume"] < 100).astype(int),
    })

    passages = pd.DatetimeIndex(pd.read_csv(ROOT / "outputs/metriques/t1_echeances_cacao.csv",
                                            parse_dates=["date"])["date"])
    saut = jours_de_saut(cc["Close"], passages)
    grille["saut_echeance"] = saut.astype(int)

    bilan = []
    for groupe, series in config["series"].items():
        if groupe == "cacao":
            continue
        for ticker in series:
            if ticker in ECARTES:
                continue
            df = pd.read_csv(fichier(ticker), index_col="date", parse_dates=True)
            prix = "Adj Close" if groupe == "chocolatiers" else "Close"
            s = df[prix].dropna().rename(colonne(ticker))
            n_erreurs = 0
            if groupe == "change":
                masque = erreurs_de_cotation(s) | cotations_aberrantes(s, ticker)
                n_erreurs = int(masque.sum())
                s = s.where(~masque)
                r = np.log(s.dropna()).diff().abs()
                restants = r[r > 0.15]
                bilan.append({"ticker": ticker, "erreurs_retirees": n_erreurs,
                              "sauts_restants": len(restants),
                              "dates_restantes": " ".join(str(d.date()) for d in restants.index)})
            grille[colonne(ticker)] = aligner(axe, s)

    grille = grille.join(cibles(cc["Close"], HORIZONS))
    grille = grille.join(cibles_sans_sauts(cc["Close"], saut, HORIZONS))
    for h in HORIZONS:
        grille[f"passage_dans_{h}"] = passage_dans_horizon(saut, h)

    sortie = ROOT / "data/processed/grille_quotidienne_t1.parquet"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    grille.to_parquet(sortie)
    rapport = pd.DataFrame(bilan)
    rapport.to_csv(ROOT / "outputs/metriques/t1_nettoyage_change.csv", index=False)

    pd.set_option("display.width", 200, "display.max_columns", None, "display.max_colwidth", 90)
    print(f"Grille : {grille.shape[0]} seances, {grille.shape[1]} colonnes, "
          f"{grille.index.min().date()} -> {grille.index.max().date()}")
    print("\nChange nettoye :")
    print(rapport.to_string(index=False))
    print("\nValeurs manquantes (%) :")
    variables = [c for c in grille.columns if c not in ("cacao_close",) and not c.startswith(("cible", "passage"))]
    manque = pd.DataFrame({"tout": grille[variables].isna().mean() * 100,
                           "depuis_2008": grille.loc["2008":, variables].isna().mean() * 100}).round(2)
    print(manque[manque["tout"] > 0])
    print("\nCibles :")
    for h in HORIZONS:
        c = grille[f"cible_hausse_{h}"].dropna()
        r = grille[f"cible_rendement_{h}"].dropna()
        print(f"h={h:2d} : {len(c)} lignes, hausse {c.mean():.1%}, rendement nul {(r == 0).sum()}, "
              f"passage dans la fenetre {grille[f'passage_dans_{h}'].mean():.1%}")
    print("Volatilite future 20 seances :", grille["cible_vol_20"].describe().round(3).to_dict())
    print("Seances cloture inchangee :", int((cc["Close"].diff() == 0).sum()),
          "| volume nul :", int(grille["volume_nul"].sum()),
          "| volume faible :", int(grille["volume_faible"].sum()),
          "| sauts d'echeance :", int(grille["saut_echeance"].sum()))


if __name__ == "__main__":
    main()
