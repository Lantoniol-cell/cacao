"""Analyses de la page Donnees : information statistique, climat saisonnier, qualite de CC=F.

1. Information statistique (niveau B) : correlation de rang entre chaque variable du modele
   (construire(d, h)) et la cible future (rendement ou volatilite a h seances), 2010-2026,
   intervalle par bootstrap par blocs de max(20, h) seances, controle du taux de fausses
   decouvertes (Benjamini-Hochberg, 5 %) par cible. C'est une association dans l'echantillon,
   pas une preuve de pouvoir predictif : celui-ci se mesure hors echantillon (scripts 37-39).
2. Climat : pluie mensuelle CHIRPS en mm pour la Cote d'Ivoire et le Ghana, normale 1991-2004
   (celle des anomalies du modele) et 1991-2020 (affichage), anomalie, saisons deduites de
   la climatologie. Profil de delai : correlation entre l'anomalie de pluie sur 3 mois
   publiee a la fin du mois m+1 et le rendement du cacao sur 3 mois commencant k mois plus
   tard, k de 0 a 12, intervalle par bootstrap par blocs de 12 mois.
3. CC=F : contrats individuels encore cotes sur Yahoo (les contrats expires n'y sont pas),
   rendements bruts et neutralises, valeurs extremes, comparaison mensuelle a la Banque
   mondiale, et consequences predictives pour la volatilite (persistance et HAR, cible brute
   contre cible sans sauts).

Sorties dans outputs/metriques/ : association_variables.csv, pluie_mensuelle_pays.csv,
climat_delais.csv, ccf_contrats.csv, ccf_rendements.parquet, ccf_resume.csv,
ccf_consequences.csv

Usage : PYTHONPATH=src .venv/Scripts/python.exe -u scripts/46_analyses_donnees.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from cacao.evaluation import plis
from cacao.variables import construire

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/metriques"
GRAINE, TIRAGES = 42, 200
DEBUT, FIN = 2010, 2026


def blocs(n: int, taille: int, alea) -> np.ndarray:
    departs = alea.integers(0, n - taille + 1, n // taille + 1)
    return np.concatenate([np.arange(s, s + taille) for s in departs])[:n]


def bh(p: pd.Series, q: float = 0.05) -> pd.Series:
    """Benjamini-Hochberg : vrai si la decouverte est retenue."""
    o = p.sort_values()
    seuil = q * np.arange(1, len(o) + 1) / len(o)
    ok = o.to_numpy() <= seuil
    k = np.max(np.nonzero(ok)[0]) + 1 if ok.any() else 0
    return pd.Series(np.arange(len(o)) < k, index=o.index).reindex(p.index)


def association(d: pd.DataFrame) -> pd.DataFrame:
    alea = np.random.default_rng(GRAINE)
    lignes = []
    for cible, h in [("rendement", h) for h in (1, 5, 20, 60, 120)] + [("vol", h) for h in (5, 20, 60, 120)]:
        X, fam = construire(d, h)
        y = d[f"cible_{'rendement' if cible == 'rendement' else 'vol'}_{h}"]
        i = (X.index.year >= DEBUT) & (X.index.year <= FIN) & y.notna().to_numpy()
        Xr, yr = X[i].rank(), y[i].rank()
        rho = Xr.corrwith(yr)
        tirages = []
        for _ in range(TIRAGES):
            k = blocs(len(yr), max(20, h), alea)
            tirages.append(Xr.iloc[k].reset_index(drop=True).corrwith(yr.iloc[k].reset_index(drop=True)))
        t = pd.DataFrame(tirages)
        # p-value par approximation normale avec l'ecart-type bootstrap : avec 200 tirages, la
        # p-value empirique ne descend pas sous 0,005, trop grossier pour Benjamini-Hochberg.
        from scipy.stats import norm
        p = pd.Series(2 * norm.sf(np.abs(rho / t.std())), index=rho.index)
        carte = {v: f for f, cols in fam.items() for v in cols}
        res = pd.DataFrame({"variable": rho.index, "famille": rho.index.map(carte), "cible": cible, "horizon": h, "rho": rho.values,
                            "ic_bas": t.quantile(0.025).values, "ic_haut": t.quantile(0.975).values, "p_bootstrap": p.values,
                            "n": int(i.sum())})
        res["retenue_fdr_5pct"] = bh(res.set_index("variable")["p_bootstrap"].dropna()).reindex(res["variable"]).fillna(False).to_numpy()
        lignes.append(res)
        print(f"association {cible} {h} : {int(res['retenue_fdr_5pct'].sum())}/{len(res)} retenues", flush=True)
    return pd.concat(lignes)


def pluie_pays(pays: str) -> pd.Series:
    p = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    ids = [i for i in p.index if i.startswith(pays)]
    t = pd.concat({i: pd.read_csv(ROOT / f"data/raw/t2_climat/chirps/{i}.csv", index_col="mois", parse_dates=True)["pluie"] for i in ids}, axis=1)
    w = p.loc[ids, "poids"]
    return ((t * w).sum(axis=1, min_count=1) / (t.notna() * w).sum(axis=1)).dropna()


SAISONS = {12: "Grande saison sèche", 1: "Grande saison sèche", 2: "Grande saison sèche", 11: "Grande saison sèche",
           3: "Grande saison des pluies", 4: "Grande saison des pluies", 5: "Grande saison des pluies", 6: "Grande saison des pluies",
           7: "Petite saison sèche", 8: "Petite saison sèche", 9: "Petite saison des pluies", 10: "Petite saison des pluies"}


def climat(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    lignes, delais = [], []
    prix = d["cacao_close"].resample("ME").last()
    alea = np.random.default_rng(GRAINE)
    for pays in ("CIV", "GHA"):
        s = pluie_pays(pays)
        m = s.index.month
        ref = s.loc["1991":"2004"]
        moy, sd = ref.groupby(ref.index.month).mean(), ref.groupby(ref.index.month).std()
        norm20 = s.loc["1991":"2020"].groupby(s.loc["1991":"2020"].index.month).mean()
        lignes.append(pd.DataFrame({"pays": pays, "mois": s.index, "pluie_mm": s.values, "normale_1991_2004_mm": moy.reindex(m).values,
                                    "normale_1991_2020_mm": norm20.reindex(m).values, "anomalie_ecarts_types": ((s - moy.reindex(m).values) / sd.reindex(m).values).values,
                                    "saison": [SAISONS[x] for x in m]}))
        # Profil de delai : anomalie 3 mois connue fin m+1, rendement sur 3 mois a partir de fin m+1+k.
        c3 = s.rolling(3).sum()
        r3 = c3.loc["1991":"2004"]
        z3 = (c3 - r3.groupby(r3.index.month).mean().reindex(c3.index.month).values) / r3.groupby(r3.index.month).std().reindex(c3.index.month).values
        z3.index = z3.index + pd.offsets.MonthEnd(0)
        z3 = z3.shift(1, freq="ME")  # date de disponibilite : fin du mois suivant
        for k in range(13):
            futur = np.log(prix.shift(-(k + 3)) / prix.shift(-k))
            x = pd.concat([z3.rename("z"), futur.rename("r")], axis=1).dropna().loc["2005":]
            rho = x["z"].corr(x["r"], method="spearman")
            boot = []
            for _ in range(500):
                i = blocs(len(x), 12, alea)
                boot.append(x.iloc[i]["z"].corr(x.iloc[i]["r"], method="spearman"))
            delais.append({"pays": pays, "delai_mois": k, "rho": rho, "ic_bas": np.percentile(boot, 2.5), "ic_haut": np.percentile(boot, 97.5), "n_mois": len(x)})
    return pd.concat(lignes), pd.DataFrame(delais)


def contrats() -> pd.DataFrame:
    """Contrats individuels encore cotes : seuls ceux-ci sont sur Yahoo. Aucun contrat expire."""
    import yfinance as yf
    dest = ROOT / "data/raw/t1_marches/contrats"
    dest.mkdir(parents=True, exist_ok=True)
    tables = {}
    for t in ("CCZ26.NYB", "CCH27.NYB", "CCK27.NYB", "CCN27.NYB", "CCU27.NYB"):
        h = yf.Ticker(t).history(period="max", auto_adjust=False, actions=False)
        if len(h):
            h.index = h.index.tz_localize(None).normalize()
            h.to_csv(dest / f"{t.replace('.', '_')}.csv")
            tables[t[:5]] = h["Close"]
    cc = pd.read_parquet(ROOT / "data/live/cc_f.parquet")["Close"].rename("CC=F")
    t = pd.concat([cc] + [v.rename(k) for k, v in tables.items()], axis=1).loc["2025":].dropna(subset=["CC=F"])
    noms = list(tables)
    ecart = pd.DataFrame({k: (t["CC=F"] - t[k]).abs() for k in noms})
    t["contrat_suivi"] = ecart.idxmin(axis=1).where(ecart.min(axis=1) < 0.5)
    if {"CCZ26", "CCH27"} <= set(noms):
        t["ecart_H27_Z26_pct"] = (t["CCH27"] / t["CCZ26"] - 1) * 100
    return t


def rendements(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    p, saut = d["cacao_close"], d["saut_echeance"].astype(bool)
    r = np.log(p).diff()
    t = pd.DataFrame({"r_brut": r, "r_neutre": r.where(~saut, 0.0), "saut": saut})
    t["prix_neutre"] = p.iloc[0] * np.exp(t["r_neutre"].fillna(0).cumsum())
    resume = []
    for s in (0.05, 0.08, 0.10):
        ext = t["r_brut"].abs() > s
        resume.append({"seuil_pct": s * 100, "n_extremes": int(ext.sum()), "dont_jours_de_saut": int((ext & t["saut"]).sum()),
                       "part_saut": float((ext & t["saut"]).sum() / max(ext.sum(), 1))})
    resume = pd.DataFrame(resume)
    resume.attrs["n_sauts"] = int(saut.sum())
    return t, resume


def consequences(d: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """Volatilite : persistance et HAR hors echantillon, cible brute contre cible sans sauts."""
    lignes = []
    for nom, r in (("brute", t["r_brut"]), ("sans_sauts", t["r_neutre"])):
        Z = pd.DataFrame({f"vol{n}": r.rolling(n).std() * np.sqrt(252) for n in (5, 20, 60)})
        for h in (5, 20, 60, 120):
            y = r.rolling(h).std().shift(-h) * np.sqrt(252)
            pers = r.rolling(h).std() * np.sqrt(252)
            har = pd.Series(index=d.index, dtype=float)
            for tr, te in plis(d.index, DEBUT, FIN, h):
                ok = tr[(y.iloc[tr].notna() & Z.iloc[tr].notna().all(axis=1)).to_numpy()]
                tt = te[Z.iloc[te].notna().all(axis=1).to_numpy()]
                har.iloc[tt] = LinearRegression().fit(Z.iloc[ok], y.iloc[ok]).predict(Z.iloc[tt])
            c = y.dropna().index.intersection(har.dropna().index)
            c = c[(c.year >= DEBUT)]
            lignes.append({"serie": nom, "horizon": h, "vol_moyenne": float(y[c].mean()),
                           "rmse_persistance": float(np.sqrt(((y[c] - pers[c]) ** 2).mean())),
                           "rmse_har": float(np.sqrt(((y[c] - har[c]) ** 2).mean()))})
    return pd.DataFrame(lignes)


def main() -> None:
    t0 = time.time()
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    association(d).to_csv(OUT / "association_variables.csv", index=False)
    pm, dl = climat(d)
    pm.to_csv(OUT / "pluie_mensuelle_pays.csv", index=False)
    dl.to_csv(OUT / "climat_delais.csv", index=False)
    print(dl.round(3).to_string(index=False))
    ctr = contrats()
    ctr.to_csv(OUT / "ccf_contrats.csv")
    print("Contrat suivi par CC=F :", ctr["contrat_suivi"].value_counts(dropna=False).to_dict())
    print(ctr.dropna(subset=["contrat_suivi"]).groupby("contrat_suivi").apply(lambda g: (g.index.min().date(), g.index.max().date()), include_groups=False))
    t, res = rendements(d)
    t.to_parquet(OUT / "ccf_rendements.parquet")
    res.to_csv(OUT / "ccf_resume.csv", index=False)
    print(res.to_string(index=False), "| jours de saut :", res.attrs["n_sauts"])
    cq = consequences(d, t)
    cq.to_csv(OUT / "ccf_consequences.csv", index=False)
    print(cq.round(4).to_string(index=False))
    print(f"Durée {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
