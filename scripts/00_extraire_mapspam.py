"""Extrait tous les ZIP MapSPAM restants, sans jamais rien supprimer.

Les ZIP de premier niveau ont deja ete decompresses a la main dans
<dossier MapSPAM>/<millesime au nom long>/. Ce script parcourt ces dossiers et
extrait chaque ZIP encore present vers extrait/<millesime court>/, pour rester
sous la limite de 260 caracteres des chemins Windows.

- Aucun fichier source n'est modifie ni supprime.
- Les CRC sont controles par zipfile pendant l'extraction.
- Un ZIP en echec est note et n'arrete pas le reste.
- Relancer le script saute les ZIP deja termines.

Usage : python scripts/00_extraire_mapspam.py
"""
import csv
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "MapSPAM zones de production"
CIBLE = SOURCE / "extrait"
MARGE_DISQUE = 50e9  # espace a garder libre apres extraction, en octets
MARQUEUR = ".extraction_terminee"


def nom_millesime(dossier: str) -> str:
    annee = re.search(r"for (\d{4})", dossier).group(1)
    return f"spam{annee}_ssa" if annee == "2017" else f"spam{annee}"


def destination(zip_path: Path) -> Path:
    rel = zip_path.relative_to(SOURCE)
    sous_dossiers = rel.parts[1:-1]
    return CIBLE.joinpath(nom_millesime(rel.parts[0]), *sous_dossiers,
                          zip_path.name.removesuffix(".zip"))


def extraire(zip_path: Path, dest: Path, echecs: list) -> None:
    """Extrait un ZIP puis, recursivement, les ZIP qu'il contenait."""
    if (dest / MARQUEUR).exists():
        return
    print(f"  {dest.relative_to(CIBLE)}", flush=True)
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(dest)
        for interne in sorted(dest.rglob("*.zip")):
            extraire(interne, interne.with_name(interne.name.removesuffix(".zip")), echecs)
        (dest / MARQUEUR).touch()
    except (OSError, zipfile.BadZipFile) as e:
        print(f"  ECHEC {zip_path.name} : {e}", flush=True)
        echecs.append((zip_path.name, str(e)))


def main() -> None:
    zips = sorted(p for p in SOURCE.rglob("*.zip") if CIBLE not in p.parents)
    print(f"{len(zips)} ZIP trouves", flush=True)

    a_faire = [z for z in zips if not (destination(z) / MARQUEUR).exists()]
    besoin = 0
    for z_path in a_faire:
        with zipfile.ZipFile(z_path) as z:
            besoin += sum(i.file_size for i in z.infolist())
    libre = shutil.disk_usage(SOURCE).free
    print(f"{len(a_faire)} a extraire : besoin {besoin/1e9:.1f} Go, "
          f"libre {libre/1e9:.1f} Go", flush=True)
    if libre - besoin < MARGE_DISQUE:
        sys.exit("Arret : espace disque insuffisant")

    echecs = []
    for z_path in a_faire:
        extraire(z_path, destination(z_path), echecs)

    manifeste = CIBLE / "manifeste_extraction.csv"
    fichiers = sorted(p for p in CIBLE.rglob("*") if p.is_file()
                      and p.name != MARQUEUR and p != manifeste)
    with manifeste.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["chemin", "octets"])
        for p in fichiers:
            w.writerow([p.relative_to(CIBLE).as_posix(), p.stat().st_size])

    total = sum(p.stat().st_size for p in fichiers)
    print(f"\nTermine : {len(fichiers)} fichiers, {total/1e9:.1f} Go, "
          f"{len(echecs)} echec(s)", flush=True)
    for nom, err in echecs:
        print(f"  {nom} : {err}", flush=True)
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
