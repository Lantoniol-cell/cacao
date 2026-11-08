"""Thematique 1 : telecharge les series Yahoo Finance et controle leur qualite.

Les valeurs sont enregistrees telles que recues, un CSV par ticker, dans
data/raw/t1_marches/. Un ticker sans donnees est signale, jamais remplace.
Sortie du controle : outputs/metriques/t1_couverture.csv

Usage : .venv/Scripts/python.exe scripts/01_collecter_t1_marches.py
"""
import sys
from pathlib import Path

import pandas as pd
import yaml
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
BRUT = ROOT / "data" / "raw" / "t1_marches"
SORTIE = ROOT / "outputs" / "metriques" / "t1_couverture.csv"


def nom_fichier(ticker: str) -> str:
    return ticker.replace("=", "_").replace("^", "idx_") + ".csv"


def controler(groupe, ticker, description, df) -> dict:
    ligne = {"groupe": groupe, "ticker": ticker, "description": description}
    if df.empty or df["Close"].dropna().empty:
        return ligne | {"statut": "AUCUNE DONNEE"}
    close = df["Close"].dropna()
    rendement = close.pct_change().abs()
    return ligne | {
        "statut": "ok",
        "debut": close.index.min().date(),
        "fin": close.index.max().date(),
        "n_jours": len(close),
        "nan_close": int(df["Close"].isna().sum()),
        "min": round(float(close.min()), 4),
        "date_min": close.idxmin().date(),
        "max": round(float(close.max()), 4),
        "date_max": close.idxmax().date(),
        "n_valeurs_distinctes": int(close.nunique()),
        "plus_grand_saut_pct": round(float(rendement.max()) * 100, 1),
        "date_saut": rendement.idxmax().date(),
        "ecart_max_jours": int(close.index.to_series().diff().dt.days.max()),
    }


def main() -> None:
    config = yaml.safe_load((ROOT / "config" / "t1_marches.yaml").read_text(encoding="utf-8"))
    BRUT.mkdir(parents=True, exist_ok=True)
    lignes = []
    for groupe, series in config["series"].items():
        for ticker, description in series.items():
            print(f"{ticker} ...", flush=True)
            df = yf.Ticker(ticker).history(start=config["debut"], auto_adjust=False, actions=False)
            if not df.empty:
                df.index = df.index.tz_localize(None).normalize()
                df.index.name = "date"
                df.to_csv(BRUT / nom_fichier(ticker))
            lignes.append(controler(groupe, ticker, description, df))

    rapport = pd.DataFrame(lignes)
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    rapport.to_csv(SORTIE, index=False)
    pd.set_option("display.width", 220, "display.max_columns", None)
    print(rapport.drop(columns="description").to_string(index=False))
    sys.exit(1 if (rapport["statut"] != "ok").any() else 0)


if __name__ == "__main__":
    main()
