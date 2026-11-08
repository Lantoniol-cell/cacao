"""Thematiques 4 et 5 : positions CFTC, attention Google, risque geopolitique, presse GDELT.

- CFTC : rapports hebdomadaires du cacao (code 073732), classement historique et desagrege.
- Google Trends : mensuel 2004-2026, via pytrends, bibliotheque non officielle. L'echelle
  0-100 depend de toute la periode : n'utiliser que des variations, pas le niveau.
- GPR : indice de risque geopolitique de Caldara et Iacoviello, quotidien et mensuel.
  Par pays, seuls le Bresil, l'Indonesie et le Perou sont couverts.
- GDELT : volume et ton de la presse, disponibles depuis 2017 seulement.

Sorties : data/raw/t4_investisseurs/ et data/raw/t5_geopolitique/

Usage : .venv/Scripts/python.exe -u scripts/31_collecter_investisseurs_geopolitique.py
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from pytrends.request import TrendReq

ROOT = Path(__file__).resolve().parents[1]
T4, T5 = ROOT / "data/raw/t4_investisseurs", ROOT / "data/raw/t5_geopolitique"
CFTC = {"legacy": "6dca-aqww", "desagrege": "72hh-3qpy"}
CODE = "073732"
TERMES = ["cocoa", "chocolate", "cocoa price"]
GPR = {"gpr_quotidien.xls": "data_gpr_daily_recent.xls", "gpr_mensuel.xls": "data_gpr_export.xls"}
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
REQUETES = {"cacao": "cocoa",
            "cacao_afrique": 'cocoa (Ghana OR "Ivory Coast")',
            "tensions_afrique": '(Ghana OR "Ivory Coast") (strike OR coup OR protest OR unrest OR smuggling)'}
ENTETE = {"User-Agent": "Mozilla/5.0"}
ESSAIS = 5
PAUSE_GDELT = 120


def obtenir(url: str, **k) -> requests.Response:
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(url, timeout=(20, 180), headers=ENTETE, **k)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"    essai {essai} echoue : {str(e)[:100]}", flush=True)
            time.sleep(15 * essai)
    raise RuntimeError(f"echec : {url}")


def cftc() -> None:
    for nom, jeu in CFTC.items():
        lignes, debut = [], 0
        while True:
            lot = obtenir(f"https://publicreporting.cftc.gov/resource/{jeu}.json",
                          params={"$where": f"cftc_contract_market_code='{CODE}'",
                                  "$order": "report_date_as_yyyy_mm_dd", "$limit": "5000", "$offset": str(debut)}).json()
            lignes += lot
            debut += len(lot)
            if len(lot) < 5000:
                break
        d = pd.DataFrame(lignes)
        d.to_csv(T4 / f"cftc_{nom}.csv", index=False)
        print(f"CFTC {nom} : {d.shape}, {d['report_date_as_yyyy_mm_dd'].min()[:10]} -> "
              f"{d['report_date_as_yyyy_mm_dd'].max()[:10]}", flush=True)


def trends() -> None:
    res = {}
    for terme in TERMES:
        t = TrendReq(hl="en-US", timeout=(10, 30))
        t.build_payload([terme], timeframe="2004-01-01 2026-10-31")
        res[terme] = t.interest_over_time()[terme]
        time.sleep(20)
    pd.DataFrame(res).to_csv(T4 / "google_trends_mensuel.csv")
    print("Trends :", pd.DataFrame(res).shape, flush=True)


def gpr() -> None:
    for sortie, nom in GPR.items():
        (T5 / sortie).write_bytes(obtenir(f"https://www.matteoiacoviello.com/gpr_files/{nom}").content)
    print("GPR : ok", flush=True)


def gdelt() -> None:
    for nom, requete in REQUETES.items():
        for mode, suffixe in (("timelinevol", "volume"), ("timelinetone", "ton")):
            cible = T5 / f"gdelt_{nom}_{suffixe}.csv"
            if cible.exists():
                continue
            time.sleep(PAUSE_GDELT)
            r = obtenir(GDELT, params={"query": requete, "mode": mode, "format": "json",
                                       "startdatetime": "20170101000000",
                                       "enddatetime": pd.Timestamp.today().strftime("%Y%m%d000000")})
            s = pd.DataFrame(r.json()["timeline"][0]["data"])
            s["date"] = pd.to_datetime(s["date"], format="%Y%m%dT%H%M%SZ")
            s.set_index("date")["value"].rename(f"{nom}_{suffixe}").to_csv(cible)
            print(f"GDELT {nom} {suffixe} : {len(s)} jours", flush=True)


def main() -> None:
    T4.mkdir(parents=True, exist_ok=True)
    T5.mkdir(parents=True, exist_ok=True)
    for etape in (gdelt,) if "--gdelt" in sys.argv else (cftc, gpr, gdelt, trends):
        try:
            etape()
        except (RuntimeError, KeyError, ValueError, requests.RequestException) as e:
            print(f"{etape.__name__} ECHEC : {str(e)[:200]}", flush=True)


if __name__ == "__main__":
    main()
