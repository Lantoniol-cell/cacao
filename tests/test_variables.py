"""Controle sans cible : les variables ne dependent pas du futur."""
from pathlib import Path

import pandas as pd
import pytest

from cacao.variables import construire

SOURCE = Path(__file__).resolve().parents[1] / "data/processed/dataset_quotidien.parquet"


@pytest.mark.skipif(not SOURCE.exists(), reason="dataset absent")
@pytest.mark.parametrize("h", [1, 20])
def test_troncature(h):
    d = pd.read_parquet(SOURCE)
    d = d[[c for c in d.columns if not c.startswith(("cible_", "passage_dans"))]]
    complet, _ = construire(d, h)
    coupe = "2018-06-29"
    tronque, _ = construire(d.loc[:coupe], h)
    pd.testing.assert_frame_equal(complet.loc[:coupe], tronque, check_freq=False)


@pytest.mark.skipif(not SOURCE.exists(), reason="dataset absent")
def test_familles_completes():
    d = pd.read_parquet(SOURCE)
    d = d[[c for c in d.columns if not c.startswith(("cible_", "passage_dans"))]]
    X, familles = construire(d, 20)
    assert all(len(v) > 0 for v in familles.values())
    colonnes = [c for v in familles.values() for c in v]
    assert sorted(colonnes) == sorted(X.columns)
    assert not any(c.startswith(("cible_", "passage_dans", "ROBUSTESSE", "saut")) for c in colonnes)
