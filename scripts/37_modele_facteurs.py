"""Phase 3 et 4 : modele a facteurs, selon protocole.md valide le 2026-11-07.

Pour chacune des 9 comparaisons (sens a 1, 5, 20, 60, 120 seances ; volatilite a 5, 20, 60,
120), en validation annuelle 2010-2026, purge egale a l'horizon :
- Gradient Boosting (modele principal) et Random Forest (controle), reglages figes ;
- comparaison au meilleur benchmark sans facteurs (scripts/30_benchmark.py), sur 2010-2026
  et en lecture de controle, intervalle bootstrap a 99,4 % par blocs de max(20, h) seances ;
- retrait d'une famille a la fois (mesure principale), Gradient Boosting, cible brute ;
- SHAP absolu moyen par variable et par famille (mesure secondaire), avant et depuis 2024.

Lecture de controle : sans fenetres de passage d'echeance jusqu'a 20 seances ; cible sans
sauts a 60 et 120 seances pour le sens. Pour la volatilite a 60 et 120 seances, le protocole
ne definit pas de lecture de controle : seule la lecture brute existe, signale en sortie.

Sorties dans outputs/metriques/ : modele_horizons.csv, modele_predictions.parquet,
retrait_familles.csv, shap_variables.csv, shap_familles.csv

Usage : PYTHONPATH=src .venv/Scripts/python.exe -u scripts/37_modele_facteurs.py
"""
import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.metrics import roc_auc_score

from cacao.evaluation import GRAINE, boosting, ecart_bootstrap, foret, predire, score
from cacao.variables import construire

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/metriques"
DEBUT, FIN = 2010, 2026
HORIZONS = [1, 5, 20, 60, 120]
HORIZONS_VOL = [5, 20, 60, 120]
NIVEAU = 1 - 0.05 / 9
TIRAGES = 1000
PERIODES = {"2010-2026": (2010, 2026), "2010-2023": (2010, 2023), "2024-2026": (2024, 2026)}
SHAP_LIGNES = 500

spec = importlib.util.spec_from_file_location("bench", ROOT / "scripts/30_benchmark.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


def periode(s: pd.Series, a: int, b: int) -> pd.Series:
    return s[(s.index.year >= a) & (s.index.year <= b)]


def meilleur_benchmark(y: pd.Series, candidats: dict[str, pd.Series], classification: bool) -> tuple[str, pd.Series]:
    """Meilleur modele sans facteurs sur 2010-2026, comme dans le tableau du protocole."""
    notes = {k: score(periode(y, DEBUT, FIN), periode(v, DEBUT, FIN), classification) for k, v in candidats.items()}
    nom = max(notes, key=notes.get)
    return nom, candidats[nom]


def benchmark_sens(d: pd.DataFrame, h: int, y: pd.Series) -> dict[str, pd.Series]:
    p = bench.predictions(d, h, y)
    return {m: p[m].reindex(d.index) for m in bench.MODELES}


def benchmark_vol(d: pd.DataFrame, h: int) -> dict[str, pd.Series]:
    y = d[f"cible_vol_{h}"]
    r = np.log(d["cacao_close"]).diff()
    moyenne = pd.Series(index=d.index, dtype=float)
    for a in range(DEBUT, FIN + 1):
        test = d.index[d.index.year == a]
        if len(test):
            moyenne.loc[test] = y.iloc[:d.index.get_loc(test[0]) - h].mean()
    return {"persistance": r.rolling(h).std() * np.sqrt(252), "moyenne_passee": moyenne}


def comparer(y, preds, ref_nom, ref, classification, h, cible, lecture, masque=None) -> list[dict]:
    """Scores par periode et ecart au benchmark avec intervalle, pour chaque modele."""
    if masque is not None:
        y = y[masque.reindex(y.index).fillna(False).astype(bool)]
    lignes = []
    for nom, p in preds.items():
        commun = y.dropna().index.intersection(p.dropna().index).intersection(ref.dropna().index)
        commun = commun[(commun.year >= DEBUT) & (commun.year <= FIN)]
        yy, pp, rr = y[commun], p[commun], ref[commun]
        ecart, bas, haut = ecart_bootstrap(yy, pp, rr, classification, bloc=max(20, h), tirages=TIRAGES, niveau=NIVEAU)
        ligne = {"cible": cible, "horizon": h, "lecture": lecture, "modele": nom, "benchmark": ref_nom,
                 "n": len(commun), "fenetres_independantes": len(commun) // h, "ecart": ecart,
                 "ic_bas": bas, "ic_haut": haut, "bat_benchmark": bool(bas > 0)}
        for per, (a, b) in PERIODES.items():
            ya, pa, ra = periode(yy, a, b), periode(pp, a, b), periode(rr, a, b)
            ligne[f"score_{per}"] = score(ya, pa, classification) if len(ya) else np.nan
            ligne[f"benchmark_{per}"] = score(ya, ra, classification) if len(ya) else np.nan
            if classification and len(ya) and ya.nunique() == 2:
                ligne[f"auc_{per}"] = roc_auc_score(ya.astype(int), pa)
        lignes.append(ligne)
    return lignes


def shap_par_variable(modeles: list, X: pd.DataFrame) -> pd.DataFrame:
    alea = np.random.default_rng(GRAINE)
    res = {}
    for m, test, cols in modeles:
        i = alea.choice(test, min(SHAP_LIGNES, len(test)), replace=False)
        v = shap.TreeExplainer(m).shap_values(X.iloc[i][cols])
        v = v[1] if isinstance(v, list) else v
        # Variable absente d'un pli (encore vide) : contribution nulle cette annee-la.
        res[int(X.index[test[0]].year)] = pd.Series(np.abs(v).mean(axis=0), index=cols).reindex(X.columns, fill_value=0.0)
    return pd.DataFrame(res).T


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    t0 = time.time()
    comparaisons, retraits, shaps, predictions, carte = [], [], [], {}, {}
    taches = [("sens", h) for h in HORIZONS] + [("vol", h) for h in HORIZONS_VOL]
    for cible, h in taches:
        X, familles = construire(d, h)
        carte.update({(cible, h, v): f for f, cols in familles.items() for v in cols})
        interdit = [c for c in X if c.startswith(("cible_", "passage_dans", "saut_echeance", "ROBUSTESSE_", "GEFS_"))]
        if interdit:
            raise ValueError(f"Colonnes interdites dans X : {interdit}")
        classification = cible == "sens"
        y = d[f"cible_hausse_{h}"] if classification else d[f"cible_vol_{h}"]
        preds, modeles_gb = {}, None
        for nom, fab in (("gradient_boosting", boosting), ("random_forest", foret)):
            p, m = predire(X, y, fab, classification, DEBUT, FIN, h)
            preds[nom] = p
            if nom == "gradient_boosting":
                modeles_gb = m
            predictions[f"{cible}_{h}_brute_{nom}"] = p
        cand = benchmark_sens(d, h, y) if classification else benchmark_vol(d, h)
        ref_nom, ref = meilleur_benchmark(y, cand, classification)
        predictions[f"{cible}_{h}_brute_benchmark"] = ref
        comparaisons += comparer(y, preds, ref_nom, ref, classification, h, cible, "brute")

        if h <= 20:
            masque = d[f"passage_dans_{h}"] == 0
            if classification:
                cand_c = {k: v.where(masque) for k, v in cand.items()}
                ref_nom_c, ref_c = meilleur_benchmark(y.where(masque), cand_c, classification)
            else:
                ref_nom_c, ref_c = meilleur_benchmark(y.where(masque), cand, classification)
            comparaisons += comparer(y, preds, ref_nom_c, ref_c, classification, h, cible, "sans_passage", masque)
        elif classification:
            yn = d[f"cible_hausse_neutre_{h}"]
            pn = {nom: predire(X, yn, fab, True, DEBUT, FIN, h)[0]
                  for nom, fab in (("gradient_boosting", boosting), ("random_forest", foret))}
            ref_nom_n, ref_n = meilleur_benchmark(yn, benchmark_sens(d, h, yn), True)
            for nom, p in pn.items():
                predictions[f"{cible}_{h}_sans_sauts_{nom}"] = p
            comparaisons += comparer(yn, pn, ref_nom_n, ref_n, True, h, cible, "sans_sauts")
        print(f"{cible} h={h} : modeles faits, {(time.time() - t0) / 60:.0f} min", flush=True)

        s = shap_par_variable(modeles_gb, X)
        s.index.name = "annee"
        shaps.append(s.reset_index().melt(id_vars="annee", var_name="variable", value_name="shap")
                     .assign(cible=cible, horizon=h))

        base = preds["gradient_boosting"]
        for fam, colonnes in familles.items():
            p, _ = predire(X.drop(columns=colonnes), y, boosting, classification, DEBUT, FIN, h)
            commun = y.dropna().index.intersection(base.dropna().index).intersection(p.dropna().index)
            perte, bas, haut = ecart_bootstrap(y[commun], base[commun], p[commun], classification,
                                               bloc=max(20, h), tirages=TIRAGES, niveau=NIVEAU)
            ligne = {"cible": cible, "horizon": h, "famille": fam, "n_variables": len(colonnes),
                     "perte": perte, "ic_bas": bas, "ic_haut": haut}
            for per, (a, b) in PERIODES.items():
                ya = periode(y[commun], a, b)
                ligne[f"perte_{per}"] = score(ya, base[ya.index], classification) - score(ya, p[ya.index], classification)
            retraits.append(ligne)
        print(f"{cible} h={h} : retraits faits, {(time.time() - t0) / 60:.0f} min", flush=True)

        pd.DataFrame(comparaisons).to_csv(OUT / "modele_horizons.csv", index=False)
        pd.DataFrame(retraits).to_csv(OUT / "retrait_familles.csv", index=False)
        sv = pd.concat(shaps)
        sv.to_csv(OUT / "shap_variables.csv", index=False)
        pd.DataFrame(predictions).to_parquet(OUT / "modele_predictions.parquet")

    sv = pd.concat(shaps)
    sv["famille"] = [carte[(c, h, v)] for c, h, v in zip(sv["cible"], sv["horizon"], sv["variable"])]
    sv["periode"] = np.where(sv["annee"] >= 2024, "2024-2026", "2010-2023")
    sf = sv.groupby(["cible", "horizon", "periode", "famille", "annee"])["shap"].sum().groupby(
        ["cible", "horizon", "periode", "famille"]).mean().reset_index()
    sf["part"] = sf["shap"] / sf.groupby(["cible", "horizon", "periode"])["shap"].transform("sum")
    sf.to_csv(OUT / "shap_familles.csv", index=False)
    sv.to_csv(OUT / "shap_variables.csv", index=False)

    c = pd.DataFrame(comparaisons)
    print("\nModele principal face au benchmark (2010-2026) :")
    print(c[c["modele"] == "gradient_boosting"][["cible", "horizon", "lecture", "benchmark", "score_2010-2026",
                                                "benchmark_2010-2026", "ic_bas", "ic_haut", "bat_benchmark"]].round(4).to_string(index=False))
    print(f"\nDuree totale : {(time.time() - t0) / 60:.0f} min")


if __name__ == "__main__":
    main()
