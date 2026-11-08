"""Controles de la grille : pas de look-ahead, cibles correctes, source respectee."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.grille import cibles_sans_sauts as _sans_sauts


def test_cible_sans_saut_retire_le_saut_seulement():
    i = pd.bdate_range("2020-01-01", periods=6)
    close = pd.Series([100.0, 101.0, 80.0, 81.0, 82.0, 83.0], index=i)
    saut = pd.Series([False, False, True, False, False, False], index=i)
    c = _sans_sauts(close, saut, [2])["cible_hausse_neutre_2"]
    assert c.iloc[0] == 1.0  # la baisse de 21 % est un saut : seule la hausse de 1 % compte
    assert c.iloc[-2:].isna().all()
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cacao.grille import aligner, cibles, passage_dans_horizon  # noqa: E402

GRILLE = ROOT / "data/processed/grille_quotidienne_t1.parquet"


def test_aligner_ignore_le_jour_meme_et_le_futur():
    axe = pd.to_datetime(["2020-01-06", "2020-01-07", "2020-01-08"])
    s = pd.Series([1.0, 2.0, 3.0], index=axe, name="x")
    res = aligner(axe, s)
    assert np.isnan(res.iloc[0])
    assert res.iloc[1] == 1.0
    assert res.iloc[2] == 2.0


def test_modifier_le_futur_ne_change_pas_le_passe():
    axe = pd.bdate_range("2020-01-01", periods=30)
    s = pd.Series(np.arange(30.0), index=axe, name="x")
    avant = aligner(axe, s)
    s2 = s.copy()
    s2.iloc[20:] = 999.0
    apres = aligner(axe, s2)
    pd.testing.assert_series_equal(avant.iloc[:21], apres.iloc[:21])


def test_aligner_ne_remplit_pas_avant_le_debut():
    axe = pd.bdate_range("2020-01-01", periods=5)
    s = pd.Series([5.0], index=[axe[2]], name="x")
    assert aligner(axe, s).iloc[:3].isna().all()


def test_aligner_refuse_une_valeur_trop_ancienne():
    axe = pd.to_datetime(["2020-01-01", "2020-02-15"])
    s = pd.Series([1.0], index=[pd.Timestamp("2020-01-01")], name="x")
    assert np.isnan(aligner(axe, s).iloc[1])


def test_cibles_utilisent_le_bon_horizon():
    axe = pd.bdate_range("2020-01-01", periods=6)
    close = pd.Series([100.0, 110, 105, 120, 90, 95], index=axe)
    c = cibles(close, [1, 2])
    assert c["cible_hausse_1"].iloc[0] == 1
    assert c["cible_hausse_1"].iloc[1] == 0
    assert c["cible_hausse_2"].iloc[3] == 0
    assert c["cible_rendement_2"].iloc[0] == pytest.approx(np.log(105 / 100))
    assert c["cible_hausse_1"].iloc[-1:].isna().all()
    assert c["cible_hausse_2"].iloc[-2:].isna().all()


def test_ecart_tendance_ne_regarde_pas_le_futur():
    from cacao.grille import cibles_ecart, ecart_tendance
    axe = pd.bdate_range("2020-01-01", periods=60)
    close = pd.Series(100 + np.sin(np.arange(60.0)) * 5, index=axe)
    futur = close.copy()
    futur.iloc[40:] = 500.0
    pd.testing.assert_series_equal(ecart_tendance(close, 10).iloc[:40], ecart_tendance(futur, 10).iloc[:40])
    saut = pd.Series(False, index=axe)
    c = cibles_ecart(close, saut, [5], n=10)
    attendu = ecart_tendance(close, 10).shift(-5) - ecart_tendance(close, 10)
    pd.testing.assert_series_equal(c["cible_ecart_5"], attendu, check_names=False)
    assert c["cible_ecart_5"].iloc[-5:].isna().all()
    pd.testing.assert_series_equal(c["cible_ecart_5"], c["cible_ecart_neutre_5"], check_names=False)


def test_passage_regarde_seulement_les_seances_futures():
    saut = pd.Series([False, False, False, True, False, False])
    res = passage_dans_horizon(saut, 2)
    assert res.tolist() == [0, 1, 1, 0, 0, 0]


@pytest.fixture(scope="module")
def grille():
    return pd.read_parquet(GRILLE)


def test_axe_egal_aux_seances_cacao(grille):
    cc = pd.read_csv(ROOT / "data/raw/t1_marches/CC_F.csv", index_col="date", parse_dates=True)
    assert grille.index.equals(cc.index)
    assert grille.index.is_unique and grille.index.is_monotonic_increasing
    assert grille["cacao_close"].equals(cc["Close"])


def test_grille_contre_la_source_brute(grille):
    brut = pd.read_csv(ROOT / "data/raw/t1_marches/HSY.csv", index_col="date", parse_dates=True)["Adj Close"]
    for d in grille.index[[500, 2500, 5000]]:
        attendu = brut[brut.index < d].iloc[-1]
        assert grille.loc[d, "hsy"] == pytest.approx(attendu)


def test_aucune_correlation_parfaite_avec_le_futur(grille):
    """Une variable identique a la cible future trahirait une fuite."""
    variables = [c for c in grille.columns if c not in ("cacao_close", "cacao_volume")
                 and not c.startswith(("cible", "passage"))]
    futur = grille["cacao_close"].shift(-1)
    assert grille[variables].corrwith(futur).abs().max() < 0.999


def test_erreur_connue_retiree_du_change(grille):
    assert grille.loc["2015-07-20":"2015-08-10", "ngn_x"].min() > 100
    assert grille.loc["2020-03-25":"2020-04-10", "ghs_x"].max() < 10
