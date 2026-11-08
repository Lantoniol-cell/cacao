"""Telecharge les tableaux de production publics des bulletins ICCO (QBCS).

Les PDF sont conserves tels quels dans data/raw/t3_offre/icco/.
Une edition absente du site est notee, jamais remplacee.

Usage : .venv/Scripts/python.exe scripts/09_collecter_icco_production.py
"""
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t3_offre/icco"
BASE = "https://www.icco.org/wp-content/uploads/Production_QBCS-{v}-No.-{n}.pdf"
VOLUMES = ["XLV", "XLVI", "XLVII", "XLVIII", "XLIX", "L", "LI", "LII"]
ENTETES = {"User-Agent": "Mozilla/5.0 (projet academique cacao)"}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    trouves = 0
    for v in VOLUMES:
        for n in range(1, 5):
            nom = f"Production_QBCS-{v}-No.-{n}.pdf"
            cible = DEST / nom
            if cible.exists():
                trouves += 1
                continue
            try:
                r = requests.get(BASE.format(v=v, n=n), headers=ENTETES, timeout=(15, 60))
            except requests.RequestException as e:
                print(f"{nom} : erreur reseau {e}")
                continue
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                cible.write_bytes(r.content)
                trouves += 1
                print(f"{nom} : {len(r.content) / 1e3:.0f} ko")
            else:
                print(f"{nom} : absent ({r.status_code})")
    print(f"\n{trouves} editions disponibles")


if __name__ == "__main__":
    main()
