"""Tableau de bord : cours quotidiens de CC=F, mise a jour incrementale et controles.

Source : Yahoo Finance via yfinance (API non officielle, cours retardes). Le fichier de
travail est data/live/cc_f.parquet, distinct des donnees brutes du modele.
"""
from pathlib import Path

import numpy as np
import pandas as pd

TICKER = "CC=F"
COLONNES = ["Open", "High", "Low", "Close", "Volume"]
RECOUVREMENT_JOURS = 10  # on retelecharge les derniers jours : Yahoo corrige parfois la derniere seance


def telecharger(debut: str) -> pd.DataFrame:
    import yfinance as yf
    df = yf.Ticker(TICKER).history(start=debut, auto_adjust=False, actions=False)
    if df.empty:
        raise RuntimeError(f"Aucune donnee recue pour {TICKER} depuis {debut}")
    df.index = df.index.tz_localize(None).normalize()
    df.index.name = "date"
    return df[COLONNES].astype(float)


def controler(df: pd.DataFrame) -> list[str]:
    """Anomalies bloquantes : la table est alors rejetee. Vide si tout va bien."""
    pb = []
    if df.index.duplicated().any():
        pb.append("dates en double")
    if not df.index.is_monotonic_increasing:
        pb.append("dates non triees")
    if df["Close"].isna().any() or (df["Close"] <= 0).any():
        pb.append("cloture manquante ou non positive")
    if (df["High"] < df["Low"]).any():
        pb.append("plus haut sous le plus bas")
    return pb


def avertissements(df: pd.DataFrame) -> dict:
    """Particularites connues de Yahoo, signalees sans corriger les donnees.

    La cloture de CC=F est le prix de reglement, qui peut sortir de la fourchette des
    echanges (environ 11 % des seances depuis 2005). Certaines seances proches d'un passage
    d'echeance ont un volume tres faible.
    """
    hors_fourchette = (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
    return {"cloture_hors_fourchette": int(hors_fourchette.sum()), "volume_inferieur_a_10": int((df["Volume"] < 10).sum())}


def fusionner(ancien: pd.DataFrame, nouveau: pd.DataFrame) -> pd.DataFrame:
    """Les seances retelechargees remplacent les anciennes : la derniere version gagne."""
    tout = pd.concat([ancien[~ancien.index.isin(nouveau.index)], nouveau]).sort_index()
    return tout[~tout.index.duplicated(keep="last")]


def mettre_a_jour(chemin: Path, debut: str = "2005-01-01") -> tuple[pd.DataFrame, int]:
    """Ajoute les nouvelles seances au fichier ; renvoie la table et le nombre de seances ajoutees."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if chemin.exists():
        ancien = pd.read_parquet(chemin)
        depart = (ancien.index.max() - pd.Timedelta(days=RECOUVREMENT_JOURS)).strftime("%Y-%m-%d")
        df = fusionner(ancien, telecharger(depart))
        ajout = len(df) - len(ancien)
    else:
        df = telecharger(debut)
        ajout = len(df)
    pb = controler(df)
    if pb:
        raise ValueError(f"Cours {TICKER} rejetes : {', '.join(pb)}")
    df.to_parquet(chemin)
    return df, ajout


def resume(df: pd.DataFrame) -> dict:
    """Chiffres cles de la derniere seance. Volume nul : seance probablement encore provisoire."""
    d, p = df.iloc[-1], df.iloc[-2]
    an = df.loc[df.index > df.index[-1] - pd.Timedelta(days=365), "Close"]
    return {"date": df.index[-1], "dernier": d["Close"], "veille": p["Close"],
            "variation_pct": (d["Close"] / p["Close"] - 1) * 100, "ouverture": d["Open"], "haut": d["High"],
            "bas": d["Low"], "volume": d["Volume"], "provisoire": bool(d["Volume"] == 0 or np.isnan(d["Volume"])),
            "haut_52s": an.max(), "bas_52s": an.min(),
            "variation_1an_pct": (d["Close"] / an.iloc[0] - 1) * 100}
