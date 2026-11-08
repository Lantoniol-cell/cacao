"""Phase 2 : benchmark du cacao sans aucun facteur, par horizon, en validation chronologique.

Horizons 1, 5, 20, 60 et 120 seances. Pour chaque annee de test, l'entrainement s'arrete
h seances avant le debut de l'annee : la purge est egale a l'horizon.

Sens : majorite, persistance, momentum a 20 seances, logistique sur le passe du prix.
Volatilite : moyenne passee et persistance.
Trois lectures du sens : brute, sans fenetres de passage d'echeance (utile jusqu'a 20 seances),
et cible sans sauts d'echeance.

Sorties : outputs/metriques/benchmark.csv, outputs/metriques/benchmark_horizons.csv

Usage : .venv/Scripts/python.exe scripts/30_benchmark.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
HORIZONS = [1, 5, 20, 60, 120]
HORIZONS_VOL = [5, 20, 60, 120]
ANNEES = range(2010, 2027)
GRAINE = 42
PERIODES = {"2010-2023": (2010, 2023), "2024-2026": (2024, 2026), "2010-2026": (2010, 2026)}
MODELES = ("majorite", "persistance", "momentum", "logistique")
pd.set_option("display.width", 200, "display.max_columns", None)


def variables(close: pd.Series) -> pd.DataFrame:
    r = np.log(close).diff()
    return pd.DataFrame({f"r{n}": np.log(close / close.shift(n)) for n in (1, 5, 20, 60, 120)}
                        | {"vol20": r.rolling(20).std(), "vol60": r.rolling(60).std()})


def predictions(d: pd.DataFrame, h: int, y: pd.Series) -> pd.DataFrame:
    X = variables(d["cacao_close"])
    entree = X.drop(columns="r120")
    lignes = []
    for a in ANNEES:
        test = d.index[d.index.year == a]
        test = test[y.loc[test].notna()]
        if len(test) == 0:
            continue
        rang = d.index.get_loc(test[0])
        train = d.index[:rang - h]
        ok = train[entree.loc[train].notna().all(axis=1) & y.loc[train].notna()]
        modele = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=GRAINE))
        modele.fit(entree.loc[ok], y.loc[ok].astype(int))
        proba = pd.Series(modele.predict_proba(entree.loc[test].fillna(0))[:, 1], index=test)
        lignes.append(pd.DataFrame({
            "y": y.loc[test], "annee": a, "passage": d.loc[test, f"passage_dans_{h}"],
            "majorite": float(y.loc[ok].mean() > 0.5), "persistance": (X.loc[test, f"r{h}"] > 0).astype(float),
            "momentum": (X.loc[test, "r20"] > 0).astype(float),
            "logistique": (proba > 0.5).astype(float), "logistique_p": proba}))
    return pd.concat(lignes)


def scores(p: pd.DataFrame, h: int, lecture: str) -> list[dict]:
    res = []
    for nom, (a, b) in PERIODES.items():
        x = p[(p["annee"] >= a) & (p["annee"] <= b)]
        if x["y"].nunique() < 2:
            continue
        for m in MODELES:
            res.append({"cible": "sens", "horizon": h, "lecture": lecture, "periode": nom, "modele": m, "n": len(x),
                        "n_fenetres_independantes": len(x) // h, "exactitude": accuracy_score(x["y"], x[m]),
                        "exactitude_equilibree": balanced_accuracy_score(x["y"], x[m]),
                        "auc": roc_auc_score(x["y"], x["logistique_p"]) if m == "logistique" else np.nan})
    return res


def volatilite(d: pd.DataFrame, h: int) -> list[dict]:
    y = d[f"cible_vol_{h}"]
    r = np.log(d["cacao_close"]).diff()
    persistance = r.rolling(h).std() * np.sqrt(252)
    moyenne = pd.Series(index=d.index, dtype=float)
    for a in ANNEES:
        test = d.index[d.index.year == a]
        moyenne.loc[test] = y.iloc[:d.index.get_loc(test[0]) - h].mean()
    res = []
    for nom, (a, b) in PERIODES.items():
        i = d.index[(d.index.year >= a) & (d.index.year <= b) & y.notna()]
        for m, s in (("moyenne_passee", moyenne), ("persistance", persistance)):
            res.append({"cible": "vol", "horizon": h, "lecture": "brute", "periode": nom, "modele": m, "n": len(i),
                        "n_fenetres_independantes": len(i) // h,
                        "rmse": float(np.sqrt(((y[i] - s[i]) ** 2).mean())), "mae": float((y[i] - s[i]).abs().mean())})
    return res


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    res = []
    for h in HORIZONS:
        p = predictions(d, h, d[f"cible_hausse_{h}"])
        res += scores(p, h, "brute")
        res += scores(p[p["passage"] == 0], h, "sans_passage")
        res += scores(predictions(d, h, d[f"cible_hausse_neutre_{h}"]), h, "sans_sauts")
        print(f"h={h}, fenetres avec passage : {d[f'passage_dans_{h}'].mean():.1%}", flush=True)
    for h in HORIZONS_VOL:
        res += volatilite(d, h)
    t = pd.DataFrame(res)
    t.round(4).to_csv(ROOT / "outputs/metriques/benchmark.csv", index=False)

    s = t[(t["cible"] == "sens") & (t["periode"] == "2010-2026")]
    meilleur = s.groupby(["horizon", "lecture"])["exactitude_equilibree"].max().unstack().round(3)
    logistique = s[s["modele"] == "logistique"].pivot(index="horizon", columns="lecture", values="auc").round(3)
    print("\nMeilleure exactitude equilibree 2010-2026 :")
    print(meilleur[["brute", "sans_passage", "sans_sauts"]].to_string())
    print("\nAUC logistique 2010-2026 :")
    print(logistique[["brute", "sans_passage", "sans_sauts"]].to_string())
    print("\nFenetres independantes, lecture sans passage :")
    print(s[(s["modele"] == "logistique") & (s["lecture"] == "sans_passage")].set_index("horizon")[["n", "n_fenetres_independantes"]].to_string())
    v = t[t["cible"] == "vol"]
    print("\nVolatilite, RMSE :")
    print(v[v["modele"] == "persistance"].pivot(index="horizon", columns="periode", values="rmse")[list(PERIODES)].round(3).to_string())
    print(v[v["modele"] == "moyenne_passee"].pivot(index="horizon", columns="periode", values="rmse")[list(PERIODES)].round(3).to_string())
    t.pivot_table(index=["cible", "horizon", "lecture", "periode"], columns="modele",
                  values=["exactitude_equilibree", "rmse"]).round(4).to_csv(ROOT / "outputs/metriques/benchmark_horizons.csv")


if __name__ == "__main__":
    main()
