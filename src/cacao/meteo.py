"""Anomalies de pluie sans look-ahead."""
import pandas as pd

MIN_ANNEES = 3


def anomalie_passee(serie: pd.Series, min_annees: int = MIN_ANNEES) -> pd.Series:
    """Ecart a la normale du meme mois calendaire, en ecarts-types.

    La normale d'une annee n'utilise que les annees strictement anterieures. Tant qu'il
    y a moins de `min_annees` annees passees, le resultat est vide.
    """
    s = serie.dropna()
    res = pd.Series(index=serie.index, dtype=float)
    for mois in range(1, 13):
        m = s[s.index.month == mois]
        par_an = m.groupby(m.index.year)
        cumul = pd.DataFrame({"n": par_an.size(), "somme": par_an.sum(),
                              "carres": par_an.apply(lambda x: (x ** 2).sum())}).cumsum().shift(1)
        annees = pd.Index(m.index.year)
        n_annees = pd.Series(range(len(cumul)), index=cumul.index)
        c = cumul.reindex(annees)
        moyenne = c["somme"].to_numpy() / c["n"].to_numpy()
        variance = c["carres"].to_numpy() / c["n"].to_numpy() - moyenne ** 2
        z = (m.to_numpy() - moyenne) / pd.Series(variance).clip(lower=0).pow(0.5).replace(0, float("nan")).to_numpy()
        z = pd.Series(z, index=m.index).where(n_annees.reindex(annees).to_numpy() >= min_annees)
        res.loc[z.index] = z
    return res


def aligner_disponible(axe: pd.DatetimeIndex, serie: pd.Series, disponible_le: pd.Series,
                       tolerance_jours: int) -> pd.Series:
    """Pour chaque seance, prend la derniere valeur disponible strictement avant ce jour.

    Une valeur trop ancienne reste vide : aucune interpolation, aucun futur.
    """
    source = pd.DataFrame({"dispo": disponible_le.to_numpy(), "valeur": serie.to_numpy()}).dropna()
    gauche = pd.DataFrame({"date": axe}).astype({"date": "datetime64[ns]"})
    fusion = pd.merge_asof(gauche, source.astype({"dispo": "datetime64[ns]"}).sort_values("dispo"),
                           left_on="date", right_on="dispo", direction="backward",
                           allow_exact_matches=False, tolerance=pd.Timedelta(days=tolerance_jours))
    return pd.Series(fusion["valeur"].to_numpy(), index=axe, name=serie.name)


def anomalie_reference(serie: pd.Series, debut: str, fin: str) -> pd.Series:
    """Ecart a la normale du meme mois calendaire, calculee sur une periode fixe."""
    ref = serie.loc[debut:fin]
    moyenne = ref.groupby(ref.index.month).mean()
    ecart = ref.groupby(ref.index.month).std()
    return (serie - moyenne.reindex(serie.index.month).to_numpy()) / ecart.reindex(serie.index.month).to_numpy()
