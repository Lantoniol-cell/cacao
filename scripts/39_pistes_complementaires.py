"""Analyses exploratoires du point 11 de protocole.md, validees le 2026-11-08.

A. Variation future de l'ecart a la tendance (log P - log MA120), 60 et 120 seances.
   Benchmark : regression sur l'ecart actuel seul. Le modele recoit les facteurs plus
   l'ecart actuel, pour que le benchmark soit un sous-ensemble de son information.
B. Volatilite au-dela du HAR (volatilites passees a 5, 20 et 60 seances), 5 a 120 seances.
   Les facteurs prevoient le residu du HAR, estime sur l'entrainement de chaque pli.
C. Perte au retrait de la famille investisseurs_biais, en regime de haute et de basse
   volatilite (vol 60 seances au-dessus du 80e centile de son passe strict), 9 cibles.

Gradient Boosting seulement, reglages du point 4, validation annuelle 2010-2026, purge h.
Intervalles : 98,75 % pour A et B, 99,72 % pour C (Bonferroni dans chaque bloc).
Pour C, le bootstrap tire des blocs dans les seances du regime, qui ne sont pas toujours
consecutives : l'intervalle est donc approximatif.

Sorties : outputs/metriques/pistes_ecart.csv, pistes_har.csv, pistes_regime.csv

Usage : PYTHONPATH=src .venv/Scripts/python.exe -u scripts/39_pistes_complementaires.py
"""
import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cacao.evaluation import GRAINE, boosting, ecart_bootstrap, plis, predire, score
from cacao.grille import cibles_ecart, ecart_tendance
from cacao.variables import construire

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/metriques"
DEBUT, FIN, TIRAGES = 2010, 2026, 1000
NIVEAU_AB, NIVEAU_C = 1 - 0.05 / 4, 1 - 0.05 / 18
PERIODES = {"2010-2026": (2010, 2026), "2010-2023": (2010, 2023), "2024-2026": (2024, 2026)}
pd.set_option("display.width", 220, "display.max_columns", None)


def lineaire(Z: pd.DataFrame, y: pd.Series, classification: bool, h: int) -> pd.Series:
    """Benchmark lineaire refait a chaque pli sur le passe purge."""
    sortie = pd.Series(index=Z.index, dtype=float)
    for train, test in plis(Z.index, DEBUT, FIN, h):
        ok = train[(y.iloc[train].notna() & Z.iloc[train].notna().all(axis=1)).to_numpy()]
        t = test[Z.iloc[test].notna().all(axis=1).to_numpy()]
        if classification:
            m = make_pipeline(StandardScaler(), LogisticRegression(random_state=GRAINE)).fit(Z.iloc[ok], y.iloc[ok].astype(int))
            sortie.iloc[t] = m.predict_proba(Z.iloc[t])[:, 1]
        else:
            sortie.iloc[t] = LinearRegression().fit(Z.iloc[ok], y.iloc[ok]).predict(Z.iloc[t])
    return sortie


def har_plus_facteurs(X: pd.DataFrame, Z: pd.DataFrame, y: pd.Series, h: int) -> tuple[pd.Series, pd.Series]:
    """HAR seul, et HAR plus le residu prevu par le Gradient Boosting sur les facteurs."""
    har, total = pd.Series(index=X.index, dtype=float), pd.Series(index=X.index, dtype=float)
    for train, test in plis(X.index, DEBUT, FIN, h):
        ok = train[(y.iloc[train].notna() & Z.iloc[train].notna().all(axis=1)).to_numpy()]
        t = test[Z.iloc[test].notna().all(axis=1).to_numpy()]
        m = LinearRegression().fit(Z.iloc[ok], y.iloc[ok])
        residu = y.iloc[ok] - m.predict(Z.iloc[ok])
        cols = X.columns[X.iloc[ok].notna().any().to_numpy()]
        g = boosting(False).fit(X.iloc[ok][cols], residu)
        har.iloc[t] = m.predict(Z.iloc[t])
        total.iloc[t] = har.iloc[t] + g.predict(X.iloc[t][cols])
    return har, total


def qlike(y: pd.Series, f: pd.Series) -> float:
    i = y.notna() & f.notna()
    ratio = y[i] ** 2 / f[i].clip(lower=1e-4) ** 2
    return float((ratio - np.log(ratio) - 1).mean())


def comparer(y, p, ref, classification, h, niveau, **etiquettes) -> dict:
    c = y.dropna().index.intersection(p.dropna().index).intersection(ref.dropna().index)
    c = c[(c.year >= DEBUT) & (c.year <= FIN)]
    ecart, bas, haut = ecart_bootstrap(y[c], p[c], ref[c], classification, bloc=max(20, h), tirages=TIRAGES, niveau=niveau)
    ligne = {**etiquettes, "horizon": h, "n": len(c), "fenetres_independantes": len(c) // h,
             "ecart": ecart, "ic_bas": bas, "ic_haut": haut, "bat_benchmark": bool(bas > 0)}
    for per, (a, b) in PERIODES.items():
        k = c[(c.year >= a) & (c.year <= b)]
        if len(k) == 0:  # decoupe par annees : une des periodes est vide
            continue
        ligne[f"score_{per}"] = score(y[k], p[k], classification)
        ligne[f"benchmark_{per}"] = score(y[k], ref[k], classification)
        if classification and y[k].nunique() == 2:
            ligne[f"auc_{per}"] = roc_auc_score(y[k].astype(int), p[k])
    return ligne


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    close, saut = d["cacao_close"], d["saut_echeance"].astype(bool)
    t0 = time.time()

    # A. Ecart a la tendance
    ce = cibles_ecart(close, saut, [60, 120])
    D = ecart_tendance(close).rename("ecart_tendance")
    a = []
    for h in (60, 120):
        X, _ = construire(d, h)
        X = X.join(D)
        for lecture, suffixe in (("brute", ""), ("sans_sauts", "neutre_")):
            for nature, col, classification in (("sens", f"cible_ecart_hausse_{suffixe}{h}", True),
                                                ("valeur", f"cible_ecart_{suffixe}{h}", False)):
                y = ce[col]
                p, _ = predire(X, y, boosting, classification, DEBUT, FIN, h)
                ref = lineaire(D.to_frame(), y, classification, h)
                a.append(comparer(y, p, ref, classification, h, NIVEAU_AB, cible=f"ecart_{nature}", lecture=lecture))
        print(f"A h={h} fait, {(time.time() - t0) / 60:.0f} min", flush=True)
    a = pd.DataFrame(a)
    a.to_csv(OUT / "pistes_ecart.csv", index=False)

    # B. Volatilite au-dela du HAR
    r = np.log(close).diff()
    Z = pd.DataFrame({f"vol{n}": r.rolling(n).std() * np.sqrt(252) for n in (5, 20, 60)})
    b = []
    for h in (5, 20, 60, 120):
        X, _ = construire(d, h)
        y = d[f"cible_vol_{h}"]
        har, total = har_plus_facteurs(X, Z, y, h)
        persistance = r.rolling(h).std() * np.sqrt(252)
        ligne = comparer(y, total, har, False, h, NIVEAU_AB, cible="vol_har", lecture="brute")
        ligne |= {"qlike_modele": qlike(y, total), "qlike_har": qlike(y, har), "qlike_persistance": qlike(y, persistance),
                  "rmse_persistance": -score(y[har.dropna().index], persistance[har.dropna().index], False)}
        b.append(ligne)
        print(f"B h={h} fait, {(time.time() - t0) / 60:.0f} min", flush=True)
    b = pd.DataFrame(b)
    b.to_csv(OUT / "pistes_har.csv", index=False)

    # C. Regime de volatilite et famille investisseurs_biais
    vol60 = r.rolling(60).std()
    seuil = vol60.expanding(min_periods=252).quantile(0.8).shift(1)
    regime = pd.Series(np.where(seuil.isna(), np.nan, (vol60 > seuil).astype(float)), index=d.index)
    print("Part de seances en regime haut :", {p: round(float(regime.loc[str(x):str(y)].mean()), 3)
                                               for p, (x, y) in PERIODES.items()}, flush=True)
    base = pd.read_parquet(OUT / "modele_predictions.parquet")
    c = []
    for cible, h in [("sens", h) for h in (1, 5, 20, 60, 120)] + [("vol", h) for h in (5, 20, 60, 120)]:
        classification = cible == "sens"
        y = d[f"cible_hausse_{h}"] if classification else d[f"cible_vol_{h}"]
        X, fam = construire(d, h)
        p_base = base[f"{cible}_{h}_brute_gradient_boosting"].reindex(d.index)
        p_sans, _ = predire(X.drop(columns=fam["investisseurs_biais"]), y, boosting, classification, DEBUT, FIN, h)
        decoupes = {"regime_haut": regime == 1, "regime_bas": regime == 0,
                    "annees_2010_2023": pd.Series(d.index.year <= 2023, index=d.index),
                    "annees_2024_2026": pd.Series(d.index.year >= 2024, index=d.index)}
        for nom, masque in decoupes.items():
            yy = y.where(masque)
            ligne = comparer(yy, p_base, p_sans, classification, h, NIVEAU_C, cible=cible, decoupe=nom)
            ligne["lecture_ecart"] = "perte au retrait de investisseurs_biais (positif : la famille aide)"
            c.append(ligne)
        print(f"C {cible} h={h} fait, {(time.time() - t0) / 60:.0f} min", flush=True)
    c = pd.DataFrame(c)
    c.to_csv(OUT / "pistes_regime.csv", index=False)

    print("\nA. Ecart a la tendance :")
    print(a[["cible", "lecture", "horizon", "score_2010-2026", "benchmark_2010-2026", "ecart", "ic_bas", "ic_haut", "bat_benchmark"]].round(4).to_string(index=False))
    print("\nB. Volatilite, HAR plus facteurs face au HAR (score = -RMSE) :")
    print(b[["horizon", "score_2010-2026", "benchmark_2010-2026", "rmse_persistance", "ecart", "ic_bas", "ic_haut",
             "bat_benchmark", "qlike_modele", "qlike_har", "qlike_persistance"]].round(4).to_string(index=False))
    print("\nC. Perte au retrait de investisseurs_biais :")
    print(c[["cible", "horizon", "decoupe", "n", "ecart", "ic_bas", "ic_haut", "bat_benchmark"]].round(4).to_string(index=False))
    print(f"\nDuree : {(time.time() - t0) / 60:.0f} min")


if __name__ == "__main__":
    main()
