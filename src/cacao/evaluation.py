"""Validation chronologique, retrait de familles et SHAP par famille."""
from collections.abc import Callable, Iterator

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import (HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, root_mean_squared_error
from sklearn.pipeline import make_pipeline

GRAINE = 42


def boosting(classification: bool):
    classe = HistGradientBoostingClassifier if classification else HistGradientBoostingRegressor
    return classe(max_iter=300, learning_rate=0.03, max_depth=3, min_samples_leaf=50, random_state=GRAINE)


def foret(classification: bool):
    classe = RandomForestClassifier if classification else RandomForestRegressor
    return make_pipeline(SimpleImputer(strategy="median"),
                         classe(n_estimators=500, min_samples_leaf=20, max_features="sqrt", n_jobs=-1, random_state=GRAINE))


def plis(index: pd.DatetimeIndex, debut: int, fin: int, h: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Par annee : entrainement sur le passe, moins h seances de purge."""
    for annee in range(debut, fin + 1):
        test = np.flatnonzero(index.year == annee)
        if len(test) and test[0] - h > 0:
            yield np.arange(test[0] - h), test


def predire(X: pd.DataFrame, y: pd.Series, fabrique: Callable, classification: bool,
            debut: int, fin: int, h: int) -> tuple[pd.Series, list]:
    """Predictions hors echantillon, et modeles avec leur periode de test et leurs colonnes.

    Une colonne entierement vide sur l'entrainement d'un pli (serie qui commence plus tard)
    est ignoree pour ce pli : elle ne porte encore aucune information.
    """
    sortie = pd.Series(index=X.index, dtype=float)
    modeles = []
    for train, test in plis(X.index, debut, fin, h):
        ok = train[y.iloc[train].notna().to_numpy()]
        cols = X.columns[X.iloc[ok].notna().any().to_numpy()]
        m = fabrique(classification).fit(X.iloc[ok][cols], y.iloc[ok].astype(int) if classification else y.iloc[ok])
        xt = X.iloc[test][cols]
        sortie.iloc[test] = m.predict_proba(xt)[:, 1] if classification else m.predict(xt)
        modeles.append((m, test, cols))
    return sortie, modeles


def score(y: pd.Series, p: pd.Series, classification: bool) -> float:
    """Plus grand = meilleur : exactitude equilibree, ou RMSE negatif."""
    i = y.notna() & p.notna()
    if classification:
        return float(balanced_accuracy_score(y[i].astype(int), (p[i] > 0.5).astype(int)))
    return -float(root_mean_squared_error(y[i], p[i]))


def retrait_familles(X: pd.DataFrame, y: pd.Series, familles: dict[str, list[str]], fabrique: Callable,
                     classification: bool, debut: int, fin: int, h: int) -> pd.Series:
    """Perte de score quand on retire chaque famille. Positif : la famille aide."""
    base = score(y, predire(X, y, fabrique, classification, debut, fin, h)[0], classification)
    pertes = {}
    for nom, colonnes in familles.items():
        p, _ = predire(X.drop(columns=colonnes), y, fabrique, classification, debut, fin, h)
        pertes[nom] = base - score(y, p, classification)
    return pd.Series(pertes).sort_values(ascending=False)


def shap_familles(modeles: list, X: pd.DataFrame, familles: dict[str, list[str]],
                  max_lignes: int = 500) -> pd.DataFrame:
    """SHAP absolu moyen par famille et par annee de test. Modeles boosting uniquement."""
    alea = np.random.default_rng(GRAINE)
    res = {}
    for m, test, cols in modeles:
        i = alea.choice(test, min(max_lignes, len(test)), replace=False)
        valeurs = shap.TreeExplainer(m).shap_values(X.iloc[i][cols])
        valeurs = valeurs[1] if isinstance(valeurs, list) else valeurs
        moyenne = pd.Series(np.abs(valeurs).mean(axis=0), index=cols).reindex(X.columns, fill_value=0.0)
        res[int(X.index[test[0]].year)] = {f: moyenne[c].sum() for f, c in familles.items()}
    return pd.DataFrame(res).T


def ecart_bootstrap(y: pd.Series, a: pd.Series, b: pd.Series, classification: bool,
                    bloc: int = 20, tirages: int = 1000, niveau: float = 0.95) -> tuple[float, float, float]:
    """Ecart de score a - b et son intervalle, par blocs de seances consecutives."""
    i = y.notna() & a.notna() & b.notna()
    y, a, b = y[i], a[i], b[i]
    alea = np.random.default_rng(GRAINE)
    n, ecarts = len(y), []
    for _ in range(tirages):
        departs = alea.integers(0, n - bloc + 1, n // bloc + 1)
        rang = np.concatenate([np.arange(d, d + bloc) for d in departs])[:n]
        ya, ab, bb = y.iloc[rang], a.iloc[rang], b.iloc[rang]
        ya.index = ab.index = bb.index = range(n)
        ecarts.append(score(ya, ab, classification) - score(ya, bb, classification))
    queue = (1 - niveau) / 2 * 100
    return score(y, a, classification) - score(y, b, classification), *np.percentile(ecarts, [queue, 100 - queue])
