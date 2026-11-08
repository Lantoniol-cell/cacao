"""Phase 1 : verifie que chaque jeu de donnees attendu est present et complet.

Sortie : outputs/metriques/inventaire_donnees.csv

Usage : .venv/Scripts/python.exe scripts/34_inventaire_donnees.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/raw"
POINTS = 349
ATTENDU_GEFS = 7980
pd.set_option("display.width", 220, "display.max_columns", None, "display.max_colwidth", 60)


def dossier(famille, nom, chemin, motif, attendu):
    n = len(list((R / chemin).glob(motif))) if (R / chemin).exists() else 0
    return {"famille": famille, "donnee": nom, "chemin": chemin, "attendu": attendu, "present": n,
            "etat": "complet" if n >= attendu else "incomplet"}


def fichier(famille, nom, chemin):
    p = ROOT / chemin
    ok = p.exists() and p.stat().st_size > 0
    return {"famille": famille, "donnee": nom, "chemin": chemin, "attendu": 1, "present": int(ok),
            "etat": "complet" if ok else "absent"}


def main() -> None:
    lignes = [
        dossier("marche_finance", "Marches Yahoo", "t1_marches", "*.csv", 19),
        fichier("marche_finance", "Prix Banque mondiale", "data/raw/t1_marches/controle/worldbank_CMO_monthly.xlsx"),
        dossier("climat", "NASA POWER 7 variables", "t2_climat/power", "*.csv", POINTS),
        dossier("climat", "NASA rayonnement et vent", "t2_climat/power_complement", "*.csv", POINTS),
        dossier("climat", "ERA5 pluie", "t2_climat/era5", "*.csv", POINTS),
        dossier("climat", "ERA5 controle", "t2_climat/era5_controle", "*.csv", 14),
        dossier("climat", "CHIRPS points", "t2_climat/chirps", "*.csv", POINTS),
        fichier("climat", "ENSO ONI", "data/raw/t2_climat/oni.txt"),
        dossier("climat", "GEFS pluie", "t2_climat/gefs", "*.npy", ATTENDU_GEFS),
        dossier("climat", "GEFS temperature maximale", "t2_climat/gefs_tmax", "*.npy", ATTENDU_GEFS),
        fichier("climat", "Indices GEFS corriges", "data/processed/gefs_pays.parquet"),
        dossier("biodiversite", "Incendies FIRMS 2005-2025", "t2_climat/firms", "*.csv", 189),
        dossier("biodiversite", "Incendies FIRMS 2026", "t2_climat/firms", "*_2026.csv", 9),
        fichier("biodiversite", "Pesticides FAOSTAT", "data/raw/t3_offre/faostat_pesticides.csv"),
        fichier("biodiversite", "Azote FAOSTAT", "data/raw/t3_offre/faostat_engrais.csv"),
        fichier("production_offre", "FAOSTAT cacao", "data/raw/t3_offre/faostat_cacao.csv"),
        fichier("production_offre", "ICCO editions (sensibilite)", "data/interim/icco_production_editions.csv"),
        fichier("investisseurs_biais", "CFTC historique", "data/raw/t4_investisseurs/cftc_legacy.csv"),
        fichier("investisseurs_biais", "CFTC desagrege", "data/raw/t4_investisseurs/cftc_desagrege.csv"),
        fichier("investisseurs_biais", "Google Trends", "data/raw/t4_investisseurs/google_trends_mensuel.csv"),
        # Les 2 series de tensions par mots-cles sont abandonnees : les fichiers bruts les couvrent.
        dossier("investisseurs_biais", "GDELT presse cacao", "t5_geopolitique", "gdelt_cacao*.csv", 4),
        fichier("geopolitique", "GPR quotidien", "data/raw/t5_geopolitique/gpr_quotidien.xls"),
        fichier("geopolitique", "GPR mensuel", "data/raw/t5_geopolitique/gpr_mensuel.xls"),
        dossier("geopolitique", "GDELT evenements", "t5_geopolitique/gdelt_evenements", "*.csv", 5000),
        fichier("geopolitique", "Base d'evenements", "config/evenements.csv"),
        fichier("reference", "Points meteo", "data/interim/points_meteo_retenus.parquet"),
        fichier("reference", "Poids FAOSTAT", "outputs/metriques/t2_poids_pays.csv"),
        fichier("traite", "Dataset quotidien", "data/processed/dataset_quotidien.parquet"),
    ]
    t = pd.DataFrame(lignes)
    t.to_csv(ROOT / "outputs/metriques/inventaire_donnees.csv", index=False)
    print(t[["famille", "donnee", "attendu", "present", "etat"]].to_string(index=False))
    print(f"\n{(t['etat'] == 'complet').sum()} complets sur {len(t)}")
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    print(f"Dataset : {d.shape}, {d.index.min().date()} -> {d.index.max().date()}, doublons de date : {int(d.index.duplicated().sum())}")


if __name__ == "__main__":
    main()
