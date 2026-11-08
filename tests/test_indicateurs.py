"""Le tableau de bord ne doit jamais utiliser d'information future."""
import numpy as np
import pandas as pd
import pytest

from cacao.indicateurs import ecarts_moyennes, prevision_har, regime
from cacao.marche import controler, fusionner


def prix(n=800, graine=0):
    alea = np.random.default_rng(graine)
    return pd.Series(1000 * np.exp(np.cumsum(alea.normal(0, 0.02, n))), index=pd.bdate_range("2020-01-01", periods=n))


def test_regime_et_ecarts_ignorent_le_futur():
    p = prix()
    futur = p.copy()
    futur.iloc[600:] *= 3
    pd.testing.assert_frame_equal(regime(p).iloc[:600], regime(futur).iloc[:600])
    pd.testing.assert_frame_equal(ecarts_moyennes(p).iloc[:600], ecarts_moyennes(futur).iloc[:600])


def test_har_coupe_a_une_date_n_utilise_que_le_passe():
    p = prix()
    a = prevision_har(p.iloc[:600], 20)
    futur = p.copy()
    futur.iloc[600:] *= np.exp(np.random.default_rng(1).normal(0, 0.2, 200)).cumprod()
    b = prevision_har(futur.iloc[:600], 20)
    assert a["prevision"] == pytest.approx(b["prevision"])
    assert a["n"] == 600 - 60 - 20  # 59 seances pour vol60 + 1 rendement manquant, 20 cibles inconnues


def test_regime_seuil_strictement_passe():
    p = prix()
    r = regime(p)
    i = 700
    attendu = r["vol60"].iloc[:i].dropna().quantile(0.8)
    assert r["seuil"].iloc[i] == pytest.approx(attendu)


def test_controle_et_fusion_des_cours():
    i = pd.bdate_range("2024-01-01", periods=3)
    a = pd.DataFrame({"Open": [1, 2, 3.0], "High": [2, 3, 4.0], "Low": [0.5, 1, 2.0], "Close": [1.5, 2.5, 3.5], "Volume": [1, 1, 0.0]}, index=i)
    assert controler(a) == []
    b = a.iloc[[2]].copy()
    b["Close"], b["Volume"] = 3.6, 10.0
    f = fusionner(a, b)
    assert len(f) == 3 and f["Close"].iloc[-1] == 3.6
    mauvais = a.copy()
    mauvais.loc[i[1], "High"] = 0.1
    assert controler(mauvais)
    reglement = a.copy()
    reglement.loc[i[1], "Close"] = 3.5  # reglement au-dessus du plus haut : signale, pas rejete
    assert controler(reglement) == []
