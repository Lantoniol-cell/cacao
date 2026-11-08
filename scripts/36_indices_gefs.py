"""Thematique 2 : indices de prevision GEFS corriges, valides par l'utilisatrice le 2026-11-08.

Regles :
1. Periode 2020-01-01 a 2020-09-22 ecartee : ancien GEFS, autre modele, 9 mois seulement.
2. Jours d'echeance 2 a 10. La prevision emise a 00 UTC le jour E n'est utilisee qu'a partir
   de la seance E+1, dont elle couvre les jours 2 (E+1) a 10. Le jour 1 est alors passe.
3. Echeance manquante dans une prevision : interpolation lineaire entre les jours d'echeance
   voisins de la meme emission, deja connus a la meme heure, donc sans look-ahead.
   Date d'emission manquante : derniere prevision connue reprise (ffill) a l'alignement,
   3 jours au plus. Pas d'interpolation entre deux dates d'emission : la suivante est future.
4. Correction de niveau par pays et par regime, avec le passe seulement :
   - pluie : rapport multiplicatif cumule CHIRPS / GEFS sur les mois deja publies par CHIRPS
     (le 25 du mois suivant), depuis le debut du regime ;
   - Tmax : ecart additif cumule NASA T2M_MAX - GEFS, mois publies (fin de mois + 3 jours).
   Au moins 3 mois du meme regime, sinon vide. Le rapport ne traverse jamais un changement
   de regime.
5. Puis ecart a la normale passee du meme mois (anomalie_passee), comme ERA5.

Le monde est la moyenne des pays ponderee par les parts FAOSTAT de l'annee N-2.

Sortie : data/processed/gefs_pays.parquet, indexe par date d'emission

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/36_indices_gefs.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.meteo import aligner_disponible, anomalie_passee

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
REGIMES = {"reprevision": ("2005-01-01", "2019-12-31"), "nouveau": ("2020-09-23", "2100-01-01")}
ECARTEE = ("2020-01-01", "2020-09-22")
FENETRES = {"5J": slice(1, 6), "9J": slice(1, 10)}  # indices 1 a 5 = jours 2 a 6 ; 1 a 9 = jours 2 a 10
MIN_MOIS = 3
SANS_LIMITE = 100_000
JUSQUA = next((a.split("=")[1] for a in sys.argv if a.startswith("--jusqua=")), None)


def dispo_chirps(m: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=24)


def dispo_nasa(m: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return m + pd.offsets.MonthEnd(0) + pd.Timedelta(days=3)


def charger(dossier: str) -> tuple[pd.DatetimeIndex, np.ndarray]:
    d = BASE / dossier
    ordre = (d / "points.txt").read_text(encoding="utf-8").split()
    attendu = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")["id"].tolist()
    if ordre != attendu:
        raise ValueError(f"Ordre des points different dans {dossier}")
    fichiers = sorted(d.glob("*.npy"))
    return pd.to_datetime([f.stem for f in fichiers], format="%Y%m%d"), np.stack([np.load(f) for f in fichiers])


def boucher_echeances(a: np.ndarray) -> np.ndarray:
    """Interpolation lineaire le long des jours d'echeance d'une meme emission."""
    a = a.copy()
    trous = np.argwhere(np.isnan(a).any(axis=2))
    for e, j in trous:
        x = np.arange(a.shape[1])
        for p in np.where(np.isnan(a[e, j]))[0]:
            v = a[e, :, p]
            ok = ~np.isnan(v)
            a[e, :, p] = np.interp(x, x[ok], v[ok])
    return a


def par_pays(table: pd.DataFrame, poids: pd.Series) -> pd.DataFrame:
    p = poids[table.columns]
    pays = pd.Index([c[:3] for c in table.columns])
    return table.mul(p).T.groupby(pays).sum(min_count=1).T / table.notna().mul(p).T.groupby(pays).sum().T


def correction(gefs_jour: pd.DataFrame, ref_mois: pd.DataFrame, dispo_mois: pd.Series, mode: str) -> pd.DataFrame:
    """Facteur (pluie) ou ecart (Tmax) cumule depuis le debut du regime, connu a chaque emission."""
    sortie = pd.DataFrame(index=gefs_jour.index, columns=gefs_jour.columns, dtype=float)
    for debut, fin in REGIMES.values():
        g = gefs_jour.loc[debut:fin]
        if g.empty:
            continue
        compte = g.notna().resample("MS").sum()
        gm = g.resample("MS").mean().where(compte >= compte.index.days_in_month.to_numpy()[:, None])
        r = ref_mois.reindex(gm.index)
        ok = gm.notna() & r.notna()
        if mode == "rapport":  # pluie en mm par jour face a CHIRPS en mm par mois
            num = r.where(ok).cumsum()
            den = (gm * gm.index.days_in_month.to_numpy()[:, None]).where(ok).cumsum()
            facteur = num / den
        else:
            facteur = (r - gm).where(ok).cumsum() / ok.cumsum()
        facteur = facteur.where(ok.cumsum() >= MIN_MOIS)
        dispo = dispo_mois(gm.index)
        for c in g.columns:
            sortie.loc[g.index, c] = aligner_disponible(g.index, facteur[c], pd.Series(dispo), SANS_LIMITE).to_numpy()
    return sortie


def monde(nat: pd.DataFrame, part: pd.DataFrame) -> pd.Series:
    w = part[nat.columns].reindex(nat.index.year)
    w.index = nat.index
    return (nat * w).sum(axis=1, min_count=len(nat.columns)) / w.sum(axis=1)


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    part = pd.read_csv(ROOT / "outputs/metriques/t2_poids_pays.csv", index_col=0)
    ids = points.index

    dates, pluie = charger("gefs")
    dt, tmax = charger("gefs_tmax")
    if not dates.equals(dt):
        raise ValueError("Dates pluie et Tmax differentes")
    garde = ~((dates >= ECARTEE[0]) & (dates <= ECARTEE[1]))
    if JUSQUA:
        garde &= dates <= JUSQUA
    dates, pluie, tmax = dates[garde], pluie[garde], tmax[garde] - 273.15
    print(f"{len(dates)} emissions gardees ; echeances vides avant bouchage : pluie {int(np.isnan(pluie).sum())}, "
          f"Tmax {int(np.isnan(tmax).sum())}")
    pluie, tmax = boucher_echeances(pluie), boucher_echeances(tmax)

    chirps = pd.concat({i: pd.read_csv(BASE / f"chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"]
                        for i in ids}, axis=1).dropna(axis=1, how="all")
    chirps = par_pays(chirps, points["poids"])
    nasa = pd.concat({i: pd.read_csv(BASE / f"power/{i}.csv", index_col="date", parse_dates=True)["T2M_MAX"]
                      for i in ids}, axis=1)
    nasa = par_pays(nasa.where(nasa > -900), points["poids"])
    if JUSQUA:  # les sources sont coupees a leur date de publication, pas a leur date de mesure
        fin = pd.Timestamp(JUSQUA)
        chirps = chirps[dispo_chirps(chirps.index) < fin]
        nasa = nasa.loc[: fin - pd.Timedelta(days=3)]
    compte = nasa.notna().resample("MS").sum()
    nasa_mois = nasa.resample("MS").mean().where(compte >= compte.index.days_in_month.to_numpy()[:, None])

    res = {}
    for nom, s in FENETRES.items():
        n = s.stop - s.start
        p = par_pays(pd.DataFrame(pluie[:, s, :].sum(axis=1), index=dates, columns=ids), points["poids"])
        t = par_pays(pd.DataFrame(tmax[:, s, :].mean(axis=1), index=dates, columns=ids), points["poids"])
        fp = correction(p / n, chirps, dispo_chirps, "rapport")
        ft = correction(t, nasa_mois, dispo_nasa, "ecart")
        pc, tc = p * fp, t + ft
        pc["MONDE"], tc["MONDE"] = monde(pc, part), monde(tc, part)
        for c in pc:
            res[f"GEFS_PLUIE{nom}_ANOM_{c}"] = anomalie_passee(pc[c])
            res[f"GEFS_TMAX{nom}_ANOM_{c}"] = anomalie_passee(tc[c])
        if nom == "9J":
            print("Facteur pluie en fin de regime (CIV, GHA) :",
                  {r: fp.loc[:f, ["CIV", "GHA"]].dropna().iloc[-1].round(2).to_dict() for r, (_, f) in REGIMES.items()})
            print("Ecart Tmax en fin de regime (CIV, GHA) :",
                  {r: ft.loc[:f, ["CIV", "GHA"]].dropna().iloc[-1].round(2).to_dict() for r, (_, f) in REGIMES.items()})
    out = pd.DataFrame(res).sort_index(axis=1)
    if JUSQUA:  # test de troncature : rien apres cette date ne doit changer le passe
        out.to_parquet(ROOT / f"outputs/metriques/gefs_tronque_{JUSQUA}.parquet")
        return
    out.to_parquet(ROOT / "data/processed/gefs_pays.parquet")
    print(f"Sortie {out.shape}, {out.index.min().date()} -> {out.index.max().date()}")
    print("Premiere valeur par regime :",
          {r: out.loc[d:f, "GEFS_PLUIE9J_ANOM_CIV"].first_valid_index().date() for r, (d, f) in REGIMES.items()})
    print(out.filter(like="MONDE").describe().round(2).to_string())


if __name__ == "__main__":
    main()
