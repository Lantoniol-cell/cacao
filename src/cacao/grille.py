"""Grille quotidienne : nettoyage du change, alignement sans look-ahead, cibles."""
import numpy as np
import pandas as pd

SEUIL_LOG = 0.15          # environ 16 % en un jour
TOLERANCE_RETOUR = 0.5    # le lendemain annule au moins la moitie du saut
ANCIENNETE_MAX_JOURS = 10 # au-dela, la valeur est trop vieille : NaN


def erreurs_de_cotation(close: pd.Series) -> pd.Series:
    """Repere les allers-retours sur un jour. Reserve au change.

    Sur les matieres premieres et les taux, ce filtre signale de vrais mouvements.
    """
    r = np.log(close.where(close > 0)).diff()
    suivant = r.shift(-1)
    return (r.abs() > SEUIL_LOG) & (np.sign(suivant) == -np.sign(r)) \
        & (suivant.abs() >= TOLERANCE_RETOUR * r.abs())


def aligner(axe: pd.DatetimeIndex, serie: pd.Series) -> pd.Series:
    """Pour chaque date de l'axe, prend la derniere valeur strictement anterieure.

    La regle stricte evite d'utiliser une cloture posterieure a celle du cacao.
    Un trou est donc comble par la derniere valeur connue, jamais par une valeur
    future. Rien n'est propage avant la premiere observation de la serie.
    """
    source = pd.DataFrame({"date_source": serie.index, "valeur": serie.values}).dropna()
    gauche = pd.DataFrame({"date": axe})
    fusion = pd.merge_asof(
        gauche.astype({"date": "datetime64[ns]"}),
        source.astype({"date_source": "datetime64[ns]"}).sort_values("date_source"),
        left_on="date", right_on="date_source", direction="backward",
        allow_exact_matches=False, tolerance=pd.Timedelta(days=ANCIENNETE_MAX_JOURS),
    )
    return pd.Series(fusion["valeur"].values, index=axe, name=serie.name)


def cibles(close: pd.Series, horizons: list[int]) -> pd.DataFrame:
    """Calcule les cibles futures. Ces colonnes ne doivent jamais servir de variables."""
    r = np.log(close).diff()
    sortie = pd.DataFrame(index=close.index)
    for h in horizons:
        rendement = np.log(close.shift(-h) / close)
        sortie[f"cible_rendement_{h}"] = rendement
        sortie[f"cible_hausse_{h}"] = (rendement > 0).astype(float).where(rendement.notna())
        if h > 1:
            sortie[f"cible_vol_{h}"] = r.rolling(h).std().shift(-h) * np.sqrt(252)
    return sortie


def cibles_sans_sauts(close: pd.Series, saut: pd.Series, horizons: list[int]) -> pd.DataFrame:
    """Sens du rendement futur, jours de saut d'echeance mis a zero. Test de robustesse.

    Au-dela de 52 seances environ, presque toute fenetre contient un passage : exclure ces
    fenetres ne laisse plus rien, d'ou cette variante. Les sauts sont reperes apres coup.
    """
    r = np.log(close).diff().where(~saut, 0.0)
    cumul = r.fillna(0).cumsum()
    sortie = pd.DataFrame(index=close.index)
    for h in horizons:
        rendement = (cumul.shift(-h) - cumul).where(close.shift(-h).notna())
        sortie[f"cible_hausse_neutre_{h}"] = (rendement > 0).astype(float).where(rendement.notna())
    return sortie


def ecart_tendance(close: pd.Series, n: int = 120) -> pd.Series:
    """D_t = log(P_t) - log(moyenne mobile de n seances), connu a la cloture de t."""
    return np.log(close) - np.log(close.rolling(n, min_periods=n).mean())


def cibles_ecart(close: pd.Series, saut: pd.Series, horizons: list[int], n: int = 120) -> pd.DataFrame:
    """Variation future de l'ecart a la tendance, D_{t+h} - D_t, brute et sans sauts.

    Amendement du protocole, point 11 A. Ces colonnes ne doivent jamais servir de variables.
    Sans sauts : le prix est reconstruit avec les rendements des jours de saut mis a zero.
    """
    r = np.log(close).diff().where(~saut, 0.0)
    neutre = np.exp(r.fillna(0).cumsum()).where(close.notna())
    sortie = pd.DataFrame(index=close.index)
    for nom, prix in (("", close), ("neutre_", neutre)):
        d = ecart_tendance(prix, n)
        for h in horizons:
            v = d.shift(-h) - d
            sortie[f"cible_ecart_{nom}{h}"] = v
            sortie[f"cible_ecart_hausse_{nom}{h}"] = (v > 0).astype(float).where(v.notna())
    return sortie


def jours_de_saut(close: pd.Series, passages: pd.DatetimeIndex) -> pd.Series:
    """Marque, pour chaque passage d'echeance, le jour du plus grand mouvement."""
    r = np.log(close).diff().abs()
    marque = pd.Series(False, index=close.index)
    for d in passages:
        i = close.index.get_loc(d)
        marque.loc[r.iloc[i:i + 2].idxmax()] = True
    return marque


def passage_dans_horizon(saut: pd.Series, h: int) -> pd.Series:
    """Vrai si un saut d'echeance tombe entre t+1 et t+h."""
    return (saut.astype(float).rolling(h).sum().shift(-h) > 0).astype(int)
