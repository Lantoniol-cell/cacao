"""Essai de bout en bout avec les vraies variables et une cible aleatoire.

Mesure la duree et la forme des sorties. La cible est tiree au hasard : aucun resultat sur
le cacao n'est produit. Le score doit rester proche du hasard.

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/33_modele_factice.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.evaluation import boosting, predire, retrait_familles, score, shap_familles
from cacao.variables import construire

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    d = d[[c for c in d.columns if not c.startswith(("cible_", "passage_dans"))]]
    X, familles = construire(d, 20)
    print(f"Variables : {X.shape}, par famille : {({k: len(v) for k, v in familles.items()})}")
    print(f"Part de vides par famille : {({k: round(float(X[v].isna().mean().mean()), 3) for k, v in familles.items()})}")
    y = pd.Series(np.random.default_rng(42).integers(0, 2, len(X)).astype(float), index=X.index)
    t = time.time()
    p, modeles = predire(X, y, boosting, True, 2024, 2025, 20)
    print(f"Deux annees : {time.time() - t:.0f} s, score factice {score(y, p, True):.3f}")
    t = time.time()
    s = shap_familles(modeles, X, familles, max_lignes=100)
    print(f"SHAP : {time.time() - t:.0f} s, forme {s.shape}")
    t = time.time()
    pertes = retrait_familles(X, y, familles, boosting, True, 2025, 2025, 20)
    print(f"Retrait sur un an : {time.time() - t:.0f} s, {len(pertes)} familles")


if __name__ == "__main__":
    main()
