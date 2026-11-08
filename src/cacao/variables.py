"""Construit les variables du modele selon l'horizon, sans utiliser les cibles.

Chaque colonne depend uniquement du passe de la date. Le test de troncature le verifie.
"""
import numpy as np
import pandas as pd

from cacao.meteo import anomalie_passee

PAYS = ["CIV", "GHA", "IDN", "MONDE"]
FENETRES = {1: (5, 20), 5: (5, 20), 20: (20, 60), 60: (60, 120), 120: (60, 120)}
UN_MOIS, UN_TRIMESTRE, UN_AN = 21, 63, 252
PRIX_MARCHE = ["cacao_close", "dx_y_nyb", "ng_f", "eurusd_x", "ghs_x", "idr_x", "ngn_x",
               "barn_sw", "hsy", "mdlz", "nesn_sw", "lisn_sw", "lisp_sw"]
NASA = ["NASA_T2M_MAX", "NASA_RH2M", "NASA_GWETROOT", "NASA_ALLSKY_SFC_SW_DWN", "NASA_WS2M"]
ENGRAIS = ["PRIX_UREE", "PRIX_DAP", "PRIX_TSP", "PRIX_POTASSE"]
PROCHES = ["PRIX_SUCRE", "PRIX_HUILE_PALME", "PRIX_CAFE_ROBUSTA"]
FAO = {"biodiversite": ["FAO_RENDEMENT", "FAO_PESTICIDES", "FAO_AZOTE"], "production_offre": ["FAO_PRODUCTION"]}


def _variation(s: pd.Series, n: int) -> pd.Series:
    """Variation relative, valable aussi quand la serie passe sous zero."""
    return (s - s.shift(n)) / s.shift(n).abs()


def _ecart_annuel(s: pd.Series) -> pd.Series:
    return s / s.shift(1).rolling(UN_AN, min_periods=UN_AN // 2).mean() - 1


def construire(d: pd.DataFrame, h: int) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Renvoie les variables et la liste des colonnes de chaque famille."""
    court, long_ = FENETRES[h]
    f: dict[str, dict[str, pd.Series]] = {k: {} for k in (
        "climat", "geopolitique", "biodiversite", "couts_production", "production_offre", "marche_finance",
        "investisseurs_biais", "demande_substituts")}
    famille_prix = {"cacao_close": "marche_finance", "dx_y_nyb": "marche_finance", "ng_f": "couts_production",
                    "eurusd_x": "couts_production", "ghs_x": "couts_production", "idr_x": "couts_production",
                    "ngn_x": "couts_production"}
    for c in PRIX_MARCHE:
        cible = f[famille_prix.get(c, "demande_substituts")]
        cible[f"{c}_r{court}"] = np.log(d[c] / d[c].shift(court))
        cible[f"{c}_r{long_}"] = np.log(d[c] / d[c].shift(long_))
    for n in (court, long_):
        f["couts_production"][f"cl_f_v{n}"] = _variation(d["cl_f"], n)
        f["marche_finance"][f"tnx_d{n}"] = d["tnx"].diff(n)
        f["marche_finance"][f"irx_d{n}"] = d["irx"].diff(n)
    r = np.log(d["cacao_close"]).diff()
    for n in (court, long_):
        f["marche_finance"][f"cacao_vol{n}"] = r.rolling(n).std()
    f["marche_finance"]["cacao_volume_ecart"] = _ecart_annuel(d["cacao_volume"].rolling(UN_MOIS).mean())

    for v in NASA:
        for p in PAYS:
            f["climat"][f"{v}_{p}_a30"] = anomalie_passee(d[f"{v}_{p}"].rolling(30, min_periods=20).mean())
    for c in d.columns:
        if c.startswith(("ERA5_ANOM", "CHIRPS_ANOM")) and c.endswith(tuple(PAYS)):
            f["climat"][c] = d[c]
    f["climat"]["ONI"] = d["ONI"]
    f["climat"]["ONI_d63"] = d["ONI"].diff(UN_TRIMESTRE)

    for c in d.columns:
        if c.startswith("GDELT_EV_") and c.endswith(("CIV", "GHA", "IDN")):
            f["geopolitique"][c] = _ecart_annuel(d[c]) if "PART" in c else d[c]
        elif c.startswith("GPR_GPRD"):
            f["geopolitique"][f"{c}_m{court}"] = np.log(d[c]).rolling(court).mean()
            f["geopolitique"][f"{c}_m{long_}"] = np.log(d[c]).rolling(long_).mean()
        elif c.startswith("GPR_MENSUEL"):
            f["geopolitique"][c] = np.log(d[c])

    for famille, racines in FAO.items():
        for racine in racines:
            for p in PAYS[:3]:
                f[famille][f"{racine}_{p}_a"] = np.log(d[f"{racine}_{p}"]).diff(UN_AN)
    for p in PAYS[:3]:
        f["biodiversite"][f"FEUX_{p}_a30"] = anomalie_passee(np.log1p(d[f"FEUX_{p}"].rolling(30, min_periods=20).sum()))

    for c in ENGRAIS:
        f["couts_production"][f"{c}_d21"] = d[c].diff(UN_MOIS)
        f["couts_production"][f"{c}_d63"] = d[c].diff(UN_TRIMESTRE)
    for c in PROCHES:
        f["demande_substituts"][f"{c}_d21"] = d[c].diff(UN_MOIS)
        f["demande_substituts"][f"{c}_d63"] = d[c].diff(UN_TRIMESTRE)

    i = f["investisseurs_biais"]
    for c in ("CFTC_NET_FONDS", "CFTC_NET_NON_COMMERCIAUX", "CFTC_NET_PRODUCTEURS"):
        i[c] = d[c]
        i[f"{c}_d{long_}"] = d[c].diff(long_)
    i[f"CFTC_INTERET_OUVERT_r{long_}"] = np.log(d["CFTC_INTERET_OUVERT"] / d["CFTC_INTERET_OUVERT"].shift(long_))
    for c in d.columns:
        if c.startswith("TRENDS_"):
            i[c] = d[c]
        elif c.startswith("GDELT_cacao"):
            i[f"{c}_m{long_}"] = d[c].rolling(long_, min_periods=long_ // 2).mean()

    X = pd.DataFrame({c: s for fam in f.values() for c, s in fam.items()}).replace([np.inf, -np.inf], np.nan)
    return X, {k: list(v) for k, v in f.items()}
