"""Tests sur des donnees factices : aucune donnee reelle n'est utilisee ici."""
import numpy as np
import pandas as pd
import pytest

from cacao.evaluation import (boosting, ecart_bootstrap, foret, plis, predire, retrait_familles,
                              score, shap_familles)

FAMILLES = {"utile": ["a1", "a2"], "bruit": ["b1", "b2"]}


def factice(signal=True, n=2200, graine=1):
    alea = np.random.default_rng(graine)
    i = pd.bdate_range("2008-01-01", periods=n)
    X = pd.DataFrame(alea.normal(size=(n, 4)), index=i, columns=["a1", "a2", "b1", "b2"])
    bruit = alea.normal(size=n)
    y = (X["a1"] * 2 + X["a2"] + bruit if signal else pd.Series(bruit, index=i))
    return X, y


def test_purge_entre_entrainement_et_test():
    i = pd.bdate_range("2008-01-01", periods=2200)
    tranches = list(plis(i, 2010, 2015, 20))
    assert len(tranches) >= 5
    for train, test in tranches:
        assert test[0] - train[-1] == 21
        assert i[train[-1]] < i[test[0]]


@pytest.mark.parametrize("h", [1, 5, 20, 60, 120])
def test_purge_egale_horizon(h):
    i = pd.bdate_range("2005-01-03", periods=5000)
    for train, test in plis(i, 2010, 2020, h):
        assert test[0] - train[-1] - 1 == h


def test_aucun_signal_sur_du_bruit():
    X, y = factice(signal=False)
    b = (y > 0).astype(float)
    p, _ = predire(X, b, boosting, True, 2010, 2015, 1)
    assert abs(score(b, p, True) - 0.5) < 0.05


def test_retrouve_la_bonne_famille():
    X, y = factice()
    pertes = retrait_familles(X, y, FAMILLES, boosting, False, 2010, 2013, 1)
    assert pertes.index[0] == "utile"
    assert pertes["utile"] > 0.2
    assert abs(pertes["bruit"]) < 0.1


def test_shap_par_famille():
    X, y = factice()
    _, modeles = predire(X, y, boosting, False, 2010, 2011, 1)
    s = shap_familles(modeles, X, FAMILLES, max_lignes=100)
    assert (s["utile"] > s["bruit"] * 5).all()


def test_shap_classification():
    X, y = factice()
    _, modeles = predire(X, (y > 0).astype(float), boosting, True, 2010, 2010, 1)
    s = shap_familles(modeles, X, FAMILLES, max_lignes=100)
    assert s.loc[2010, "utile"] > s.loc[2010, "bruit"]


def test_foret_gere_les_vides():
    X, y = factice(n=1000)
    X.iloc[::7, 0] = np.nan
    p, _ = predire(X, y, foret, False, 2010, 2010, 1)
    assert p.loc["2010"].notna().all()


def test_bootstrap_detecte_un_vrai_ecart():
    X, y = factice()
    bon = y + np.random.default_rng(2).normal(scale=0.1, size=len(y))
    mauvais = y + np.random.default_rng(3).normal(scale=2.0, size=len(y))
    e, bas, haut = ecart_bootstrap(y, bon, mauvais, False, tirages=200)
    assert e > 0 and bas > 0


def test_bootstrap_sans_ecart():
    X, y = factice()
    a = y + np.random.default_rng(2).normal(scale=1.0, size=len(y))
    b = y + np.random.default_rng(3).normal(scale=1.0, size=len(y))
    e, bas, haut = ecart_bootstrap(y, a, b, False, tirages=200)
    assert bas < 0 < haut


def test_look_ahead_detecte():
    """Le test doit voir une fuite : avec le futur, le score sur bruit explose."""
    X, y = factice(signal=False)
    b = (y > 0).astype(float)
    X["fuite"] = y
    p, _ = predire(X, b, boosting, True, 2010, 2011, 1)
    assert score(b, p, True) > 0.9
