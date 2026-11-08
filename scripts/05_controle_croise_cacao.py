"""Compare CC=F aux prix mensuels du cacao de la Banque mondiale (ICCO).

La serie de controle n'est pas identique par construction : elle n'a pas la meme
definition que CC=F. On attend donc un ecart, pas une egalite. Le test utile est
de savoir si neutraliser les passages d'echeance rapproche CC=F du controle.
Sortie : outputs/metriques/t1_controle_mensuel.csv

Usage : .venv/Scripts/python.exe scripts/05_controle_croise_cacao.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "data/raw/t1_marches/controle/worldbank_CMO_monthly.xlsx"
SORTIE = ROOT / "outputs/metriques/t1_controle_mensuel.csv"
pd.set_option("display.width", 200, "display.max_columns", None, "display.max_rows", 200)


def lire_banque_mondiale() -> pd.Series:
    brut = pd.read_excel(CTRL, sheet_name="Monthly Prices", header=None)
    ligne = brut.index[brut.eq("Cocoa").any(axis=1)][0]
    colonne = brut.columns[brut.loc[ligne].eq("Cocoa")][0]
    print("Unite :", brut.loc[ligne + 1, colonne], "| en-tete ligne", ligne)
    dates = brut[0].astype(str).str.fullmatch(r"\d{4}M\d{2}")
    s = pd.to_numeric(brut.loc[dates, colonne], errors="coerce")
    s.index = pd.PeriodIndex(brut.loc[dates, 0].str.replace("M", "-"), freq="M")
    return s["2005-01":].rename("controle") * 1000  # $/kg vers $/t


def rendements_neutralises(cc: pd.DataFrame, passages: pd.DatetimeIndex) -> pd.Series:
    """Met a zero le rendement du jour de saut : le plus grand des deux jours."""
    r = np.log(cc["Close"]).diff()
    propre = r.copy()
    for d in passages:
        i = cc.index.get_loc(d)
        fenetre = r.iloc[i:i + 2]
        propre.loc[fenetre.abs().idxmax()] = 0.0
    return propre


def main() -> None:
    cc = pd.read_csv(ROOT / "data/raw/t1_marches/CC_F.csv", index_col="date", parse_dates=True)
    passages = pd.read_csv(ROOT / "outputs/metriques/t1_echeances_cacao.csv", parse_dates=["date"])["date"]
    ctrl = lire_banque_mondiale()
    print("Controle :", ctrl.index.min(), "->", ctrl.index.max(), "| manquants :", int(ctrl.isna().sum()))

    r = np.log(cc["Close"]).diff()
    propre = rendements_neutralises(cc, pd.DatetimeIndex(passages))
    chaine = cc["Close"].iloc[0] * np.exp(propre.fillna(0).cumsum())

    m = pd.DataFrame({
        "controle": ctrl,
        "brut": cc["Close"].groupby(cc.index.to_period("M")).mean(),
        "neutralise": chaine.groupby(chaine.index.to_period("M")).mean(),
    }).dropna()
    # Le niveau chaine derive par construction : on le recale sur 24 mois glissants
    # uniquement pour lire l'ecart, sans jamais s'en servir comme prix.
    m["ecart_brut_pct"] = (m["brut"] / m["controle"] - 1) * 100
    m.to_csv(SORTIE)
    print(f"Mois compares : {len(m)}, de {m.index.min()} a {m.index.max()}")

    print("\n=== Ecart de niveau brut CC=F / controle (%) par periode ===")
    for nom, debut, fin in [("2005-2022", "2005", "2022"), ("2023", "2023", "2023"), ("2024", "2024", "2024"),
                            ("2025", "2025", "2025"), ("2026", "2026", "2026")]:
        e = m.loc[debut:fin, "ecart_brut_pct"]
        print(f"{nom:10} moyenne {e.mean():6.1f}  abs moyen {e.abs().mean():5.1f}  min {e.min():6.1f}  max {e.max():6.1f}  n={len(e)}")

    print("\n=== Variations mensuelles comparees au controle ===")
    d = np.log(m[["controle", "brut", "neutralise"]]).diff().dropna()
    for nom, debut, fin in [("toute periode", "2005", "2026"), ("2005-2022", "2005", "2022"), ("2023-2026", "2023", "2026"),
                            ("2024", "2024", "2024")]:
        x = d.loc[debut:fin]
        ligne = [f"{nom:14} n={len(x):3d}"]
        for c in ["brut", "neutralise"]:
            rmse = float(np.sqrt(((x[c] - x["controle"]) ** 2).mean())) * 100
            sens = float((np.sign(x[c]) == np.sign(x["controle"])).mean()) * 100
            ligne.append(f"{c}: corr {x[c].corr(x['controle']):.3f} ecart-type diff {rmse:.2f} pts, meme sens {sens:.0f} %")
        print(" | ".join(ligne))

    print("\n=== 10 plus grands ecarts mensuels de variation (brut - controle, en points de log) ===")
    gros = (d["brut"] - d["controle"]).abs().nlargest(10).index.sort_values()
    print((d.loc[gros] * 100).round(1))

    print("\n=== Annee 2024 : passages d'echeance, saut signe (%) ===")
    p = pd.read_csv(ROOT / "outputs/metriques/t1_echeances_cacao.csv", parse_dates=["date"], index_col="date")
    saut = p[["r", "r_lendemain"]].apply(lambda l: l.iloc[l.abs().argmax()], axis=1)
    p["saut_signe_pct"] = (np.exp(saut) - 1) * 100
    print(p.loc["2023":"2026", ["Close", "Volume", "saut_signe_pct"]].round(1))
    print("\nPart des sauts negatifs par periode :")
    for debut, fin in [("2005", "2022"), ("2024", "2025")]:
        s = p.loc[debut:fin, "saut_signe_pct"]
        print(f"  {debut}-{fin} : {(s < 0).mean():.0%} negatifs, moyenne {s.mean():.1f} %")

    print("\n=== Volatilite annualisee hors passages (%) ===")
    v = propre.groupby(propre.index.year).std() * np.sqrt(252) * 100
    print(v.round(0).astype(int).to_dict())

    print("\n=== Neutralisation ciblee : seuls les sauts au-dela d'un seuil ===")
    sauts_abs = np.exp(saut.abs()) - 1
    print("Controle en variations mensuelles, 2023-2026 puis periode complete")
    for seuil in [0.0, 0.05, 0.10, 0.15]:
        retenus = pd.DatetimeIndex(sauts_abs.index[sauts_abs > seuil])
        pr = rendements_neutralises(cc, retenus)
        ch = cc["Close"].iloc[0] * np.exp(pr.fillna(0).cumsum())
        cible = np.log(pd.DataFrame({
            "controle": ctrl, "serie": ch.groupby(ch.index.to_period("M")).mean()
        }).dropna()).diff().dropna()
        res = []
        for debut, fin in [("2023", "2026"), ("2005", "2026")]:
            x = cible.loc[debut:fin]
            rmse = float(np.sqrt(((x["serie"] - x["controle"]) ** 2).mean())) * 100
            res.append(f"corr {x['serie'].corr(x['controle']):.3f}, ecart {rmse:.2f} pts")
        print(f"seuil {seuil:>4.0%} : {len(retenus):3d} passages | " + " | ".join(res))

    print("\n=== Moyennes mensuelles 2024 ($/t) ===")
    print(m.loc["2024", ["controle", "brut", "ecart_brut_pct"]].round(0))


if __name__ == "__main__":
    main()
