"""Tableau de bord : indicateurs quotidiens calcules uniquement avec le passe.

- Prevision de volatilite : modele HAR, regression lineaire de la volatilite realisee
  future sur les volatilites passees a 5, 20 et 60 seances. C'est le meilleur
  previsionniste mesure dans le projet (scripts/39, piste B). Il est reestime chaque jour
  sur les seances dont la cible est deja connue.
- Ecart aux moyennes mobiles 60 et 120 seances : indicateur d'etat, pas une prevision.
- Regime : volatilite des 60 dernieres seances au-dessus du 80e centile de ses valeurs
  strictement passees (regle de la piste C). Etat observe, pas une prevision de crise.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

ANNUALISATION = np.sqrt(252)
FENETRES_HAR = (5, 20, 60)
CENTILE_REGIME = 0.8
MIN_HISTORIQUE = 252


def rendements(close: pd.Series) -> pd.Series:
    return np.log(close).diff()


def volatilites_passees(close: pd.Series) -> pd.DataFrame:
    r = rendements(close)
    return pd.DataFrame({f"vol{n}": r.rolling(n).std() * ANNUALISATION for n in FENETRES_HAR})


def prevision_har(close: pd.Series, h: int) -> dict:
    """Prevision de la volatilite annualisee des h prochaines seances, a la derniere date.

    L'apprentissage n'utilise que les dates t dont la cible (seances t+1 a t+h) est
    entierement observee : rien d'inconnu a la date de prevision.
    """
    Z = volatilites_passees(close)
    cible = rendements(close).rolling(h).std().shift(-h) * ANNUALISATION
    ok = Z.notna().all(axis=1) & cible.notna()
    m = LinearRegression().fit(Z[ok], cible[ok])
    derniere = Z.iloc[[-1]]
    if derniere.isna().any(axis=None):
        raise ValueError("Historique trop court pour le HAR")
    ajuste = m.predict(Z[ok])
    recente = rendements(close).rolling(h).std().iloc[-1] * ANNUALISATION  # volatilite des h dernieres seances
    return {"horizon": h, "prevision": float(m.predict(derniere)[0]), "vol_recente": float(recente),
            "rmse_apprentissage": float(np.sqrt(((cible[ok] - ajuste) ** 2).mean())),
            "n": int(ok.sum()), "coefficients": dict(zip(Z.columns, np.round(m.coef_, 3)))}


def ecarts_moyennes(close: pd.Series) -> pd.DataFrame:
    """Ecart du cours a ses moyennes mobiles, en pourcentage."""
    return pd.DataFrame({f"mm{n}": close.rolling(n, min_periods=n).mean() for n in (60, 120)}
                        | {f"ecart_mm{n}_pct": (close / close.rolling(n, min_periods=n).mean() - 1) * 100 for n in (60, 120)})


def regime(close: pd.Series) -> pd.DataFrame:
    """Volatilite 60 seances, seuil du 80e centile de son passe strict, et regime (1 = agite)."""
    vol60 = rendements(close).rolling(60).std() * ANNUALISATION
    seuil = vol60.expanding(min_periods=MIN_HISTORIQUE).quantile(CENTILE_REGIME).shift(1)
    etat = pd.Series(np.where(seuil.isna(), np.nan, (vol60 > seuil).astype(float)), index=close.index)
    return pd.DataFrame({"vol60": vol60, "seuil": seuil, "agite": etat})
