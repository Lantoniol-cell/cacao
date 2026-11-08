"""Thematique 5 : agrege les fichiers bruts d'evenements GDELT 1.0 par pays et par jour.

L'API DOC refuse nos requetes (erreur 429), mais les fichiers bruts restent accessibles.
Ils couvrent 2005 (annuel), 2006 a mars 2013 (mensuel), puis chaque jour. Le fichier
quotidien contient aussi d'anciens evenements, qu'on ecarte pour ne garder que le jour
du fichier. Rien n'est conserve sauf l'agregat. Ces evenements ne parlent pas du cacao :
ils mesurent la tension dans les 9 pays, sans mot-cle, et leur nombre depend du volume de
presse numerisee. D'ou la colonne n_monde, pour raisonner en part du total.

Sortie : data/raw/t5_geopolitique/gdelt_evenements/<fichier>.csv

Usage : .venv/Scripts/python.exe -u scripts/32_collecter_gdelt_evenements.py [--test]
"""
import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/raw/t5_geopolitique/gdelt_evenements"
URL = "https://data.gdeltproject.org/events/{}"
PAYS = {"IV": "CIV", "GH": "GHA", "ID": "IDN", "EC": "ECU", "CM": "CMR", "BR": "BRA", "NI": "NGA", "PE": "PER", "DR": "DOM"}
COLONNES = {1: "date", 28: "racine", 29: "classe", 30: "goldstein", 33: "articles", 34: "ton", 51: "lieu"}
TRAVAILLEURS = 4
ESSAIS = 4


def fichiers() -> list[str]:
    jours = pd.date_range("2013-04-01", pd.Timestamp.today().normalize() - pd.Timedelta(days=1), freq="D")
    mois = pd.date_range("2006-01-01", "2013-03-01", freq="MS")
    return ["2005.zip"] + [f"{m:%Y%m}.zip" for m in mois] + [f"{j:%Y%m%d}.export.CSV.zip" for j in jours]


def agreger(nom: str) -> pd.DataFrame | None:
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(URL.format(nom), timeout=(20, 300))
            if r.status_code == 404:
                return None
            r.raise_for_status()
            break
        except requests.RequestException:
            time.sleep(10 * essai)
    else:
        raise RuntimeError("echec du telechargement")
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        with z.open(z.namelist()[0]) as f:
            d = pd.read_csv(f, sep="\t", header=None, usecols=list(COLONNES), dtype={51: str, 28: str},
                            on_bad_lines="skip", low_memory=False).rename(columns=COLONNES)
    d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d", errors="coerce")
    if "export" in nom:
        d = d[d["date"] == pd.Timestamp(nom[:8])]
    else:
        d = d[d["date"] >= "2005-01-01"]
    monde = d.groupby("date").size().rename("n_monde")
    d = d[d["lieu"].isin(PAYS)].assign(pays=lambda x: x["lieu"].map(PAYS))
    d["conflit"] = d["classe"].isin([3, 4])
    d["protestation"] = d["racine"].astype(str).str.lstrip("0") == "14"
    res = d.groupby(["date", "pays"]).agg(n=("ton", "size"), conflit=("conflit", "sum"), protestation=("protestation", "sum"),
                                          goldstein=("goldstein", "mean"), ton=("ton", "mean"), articles=("articles", "sum"))
    return res.reset_index().merge(monde.reset_index(), on="date")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    tous = fichiers()
    if "--test" in sys.argv:
        for nom in ("200601.zip", "20170101.export.CSV.zip"):
            t = time.time()
            r = agreger(nom)
            print(nom, f"{time.time() - t:.0f} s", r.shape)
            print(r[r["pays"] == "CIV"].head(2).round(2).to_string())
        return
    a_faire = [n for n in tous if not (DEST / f"{n}.csv").exists()]
    print(f"{len(a_faire)} fichiers a faire sur {len(tous)}", flush=True)
    faits, absents, echecs, t0 = 0, [], [], time.time()
    with ThreadPoolExecutor(TRAVAILLEURS) as ex:
        travaux = {ex.submit(agreger, n): n for n in a_faire}
        for f in as_completed(travaux):
            n = travaux[f]
            try:
                r = f.result()
                if r is None:
                    absents.append(n)
                else:
                    r.to_csv(DEST / f"{n}.csv", index=False)
                faits += 1
                if faits % 100 == 0:
                    print(f"{faits}/{len(a_faire)}, {(time.time() - t0) / 60:.0f} min", flush=True)
            except (RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as e:
                echecs.append(n)
                print(f"{n} ECHEC : {str(e)[:100]}", flush=True)
    print(f"Termine : {faits} fichiers, {len(absents)} absents : {absents[:20]}, {len(echecs)} echecs : {echecs[:20]}")


if __name__ == "__main__":
    main()
