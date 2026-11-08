"""Point 13 de protocole.md : regression des rendements cumules a h seances.

Gradient Boosting (reglages du point 4) contre marche aleatoire (rendement nul) et moyenne
passee. RMSE sur les rendements, intervalle bootstrap a 99 % par blocs de max(20, h).
Lecture de controle : sans passage d'echeance jusqu'a 20 seances ; jours de saut mis a zero
a 60 et 120 seances.

Sorties : outputs/metriques/regression_rendements.csv, regression_predictions.parquet

Usage : PYTHONPATH=src .venv/Scripts/python.exe -u scripts/44_regression_rendements.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.evaluation import boosting, ecart_bootstrap, plis, predire, score
from cacao.variables import construire

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/metriques"
HORIZONS, DEBUT, FIN, NIVEAU = [1, 5, 20, 60, 120], 2010, 2026, 0.99
PERIODES = {"2010-2026": (2010, 2026), "2010-2023": (2010, 2023), "2024-2026": (2024, 2026)}


def moyenne_passee(y: pd.Series, h: int) -> pd.Series:
    p = pd.Series(index=y.index, dtype=float)
    for train, test in plis(y.index, DEBUT, FIN, h):
        p.iloc[test] = y.iloc[train].mean()
    return p


def evaluer(y, p, bench, h, lecture, masque=None) -> dict:
    if masque is not None:
        y = y[masque.reindex(y.index).fillna(False).astype(bool)]
    notes = {k: score(y[(y.index.year >= DEBUT)], v.reindex(y.index)[(y.index.year >= DEBUT)], False) for k, v in bench.items()}
    nom = max(notes, key=notes.get)
    ref = bench[nom]
    c = y.dropna().index.intersection(p.dropna().index).intersection(ref.dropna().index)
    c = c[(c.year >= DEBUT) & (c.year <= FIN)]
    ecart, bas, haut = ecart_bootstrap(y[c], p[c], ref[c], False, bloc=max(20, h), tirages=1000, niveau=NIVEAU)
    ligne = {"horizon": h, "lecture": lecture, "benchmark": nom, "n": len(c), "ecart_rmse": ecart, "ic_bas": bas, "ic_haut": haut,
             "bat_benchmark": bool(bas > 0), "mae_modele": float((y[c] - p[c]).abs().mean()),
             "mae_benchmark": float((y[c] - ref[c]).abs().mean()),
             "signe_correct_modele": float((np.sign(p[c]) == np.sign(y[c])).mean())}
    for per, (a, b) in PERIODES.items():
        k = c[(c.year >= a) & (c.year <= b)]
        ligne[f"rmse_modele_{per}"] = -score(y[k], p[k], False)
        ligne[f"rmse_benchmark_{per}"] = -score(y[k], ref[k], False)
    return ligne


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    close, saut = d["cacao_close"], d["saut_echeance"].astype(bool)
    r_neutre = np.log(close).diff().where(~saut, 0.0).fillna(0).cumsum()
    t0, lignes, preds = time.time(), [], {}
    for h in HORIZONS:
        X, _ = construire(d, h)
        y = close.shift(-h) / close - 1
        p, _ = predire(X, y, boosting, False, DEBUT, FIN, h)
        bench = {"marche_aleatoire": pd.Series(0.0, index=d.index).where(y.notna() | True), "moyenne_passee": moyenne_passee(y, h)}
        lignes.append(evaluer(y, p, bench, h, "brute"))
        preds[f"rendement_{h}_modele"], preds[f"rendement_{h}_reel"] = p, y
        if h <= 20:
            lignes.append(evaluer(y, p, bench, h, "sans_passage", d[f"passage_dans_{h}"] == 0))
        else:
            yn = (np.exp(r_neutre.shift(-h) - r_neutre) - 1).where(close.shift(-h).notna())
            pn, _ = predire(X, yn, boosting, False, DEBUT, FIN, h)
            bn = {"marche_aleatoire": pd.Series(0.0, index=d.index), "moyenne_passee": moyenne_passee(yn, h)}
            lignes.append(evaluer(yn, pn, bn, h, "sans_sauts"))
        print(f"h={h} fait, {(time.time() - t0) / 60:.0f} min", flush=True)
    t = pd.DataFrame(lignes)
    t.to_csv(OUT / "regression_rendements.csv", index=False)
    pd.DataFrame(preds).to_parquet(OUT / "regression_predictions.parquet")
    pd.set_option("display.width", 220, "display.max_columns", None)
    print(t[["horizon", "lecture", "benchmark", "rmse_modele_2010-2026", "rmse_benchmark_2010-2026", "ecart_rmse", "ic_bas",
             "ic_haut", "bat_benchmark", "signe_correct_modele", "rmse_modele_2024-2026", "rmse_benchmark_2024-2026"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
