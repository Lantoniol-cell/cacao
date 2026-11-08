import numpy as np
import pandas as pd

from cacao.meteo import aligner_disponible, anomalie_passee, anomalie_reference


def test_aligner_respecte_le_delai():
    jours = pd.date_range("2020-01-01", "2020-01-31", freq="D")
    s = pd.Series(range(len(jours)), index=jours, dtype=float)
    axe = pd.DatetimeIndex(["2020-01-10", "2020-01-11"])
    a = aligner_disponible(axe, s, pd.Series(jours + pd.Timedelta(days=7)), 10)
    # Le 10, seule une valeur rendue disponible le 9 ou avant est permise : celle du 2.
    assert a.iloc[0] == 1
    assert a.iloc[1] == 2


def test_aligner_tolerance():
    jours = pd.DatetimeIndex(["2020-01-01"])
    s = pd.Series([1.0], index=jours)
    a = aligner_disponible(pd.DatetimeIndex(["2020-03-01"]), s, pd.Series(jours), 10)
    assert a.isna().all()


def serie():
    i = pd.date_range("2005-01-01", "2012-12-31", freq="D")
    return pd.Series(np.random.default_rng(42).gamma(2, 3, len(i)), index=i)


def test_premieres_annees_vides():
    a = anomalie_passee(serie())
    assert a.loc[:"2007-12-31"].isna().all()
    assert a.loc["2008-01-01":].notna().all()


def test_pas_de_look_ahead():
    s = serie()
    t = s.copy()
    t.loc["2011-01-01":] = t.loc["2011-01-01":] * 50 + 1000
    pd.testing.assert_series_equal(anomalie_passee(s).loc[:"2010-12-31"], anomalie_passee(t).loc[:"2010-12-31"])


def test_valeur_exacte():
    s = serie()
    jan = s[s.index.month == 1]
    passe = jan[jan.index.year < 2009]
    attendu = (s.loc["2009-01-15"] - passe.mean()) / passe.std(ddof=0)
    assert abs(anomalie_passee(s).loc["2009-01-15"] - attendu) < 1e-9


def test_reference_fixe_insensible_au_futur():
    i = pd.date_range("1991-01-01", "2010-12-01", freq="MS")
    s = pd.Series(np.random.default_rng(1).gamma(2, 50, len(i)), index=i)
    t = s.copy()
    t.loc["2005-01-01":] *= 10
    a, b = anomalie_reference(s, "1991", "2004"), anomalie_reference(t, "1991", "2004")
    pd.testing.assert_series_equal(a.loc[:"2004-12-01"], b.loc[:"2004-12-01"])
