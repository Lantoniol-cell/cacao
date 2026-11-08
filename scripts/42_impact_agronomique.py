"""Module d'impact agronomique (protocole.md, point 12) : effet de la pluie et de la
temperature sur la production de cacao, panel de 9 pays.

Modele : log(production) = effets fixes pays + effets fixes annee + tendance par pays
         + b1 z_N + b2 z_N^2 + b3 z_{N-1} + b4 z_{N-1}^2 (+ temperature dans le modele 2005+)
z : pluie annuelle CHIRPS centree-reduite dans chaque pays sur 1991-2024.

Inference : erreurs regroupees par pays (CR1) ; p-value de chaque coefficient par bootstrap
sauvage par pays sous l'hypothese nulle (Rademacher, 512 combinaisons enumerees) ; test
global de la pluie par permutation des annees de meteo a l'interieur de chaque pays.

Sorties dans outputs/metriques/ : impact_coefficients.csv, impact_permutation.csv,
impact_courbe.csv

Usage : .venv/Scripts/python.exe scripts/42_impact_agronomique.py
"""
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/metriques"
GRAINE, PERMUTATIONS = 42, 2000
PLUIE = ["pluie_N", "pluie_N2", "pluie_N1", "pluie_N12"]
pd.set_option("display.width", 200, "display.max_columns", None)


def preparer() -> pd.DataFrame:
    p = pd.read_parquet(ROOT / "data/processed/impact_panel.parquet").sort_values(["pays", "annee"])
    ref = p[(p["annee"] >= 1991) & (p["annee"] <= 2024)]
    for col, nom in (("pluie_mm", "z"), ("tmax_c", "t")):
        m = ref.groupby("pays")[col].mean()
        s = ref.groupby("pays")[col].std()
        p[nom] = (p[col] - p["pays"].map(m)) / p["pays"].map(s)
    g = p.groupby("pays")
    p["pluie_N"], p["pluie_N1"], p["pluie_lead"] = p["z"], g["z"].shift(1), g["z"].shift(-1)
    p["pluie_N2"], p["pluie_N12"], p["pluie_lead2"] = p["pluie_N"] ** 2, p["pluie_N1"] ** 2, p["pluie_lead"] ** 2
    p["tmax_N"], p["tmax_N1"] = p["t"], g["t"].shift(1)
    p["y"] = np.log(p["production_t"])
    return p


def matrice(d: pd.DataFrame, cols: list[str], tendances: bool = True) -> np.ndarray:
    blocs = [d[cols].to_numpy(float), pd.get_dummies(d["pays"], dtype=float).to_numpy(),
             pd.get_dummies(d["annee"], drop_first=True, dtype=float).to_numpy()]
    if tendances:
        t = (d["annee"] - d["annee"].mean()).to_numpy(float)
        blocs.append(pd.get_dummies(d["pays"], dtype=float).to_numpy()[:, 1:] * t[:, None])
    return np.hstack(blocs)


def mco(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b


def cr1(X, e, grappes):
    """Variance regroupee par pays avec la correction de petit echantillon usuelle."""
    G, (n, k) = len(np.unique(grappes)), X.shape
    pinv = np.linalg.pinv(X.T @ X)
    viande = sum(np.outer(X[grappes == g].T @ e[grappes == g], X[grappes == g].T @ e[grappes == g]) for g in np.unique(grappes))
    return G / (G - 1) * (n - 1) / (n - k) * pinv @ viande @ pinv


def bootstrap_nul(d, cols, j, tendances=True):
    """p-value du coefficient j : bootstrap sauvage par pays, hypothese nulle imposee."""
    y, gr = d["y"].to_numpy(), d["pays"].to_numpy()
    X = matrice(d, cols, tendances)
    b, e = mco(X, y)
    t = b[j] / np.sqrt(cr1(X, e, gr)[j, j])
    Xr = np.delete(X, j, axis=1)
    br, er = mco(Xr, y)
    ajuste = Xr @ br
    pays = np.unique(gr)
    idx = np.searchsorted(pays, gr)
    stats = []
    for signes in itertools.product((-1.0, 1.0), repeat=len(pays)):
        w = np.array(signes)[idx]
        bs, es = mco(X, ajuste + w * er)
        stats.append(bs[j] / np.sqrt(cr1(X, es, gr)[j, j]))
    return float(np.mean(np.abs(stats) >= abs(t) - 1e-12))


def estimer(d, cols, nom, tendances=True, tester=None):
    d = d.dropna(subset=["y"] + cols)
    X, y, gr = matrice(d, cols, tendances), d["y"].to_numpy(), d["pays"].to_numpy()
    b, e = mco(X, y)
    v = cr1(X, e, gr)
    lignes = []
    for j, c in enumerate(cols):
        lignes.append({"modele": nom, "variable": c, "coef": b[j], "se_cr1": np.sqrt(v[j, j]),
                       "p_bootstrap": bootstrap_nul(d, cols, j, tendances) if (tester is None or c in tester) else np.nan,
                       "n": len(d), "pays": d["pays"].nunique(), "annees": f"{d['annee'].min()}-{d['annee'].max()}"})
    return lignes


def permutation(d, cols_pluie, autres=(), tendances=True):
    """Gain de R2 intra apporte par la pluie, face a 2000 permutations des annees par pays."""
    d = d.dropna(subset=["y"] + list(cols_pluie) + list(autres)).reset_index(drop=True)
    y = d["y"].to_numpy()
    _, e0 = mco(matrice(d, list(autres), tendances), y)
    ssr0 = e0 @ e0

    def gain(dd):
        _, e1 = mco(matrice(dd, list(cols_pluie) + list(autres), tendances), y)
        return (ssr0 - e1 @ e1) / ssr0

    obs = gain(d)
    alea = np.random.default_rng(GRAINE)
    tirages = []
    for _ in range(PERMUTATIONS):
        dd = d.copy()
        for _, i in d.groupby("pays").groups.items():
            i = np.asarray(i)
            dd.loc[i, list(cols_pluie)] = d.loc[alea.permutation(i), list(cols_pluie)].to_numpy()
        tirages.append(gain(dd))
    return obs, float(np.mean(np.array(tirages) >= obs)), float(np.percentile(tirages, 95))


def courbe(d, cols):
    """Effet en % sur la production selon l'ecart de pluie, avec bande bootstrap sauvage."""
    d = d.dropna(subset=["y"] + cols)
    X, y, gr = matrice(d, cols), d["y"].to_numpy(), d["pays"].to_numpy()
    b, e = mco(X, y)
    pays = np.unique(gr)
    idx = np.searchsorted(pays, gr)
    tirages = np.array([mco(X, X @ b + np.array(s)[idx] * e)[0][:4] for s in itertools.product((-1.0, 1.0), repeat=len(pays))])
    z = np.round(np.arange(-2.5, 2.51, 0.1), 2)
    sortie = []
    for annee, (i, j) in (("N", (0, 1)), ("N-1", (2, 3))):
        eff = np.exp(np.outer(tirages[:, i], z) + np.outer(tirages[:, j], z ** 2)) - 1
        centre = np.exp(b[i] * z + b[j] * z ** 2) - 1
        sortie.append(pd.DataFrame({"annee_pluie": annee, "z": z, "effet_pct": centre * 100,
                                    "bas_pct": np.percentile(eff, 2.5, axis=0) * 100, "haut_pct": np.percentile(eff, 97.5, axis=0) * 100}))
    return pd.concat(sortie)


def main() -> None:
    p = preparer()
    base = p[(p["annee"] >= 1992) & (p["annee"] <= 2024)]
    officiel = base[base["code_fao"] == "A"]
    temp = base[base["annee"] >= 2006]

    lignes = estimer(base, PLUIE, "principal")
    lignes += estimer(base, PLUIE + ["pluie_lead", "pluie_lead2"], "placebo_N+1", tester=["pluie_lead", "pluie_lead2"])
    lignes += estimer(officiel, PLUIE, "officiel_seulement")
    lignes += estimer(base[base["pays"] != "IDN"], PLUIE, "sans_indonesie")
    lignes += estimer(base, PLUIE, "sans_tendances", tendances=False)
    lignes += estimer(temp, PLUIE + ["tmax_N", "tmax_N1"], "temperature_2006_2024")
    c = pd.DataFrame(lignes)
    c.to_csv(OUT / "impact_coefficients.csv", index=False)

    perm = []
    for nom, d, cols, autres, tend in (("principal", base, PLUIE, (), True), ("sans_tendances", base, PLUIE, (), False),
                                       ("temperature_seule", temp, ["tmax_N", "tmax_N1"], tuple(PLUIE), True)):
        obs, pv, q95 = permutation(d, cols, autres, tend)
        perm.append({"modele": nom, "variables_testees": "+".join(cols), "gain_r2_intra": obs, "p_permutation": pv,
                     "seuil_95_permutations": q95})
        print(f"Permutation {nom} : gain R2 {obs:.3f}, p = {pv:.3f}", flush=True)
    pd.DataFrame(perm).to_csv(OUT / "impact_permutation.csv", index=False)
    courbe(base, PLUIE).to_csv(OUT / "impact_courbe.csv", index=False)

    print("\nCoefficients (effet sur log production) :")
    print(c[["modele", "variable", "coef", "se_cr1", "p_bootstrap", "n", "annees"]].round(4).to_string(index=False))
    k = pd.read_csv(OUT / "impact_courbe.csv")
    print("\nEffet sur la production (%), pluie a -1,5 / +1,5 ecart-type :")
    print(k[k["z"].isin([-1.5, 1.5])].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
