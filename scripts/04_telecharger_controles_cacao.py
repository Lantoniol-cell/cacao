"""Telecharge les prix mensuels du cacao servant de valeurs de controle.

- Banque mondiale, Pink Sheet : serie cacao issue de l'ICCO.
- FRED, PCOCOUSDM : prix mondial du cacao publie par le FMI.
Les fichiers sont enregistres tels quels dans data/raw/t1_marches/controle/.

Usage : .venv/Scripts/python.exe scripts/04_telecharger_controles_cacao.py
"""
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "t1_marches" / "controle"
PAGE_BM = "https://www.worldbank.org/en/research/commodity-markets"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCOCOUSDM"
ENTETES = {"User-Agent": "Mozilla/5.0 (projet academique cacao)"}


def telecharger(url: str, nom: str) -> None:
    r = requests.get(url, headers=ENTETES, timeout=(15, 60))
    r.raise_for_status()
    (DEST / nom).write_bytes(r.content)
    print(f"{nom} : {len(r.content) / 1e6:.2f} Mo depuis {url}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    try:
        page = requests.get(PAGE_BM, headers=ENTETES, timeout=60)
        page.raise_for_status()
        liens = re.findall(r'https?://[^"\']+CMO-Historical-Data-Monthly\.xlsx', page.text)
        if liens:
            telecharger(liens[0], "worldbank_CMO_monthly.xlsx")
        else:
            print("Lien du Pink Sheet introuvable sur la page de la Banque mondiale")
    except requests.RequestException as e:
        print(f"Banque mondiale indisponible : {e}")
    try:
        telecharger(FRED, "fred_PCOCOUSDM.csv")
    except requests.RequestException as e:
        print(f"FRED indisponible : {e}")


if __name__ == "__main__":
    main()
