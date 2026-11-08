"""Assemble la grille quotidienne et les donnees meteo, avec leur delai de disponibilite.

Chaque valeur n'entre qu'une fois publiable, strictement avant la seance. Delais :
NASA temperature, humidite, vent 3 jours ; rayonnement 6 jours ; ERA5 7 jours (observes sur
les API en novembre 2026) ; incendies 1 jour (hypothese, proche du temps reel, a confirmer) ;
CHIRPS le 25 du mois suivant ; GEFS des la seance suivant l'emission ; ONI le 15 du mois suivant la fin de la saison de trois mois
(hypothese prudente, a confirmer).

Sortie : data/processed/dataset_quotidien.parquet

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/29_construire_dataset_meteo.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from cacao.meteo import aligner_disponible

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/raw/t2_climat"
SAISONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
CONFIANCE_MIN = 30
TOLERANCE = 10
TOLERANCE_MOIS = 45
TOLERANCE_AN = 400
RETARD_ANS = 2  # une annee N n'est utilisee qu'a partir du 1er janvier N+2
PRIX = {"UREE": "Urea", "DAP": "DAP", "TSP": "TSP", "POTASSE": "Potassium chloride **", "SUCRE": "Sugar, world",
        "HUILE_PALME": "Palm oil", "CAFE_ROBUSTA": "Coffee, Robusta"}
NOMS_FAO = {"Côte d'Ivoire": "CIV", "Ghana": "GHA", "Indonesia": "IDN", "Ecuador": "ECU", "Cameroon": "CMR",
            "Brazil": "BRA", "Nigeria": "NGA", "Peru": "PER", "Dominican Republic": "DOM"}


def complements(points: pd.DataFrame, part: pd.DataFrame) -> pd.DataFrame:
    """Indices pays et monde du rayonnement et du vent, poids renormalises si un point manque."""
    fichiers = {i: pd.read_csv(BASE / f"power_complement/{i}.csv", index_col="date", parse_dates=True)
                for i in points.index}
    sortie = {}
    for v in ("ALLSKY_SFC_SW_DWN", "WS2M"):
        t = pd.concat({i: d[v] for i, d in fichiers.items()}, axis=1)
        p = points["poids"][t.columns]
        pays = pd.Index([i[:3] for i in t.columns])
        nat = t.mul(p).T.groupby(pays).sum(min_count=1).T / t.notna().mul(p).T.groupby(pays).sum().T
        w = part[nat.columns].reindex(nat.index.year)
        w.index = nat.index
        nat["MONDE"] = (nat * w).sum(axis=1, min_count=len(part.columns)) / w.sum(axis=1)
        sortie.update({f"{v}_{c}": nat[c] for c in nat})
    return pd.DataFrame(sortie)


def incendies(axe: pd.DatetimeIndex) -> pd.DataFrame:
    """Nombre quotidien de detections de vegetation fiables dans les zones de cacao."""
    lignes = []
    for f in sorted((BASE / "firms").glob("*.csv")):
        d = pd.read_csv(f, usecols=["acq_date", "confidence", "type"])
        d = d[(d["type"] == 0) & (d["confidence"] >= CONFIANCE_MIN)]
        lignes.append(d.groupby("acq_date").size().rename_axis("date").reset_index(name="n")
                      .assign(pays=f.stem[:3]))
    t = pd.concat(lignes).assign(date=lambda x: pd.to_datetime(x["date"]))
    t = t.pivot(index="date", columns="pays", values="n")
    jours = pd.date_range("2005-01-01", "2025-12-31", freq="D")
    return t.reindex(jours, fill_value=np.nan).fillna(0).rename_axis("date")


def oni() -> pd.DataFrame:
    t = pd.read_csv(BASE / "oni.txt", sep=r"\s+")
    # fin = 1er jour du dernier mois de la saison (DJF 2020 -> 2020-02-01, NDJ 2020 -> 2021-01-01)
    fin = pd.to_datetime(dict(year=t["YR"], month=[SAISONS.index(s) + 1 for s in t["SEAS"]], day=1)) \
        + pd.DateOffset(months=1)
    return pd.DataFrame({"ONI": t["ANOM"].to_numpy(), "disponible_le": (fin + pd.Timedelta(days=45)).to_numpy()})


def positions() -> pd.DataFrame:
    """Positions nettes en part de l'interet ouvert, datees du mardi de reference."""
    cle = "report_date_as_yyyy_mm_dd"
    a = pd.read_csv(ROOT / "data/raw/t4_investisseurs/cftc_legacy.csv", low_memory=False, parse_dates=[cle]).set_index(cle)
    b = pd.read_csv(ROOT / "data/raw/t4_investisseurs/cftc_desagrege.csv", low_memory=False, parse_dates=[cle]).set_index(cle)
    oi, oib = a["open_interest_all"], b["open_interest_all"]
    r = pd.DataFrame({"INTERET_OUVERT": oi, "NET_NON_COMMERCIAUX": (a["noncomm_positions_long_all"] - a["noncomm_positions_short_all"]) / oi,
                      "NET_COMMERCIAUX": (a["comm_positions_long_all"] - a["comm_positions_short_all"]) / oi})
    r["NET_FONDS"] = (b["m_money_positions_long_all"] - b["m_money_positions_short_all"]) / oib
    r["NET_PRODUCTEURS"] = (b["prod_merc_positions_long"] - b["prod_merc_positions_short"]) / oib
    return r.loc["2004":].sort_index()


def prix_mensuels() -> pd.DataFrame:
    """Prix Banque mondiale en logarithme : engrais et produits proches. Pas le cacao."""
    d = pd.read_excel(ROOT / "data/raw/t1_marches/controle/worldbank_CMO_monthly.xlsx", "Monthly Prices", header=None)
    noms = d.iloc[4].astype(str).str.strip()
    d = d.iloc[6:].copy()
    d.index = pd.to_datetime(d[0].str.replace("M", "-"), format="%Y-%m")
    return pd.DataFrame({cle: np.log(pd.to_numeric(d[noms[noms == nom].index[0]], errors="coerce"))
                         for cle, nom in PRIX.items()}).loc["2004":]


def annuels() -> pd.DataFrame:
    """Series FAOSTAT par pays, indexees par annee."""
    def lire(f, filtre, valeur):
        d = pd.read_csv(ROOT / "data/raw/t3_offre" / f)
        d = d[filtre(d) & d["Area"].isin(NOMS_FAO)].pivot(index="Year", columns="Area", values="Value")
        return d.rename(columns=NOMS_FAO).add_prefix(valeur + "_")
    return pd.concat([
        lire("faostat_cacao.csv", lambda d: d["Element"] == "Yield", "RENDEMENT"),
        lire("faostat_cacao.csv", lambda d: d["Element"] == "Production", "PRODUCTION"),
        lire("faostat_pesticides.csv", lambda d: (d["Item"] == "Pesticides (total)")
             & (d["Element"] == "Use per area of cropland"), "PESTICIDES"),
        lire("faostat_engrais.csv", lambda d: (d["Item"] == "Nutrient nitrogen N (total)")
             & (d["Element"] == "Use per area of cropland"), "AZOTE"),
    ], axis=1).loc[2002:]


def tensions() -> pd.DataFrame:
    """Evenements GDELT par pays, en cumul de 30 jours. Le ton est ecarte : son echelle casse."""
    d = pd.concat([pd.read_csv(f) for f in (ROOT / "data/raw/t5_geopolitique/gdelt_evenements").glob("*.csv")
                   if f.stat().st_size > 60])
    d["date"] = pd.to_datetime(d["date"])
    jours = pd.date_range(d["date"].min(), d["date"].max(), freq="D")
    monde = d.groupby("date")["n_monde"].first().reindex(jours)
    sortie = {}
    for iso, x in d.groupby("pays"):
        x = x.set_index("date").reindex(jours)
        n = x["n"].fillna(0).rolling(30, min_periods=30).sum()
        sortie[f"PART_{iso}"] = n / monde.rolling(30, min_periods=20).sum() * 1000
        sortie[f"CONFLIT_{iso}"] = x["conflit"].fillna(0).rolling(30, min_periods=30).sum() / n.where(n > 0)
        sortie[f"PROTESTATION_{iso}"] = x["protestation"].fillna(0).rolling(30, min_periods=30).sum() / n.where(n > 0)
    return pd.DataFrame(sortie)


def main() -> None:
    grille = pd.read_parquet(ROOT / "data/processed/grille_quotidienne_t1.parquet")
    axe = grille.index
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet").set_index("id")
    part = pd.read_csv(ROOT / "outputs/metriques/t2_poids_pays.csv", index_col=0)
    res = {}

    def ajouter(table: pd.DataFrame, delai: int, prefixe: str = "") -> None:
        dispo = pd.Series(table.index + pd.Timedelta(days=delai))
        for c in table:
            res[prefixe + c] = aligner_disponible(axe, table[c], dispo, TOLERANCE)

    nasa = pd.read_parquet(ROOT / "data/processed/meteo_pays.parquet")
    pluie_nasa = nasa.filter(like="PRECTOTCORR")
    ajouter(nasa.drop(columns=pluie_nasa.columns), 3, "NASA_")
    ajouter(pluie_nasa, 3, "ROBUSTESSE_")
    comp = complements(points, part)
    ajouter(comp.filter(like="WS2M"), 3, "NASA_")
    ajouter(comp.filter(like="ALLSKY"), 6, "NASA_")
    ajouter(pd.read_parquet(ROOT / "data/processed/pluie_era5_pays.parquet"), 7)

    chi = pd.read_parquet(ROOT / "data/processed/pluie_chirps_pays.parquet")
    for c in chi.columns.drop("disponible_le"):
        res[c] = aligner_disponible(axe, chi[c], chi["disponible_le"], TOLERANCE_MOIS)

    # GEFS : prevision emise a 00 UTC le jour E, utilisee des la seance E+1 (alignement strict).
    # Une emission manquante est remplacee par la derniere connue, 3 jours au plus.
    gefs = pd.read_parquet(ROOT / "data/processed/gefs_pays.parquet")
    for c in gefs:
        res[c] = aligner_disponible(axe, gefs[c], pd.Series(gefs.index), 3)

    o = oni()
    res["ONI"] = aligner_disponible(axe, o["ONI"], o["disponible_le"], TOLERANCE_MOIS)
    ajouter(incendies(axe).add_prefix("FEUX_"), 1)

    # Positions CFTC : arretees le mardi, publiees le vendredi apres la cloture du cacao.
    c = positions()
    for col in c.columns:
        res[f"CFTC_{col}"] = aligner_disponible(axe, c[col], pd.Series(c.index + pd.Timedelta(days=3)), TOLERANCE)

    g = pd.read_excel(ROOT / "data/raw/t5_geopolitique/gpr_quotidien.xls").set_index("date")
    ajouter(g[["GPRD", "GPRD_ACT", "GPRD_THREAT"]].astype(float), 7, "GPR_")
    m = pd.read_excel(ROOT / "data/raw/t5_geopolitique/gpr_mensuel.xls").set_index("month")
    m = m[["GPR", "GPRC_BRA", "GPRC_IDN", "GPRC_PER"]].astype(float).loc["2004":]
    fin_mois = pd.Series(m.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=10))
    for col in m:
        res[f"GPR_MENSUEL_{col}"] = aligner_disponible(axe, m[col], fin_mois, TOLERANCE_MOIS)

    fichiers = sorted((ROOT / "data/raw/t5_geopolitique").glob("gdelt_*.csv"))
    if fichiers:
        ajouter(pd.concat([pd.read_csv(f, index_col="date", parse_dates=True) for f in fichiers], axis=1), 1, "GDELT_")

    # Trends : seules les variations sont gardees, car l'echelle depend de toute la periode.
    t = np.log1p(pd.read_csv(ROOT / "data/raw/t4_investisseurs/google_trends_mensuel.csv", index_col=0, parse_dates=True))
    t.columns = [x.replace(" ", "_").upper() for x in t.columns]
    fin_mois = pd.Series(t.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=5))
    for col in t:
        for n in (1, 12):
            res[f"TRENDS_{col}_D{n}"] = aligner_disponible(axe, t[col].diff(n), fin_mois, TOLERANCE_MOIS)

    ajouter(tensions(), 1, "GDELT_EV_")

    p = prix_mensuels()
    fin_mois = pd.Series(p.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=5))
    for col in p:
        res[f"PRIX_{col}"] = aligner_disponible(axe, p[col], fin_mois, TOLERANCE_MOIS)

    a = annuels()
    dispo = pd.Series(pd.to_datetime((a.index + RETARD_ANS).astype(str) + "-01-01"))
    for col in a:
        res[f"FAO_{col}"] = aligner_disponible(axe, a[col], dispo, TOLERANCE_AN)

    meteo = pd.DataFrame(res)
    data = grille.join(meteo)
    data.to_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    print(f"Dataset : {data.shape}, {data.index.min().date()} -> {data.index.max().date()}")
    vide = meteo.isna().mean().sort_values(ascending=False).round(3)
    print("Part de vides, par famille de colonnes :")
    print(vide.groupby(vide.index.str.extract(r"^([A-Z]+(?:_[A-Z0-9]+)?)", expand=False)).max().to_string())
    print("Derniere valeur disponible :")
    print(meteo.apply(lambda c: c.last_valid_index()).groupby(lambda c: c.split("_")[0]).max().to_string())


if __name__ == "__main__":
    main()
