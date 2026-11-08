"""Tunnel de volatilite hors echantillon a 20 seances (modele HAR), 2010-2026.

Pour chaque annee de test, le HAR (volatilite des 20 seances suivantes expliquee par les
volatilites passees a 5, 20 et 60 seances) est estime sur le passe, avec une purge de
20 seances, comme les autres modeles du projet. Pour chaque seance t :
    sigma_t = prevision HAR de la volatilite annualisee des 20 seances suivantes
    tunnel a +/- k ecarts-types pour le cours a t+20 : P_t * exp(+/- k * sigma_t * sqrt(20/252))
Le tunnel est date a t+20, la seance qu'il vise, pour etre compare au cours realise.

Couverture : part des seances ou le cours realise a t+20 tombe dans le tunnel. Attendu sous
une loi normale : environ 68 % a 1 ecart-type, 95 % a 2.

Sorties : outputs/metriques/tunnel_har20.parquet, outputs/metriques/tunnel_couverture.csv

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/43_tunnel_historique.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from cacao.evaluation import plis

ROOT = Path(__file__).resolve().parents[1]
H, DEBUT, FIN = 20, 2010, 2026
PERIODES = {"2010-2023": (2010, 2023), "2024-2026": (2024, 2026), "2010-2026": (2010, 2026)}


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    p = d["cacao_close"]
    r = np.log(p).diff()
    Z = pd.DataFrame({f"vol{n}": r.rolling(n).std() * np.sqrt(252) for n in (5, 20, 60)})
    y = d[f"cible_vol_{H}"]
    sigma = pd.Series(index=d.index, dtype=float)
    for train, test in plis(d.index, DEBUT, FIN, H):
        ok = train[(y.iloc[train].notna() & Z.iloc[train].notna().all(axis=1)).to_numpy()]
        t = test[Z.iloc[test].notna().all(axis=1).to_numpy()]
        sigma.iloc[t] = LinearRegression().fit(Z.iloc[ok], y.iloc[ok]).predict(Z.iloc[t])

    largeur = sigma * np.sqrt(H / 252)
    vise = p.shift(-H)
    t = pd.DataFrame({"date_vise": pd.Series(d.index, index=d.index).shift(-H), "cours_depart": p, "sigma_har": sigma,
                      "cours_realise": vise})
    for k in (1, 2):
        t[f"bas_{k}"] = p * np.exp(-k * largeur)
        t[f"haut_{k}"] = p * np.exp(k * largeur)
        t[f"dedans_{k}"] = ((vise >= t[f"bas_{k}"]) & (vise <= t[f"haut_{k}"])).astype(float).where(vise.notna() & sigma.notna())
    t = t.dropna(subset=["sigma_har"])
    t.to_parquet(ROOT / "outputs/metriques/tunnel_har20.parquet")

    lignes = []
    for nom, (a, b) in PERIODES.items():
        x = t[(t.index.year >= a) & (t.index.year <= b)].dropna(subset=["dedans_1"])
        lignes.append({"periode": nom, "n": len(x), "couverture_1_ecart_type": x["dedans_1"].mean(),
                       "couverture_2_ecarts_types": x["dedans_2"].mean(), "attendu_1": 0.683, "attendu_2": 0.954,
                       "largeur_moyenne_1_pct": (np.exp(x["sigma_har"] * np.sqrt(H / 252)) - 1).mean() * 100})
    c = pd.DataFrame(lignes)
    c.to_csv(ROOT / "outputs/metriques/tunnel_couverture.csv", index=False)
    print(c.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
