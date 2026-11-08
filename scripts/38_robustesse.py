"""Tests de robustesse du point 8 de protocole.md, modele principal (Gradient Boosting).

Variantes, chacune comparee au meme meilleur benchmark que scripts/37 :
- base : variables du modele principal (refait a l'identique, sert de reference) ;
- pluie_nasa : anomalies de pluie NASA a la place d'ERA5 et CHIRPS (test 1) ;
- gefs : base + previsions GEFS corrigees, jours 2 a 6 et 2 a 10 (test 5) ;
- oracle : base + meteo reellement observee sur les 7 jours a venir (test 5, "meteo parfaite").
  Cette variante utilise volontairement le futur : elle mesure le gain maximal qu'une
  prevision parfaite apporterait. Elle ne doit jamais etre lue comme un modele utilisable.

Le test 2 (sans 2024-2026) est lu sur la periode 2010-2023 : la validation chronologique
n'entraine jamais sur une annee posterieure au test. Les tests 3 (Random Forest) et 4
(fenetres de passage exclues) sont deja dans outputs/metriques/modele_horizons.csv.
Le test 6 (MapSPAM 2020, poids ICCO) n'est pas fait : extension, faute de temps.

Sortie : outputs/metriques/robustesse.csv

Usage : PYTHONPATH=src .venv/Scripts/python.exe -u scripts/38_robustesse.py
"""
import importlib.util
import time
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.evaluation import boosting, ecart_bootstrap, predire, score
from cacao.meteo import aligner_disponible, anomalie_passee
from cacao.variables import PAYS, construire

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("m37", ROOT / "scripts/37_modele_facteurs.py")
m37 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m37)
DEBUT, FIN, NIVEAU, TIRAGES = m37.DEBUT, m37.FIN, m37.NIVEAU, m37.TIRAGES
PERIODES_IC = {"2010-2026": (2010, 2026), "2010-2023": (2010, 2023)}


def pluie_nasa(axe: pd.DatetimeIndex) -> pd.DataFrame:
    """Meme traitement que l'ERA5 : cumuls 7 et 30 jours, anomalie passee, delai 3 jours."""
    m = pd.read_parquet(ROOT / "data/processed/meteo_pays.parquet")
    res = {}
    for p in PAYS:
        s = m[f"PRECTOTCORR_{p}"]
        for n in (7, 30):
            a = anomalie_passee(s.rolling(n, min_periods=n).sum())
            res[f"NASA_PLUIE_ANOM{n}J_{p}"] = aligner_disponible(axe, a, pd.Series(a.index + pd.Timedelta(days=3)), 10)
    return pd.DataFrame(res)


def oracle(axe: pd.DatetimeIndex) -> pd.DataFrame:
    """Meteo observee de la seance t a t+6 : pluie ERA5 et Tmax NASA. Utilise le futur."""
    e = pd.read_parquet(ROOT / "data/processed/pluie_era5_pays.parquet")
    m = pd.read_parquet(ROOT / "data/processed/meteo_pays.parquet")
    res = {}
    for p in PAYS:
        res[f"ORACLE_PLUIE7J_{p}"] = e[f"ERA5_ANOM7J_{p}"].shift(-6, freq="D").reindex(axe)
        t = anomalie_passee(m[f"T2M_MAX_{p}"].rolling(7, min_periods=7).mean())
        res[f"ORACLE_TMAX7J_{p}"] = t.shift(-6, freq="D").reindex(axe)
    return pd.DataFrame(res)


def variantes(d: pd.DataFrame, h: int, nasa: pd.DataFrame, orc: pd.DataFrame) -> dict:
    X, fam = construire(d, h)
    pluie = [c for c in fam["climat"] if c.startswith(("ERA5_ANOM", "CHIRPS_ANOM"))]
    gefs = [c for c in d.columns if c.startswith("GEFS_") and c.endswith(tuple(PAYS))]
    return {
        "base": X,
        "pluie_nasa": X.drop(columns=pluie).join(nasa),
        "gefs": X.join(d[gefs]),
        "oracle": X.join(orc),
    }


def comparer(y, p, ref, classification, h, cible, lecture, variante, ref_nom, masque=None) -> list[dict]:
    if masque is not None:
        y = y[masque.reindex(y.index).fillna(False).astype(bool)]
    lignes = []
    commun = y.dropna().index.intersection(p.dropna().index).intersection(ref.dropna().index)
    for per, (a, b) in PERIODES_IC.items():
        c = commun[(commun.year >= a) & (commun.year <= b)]
        ecart, bas, haut = ecart_bootstrap(y[c], p[c], ref[c], classification, bloc=max(20, h),
                                           tirages=TIRAGES, niveau=NIVEAU)
        lignes.append({"variante": variante, "cible": cible, "horizon": h, "lecture": lecture, "periode": per,
                       "benchmark": ref_nom, "n": len(c), "score": score(y[c], p[c], classification),
                       "score_benchmark": score(y[c], ref[c], classification), "ecart": ecart,
                       "ic_bas": bas, "ic_haut": haut, "bat_benchmark": bool(bas > 0)})
    return lignes


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    nasa, orc = pluie_nasa(d.index), oracle(d.index)
    print(f"Pluie NASA : {nasa.shape}, vides {nasa.isna().mean().mean():.1%} ; oracle : {orc.shape}, vides {orc.isna().mean().mean():.1%}")
    t0, lignes = time.time(), []
    for cible, h in [("sens", h) for h in m37.HORIZONS] + [("vol", h) for h in m37.HORIZONS_VOL]:
        classification = cible == "sens"
        y = d[f"cible_hausse_{h}"] if classification else d[f"cible_vol_{h}"]
        cand = m37.benchmark_sens(d, h, y) if classification else m37.benchmark_vol(d, h)
        ref_nom, ref = m37.meilleur_benchmark(y, cand, classification)
        if h <= 20:
            masque = d[f"passage_dans_{h}"] == 0
            cand_c = {k: v.where(masque) for k, v in cand.items()} if classification else cand
            ref_nom_c, ref_c = m37.meilleur_benchmark(y.where(masque), cand_c, classification)
        elif classification:
            yn = d[f"cible_hausse_neutre_{h}"]
            ref_nom_n, ref_n = m37.meilleur_benchmark(yn, m37.benchmark_sens(d, h, yn), True)
        for nom, X in variantes(d, h, nasa, orc).items():
            p, _ = predire(X, y, boosting, classification, DEBUT, FIN, h)
            lignes += comparer(y, p, ref, classification, h, cible, "brute", nom, ref_nom)
            if h <= 20:
                lignes += comparer(y, p, ref_c, classification, h, cible, "sans_passage", nom, ref_nom_c, masque)
            elif classification:
                pn, _ = predire(X, yn, boosting, True, DEBUT, FIN, h)
                lignes += comparer(yn, pn, ref_n, True, h, cible, "sans_sauts", nom, ref_nom_n)
        print(f"{cible} h={h} fait, {(time.time() - t0) / 60:.0f} min", flush=True)
        pd.DataFrame(lignes).to_csv(ROOT / "outputs/metriques/robustesse.csv", index=False)

    t = pd.DataFrame(lignes)
    pd.set_option("display.width", 220, "display.max_columns", None)
    for per in PERIODES_IC:
        x = t[(t["periode"] == per) & (t["lecture"] == "brute")]
        print(f"\nEcart au benchmark, lecture brute, {per} (IC bas ; * = bat le benchmark) :")
        x = x.assign(v=x["ecart"].round(3).astype(str) + " [" + x["ic_bas"].round(3).astype(str) + "]"
                     + np.where(x["bat_benchmark"], "*", ""))
        print(x.pivot(index=["cible", "horizon"], columns="variante", values="v").to_string())
    print("\nVariantes qui battent le benchmark :")
    print(t[t["bat_benchmark"]][["variante", "cible", "horizon", "lecture", "periode", "ecart", "ic_bas", "ic_haut"]].round(4).to_string(index=False))
    print(f"\nDuree : {(time.time() - t0) / 60:.0f} min")


if __name__ == "__main__":
    main()
