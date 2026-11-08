"""Thematique 2 : collecte les previsions de pluie GEFS a 1-10 jours sur les 349 points.

Membre de controle c00, emission de 00 UTC. Trois regimes :
- 2005 a 2019 : reprevisions GEFSv12, produites apres coup. Ce ne sont donc pas les
  previsions que le marche a vues, a declarer dans le rapport.
- 2020-01-01 a 2020-09-22 : archive operationnelle, ancien format pgrb2a.
- depuis 2020-09-23 : archive operationnelle, format pgrb2s a 0,25 degre.

On ne lit que les cumuls de 6 heures, sommes par jour d'echeance. Rien de global n'est
garde. La colonne d'un point suit l'ordre de points_meteo_retenus.parquet, copie dans
points.txt. Le script va du plus recent au plus ancien et reprend ou il s'est arrete.

Sorties : data/raw/t2_climat/gefs/AAAAMMJJ.npy, tableau 10 x 349 en mm par jour d'echeance ;
data/raw/t2_climat/gefs_tmax/AAAAMMJJ.npy avec --tmax, maximum du jour en kelvins

Usage : .venv/Scripts/python.exe -u scripts/28_collecter_previsions_gefs.py [--test] [--tmax]
"""
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import eccodes
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
REFO = "https://noaa-gefs-retrospective.s3.amazonaws.com/GEFSv12/reforecast"
PDS = "https://noaa-gefs-pds.s3.amazonaws.com"
DEBUT = "2005-01-01"
LIMITE_REFO = pd.Timestamp("2019-12-31")
LIMITE_ANCIEN = pd.Timestamp("2020-09-22")
JOURS = 10
TRAVAILLEURS = 6
ESSAIS = 4
MOTIFS = {"pluie": (re.compile(r"APCP:surface:(\d+)-(\d+) hour acc"), "apcp_sfc", "gefs"),
          "tmax": (re.compile(r"TMAX:2 m above ground:(\d+)-(\d+) hour max"), "tmax_2m", "gefs_tmax")}
VARIABLE = "tmax" if "--tmax" in sys.argv else "pluie"
ACCUM, FICHIER, DOSSIER = MOTIFS[VARIABLE]
VERROU = threading.Lock()
ABSENTES = {"2020-08-28": (168,)}  # echeance absente de l'archive NOAA (404 sur le GRIB et son index)
DEST = ROOT / "data/raw/t2_climat" / DOSSIER


def obtenir(url: str, debut: int | None = None, fin: int | None = None) -> bytes:
    entete = {"Range": f"bytes={debut}-{'' if fin is None else fin}"} if debut is not None else None
    for essai in range(1, ESSAIS + 1):
        try:
            r = requests.get(url, headers=entete, timeout=(20, 120))
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            if getattr(e.response, "status_code", None) == 404:
                raise
            time.sleep(5 * essai)
    raise RuntimeError(f"echec : {url}")


def enregistrements(idx: str) -> list[tuple[int, int | None, int, int]]:
    """Renvoie (debut, fin, heure a, heure b) des cumuls de 6 heures de pluie."""
    lignes = idx.strip().splitlines()
    res = []
    for n, ligne in enumerate(lignes):
        m = ACCUM.search(ligne)
        if m and int(m[2]) - int(m[1]) == 6 and int(m[2]) <= JOURS * 24:
            debut = int(ligne.split(":")[1])
            fin = int(lignes[n + 1].split(":")[1]) - 1 if n + 1 < len(lignes) else None
            res.append((debut, fin, int(m[1]), int(m[2])))
    return res


def lire(message: bytes, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    g = eccodes.codes_new_from_message(message)
    try:
        ni, nj = eccodes.codes_get(g, "Ni"), eccodes.codes_get(g, "Nj")
        la0 = eccodes.codes_get(g, "latitudeOfFirstGridPointInDegrees")
        lo0 = eccodes.codes_get(g, "longitudeOfFirstGridPointInDegrees")
        dla = eccodes.codes_get(g, "jDirectionIncrementInDegrees")
        dlo = eccodes.codes_get(g, "iDirectionIncrementInDegrees")
        signe = 1 if eccodes.codes_get(g, "jScansPositively") else -1
        v = eccodes.codes_get_values(g).reshape(nj, ni)
    finally:
        eccodes.codes_release(g)
    j = np.rint((lat - la0) / (signe * dla)).astype(int)
    i = np.rint(((lon % 360) - lo0) / dlo).astype(int) % ni
    return v[j, i]


def messages(date: pd.Timestamp):
    """Produit (heure de fin, octets du message) pour une date d'emission."""
    j = date.strftime("%Y%m%d")
    if date <= LIMITE_REFO:
        url = f"{REFO}/{date.year}/{j}00/c00/Days:1-10/{FICHIER}_{j}00_c00.grib2"
        rec = enregistrements(obtenir(url + ".idx").decode())
        brut = obtenir(url)
        uniques = {}  # 3 fichiers contiennent des messages en double, a ne pas sommer deux fois
        for debut, fin, _, b in rec:
            octets = brut[debut: None if fin is None else fin + 1]
            if uniques.setdefault(b, octets) != octets:
                raise RuntimeError(f"doublon different a l'echeance {b}")
        yield from uniques.items()
        return
    for h in range(6, JOURS * 24 + 1, 6):
        if h in ABSENTES.get(str(date.date()), ()):
            continue
        if date <= LIMITE_ANCIEN:
            url = f"{PDS}/gefs.{j}/00/pgrb2a/gec00.t00z.pgrb2af{h:02d}"
        else:
            url = f"{PDS}/gefs.{j}/00/atmos/pgrb2sp25/gec00.t00z.pgrb2s.0p25.f{h:03d}"
        rec = [r for r in enregistrements(obtenir(url + ".idx").decode()) if r[3] == h]
        yield h, obtenir(url, rec[0][0], rec[0][1])


def traiter(date: pd.Timestamp, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    res = np.full((JOURS, len(lat)), -np.inf if VARIABLE == "tmax" else 0.0, dtype=np.float32)
    vus = 0
    for b, octets in messages(date):
        with VERROU:  # le processus s'arrete sans message si ecCodes decode en parallele
            v = lire(octets, lat, lon).astype(np.float32)
            j = (b - 1) // 24
            res[j] = np.maximum(res[j], v) if VARIABLE == "tmax" else res[j] + v
        vus += 1
    absentes = ABSENTES.get(str(date.date()), ())
    if vus != JOURS * 4 - len(absentes):
        raise RuntimeError(f"{vus} cumuls au lieu de {JOURS * 4 - len(absentes)}")
    for h in absentes:
        res[(h - 1) // 24] = np.nan  # jour incomplet : laisse vide, jamais reconstitue
    return res


def main() -> None:
    points = pd.read_parquet(ROOT / "data/interim/points_meteo_retenus.parquet")
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "points.txt").write_text("\n".join(points["id"]), encoding="utf-8")
    lat, lon = points["lat"].to_numpy(), points["lon"].to_numpy()
    if "--test" in sys.argv:
        for d in ("2024-06-15", "2020-03-01", "2015-04-11"):
            t = time.time()
            r = traiter(pd.Timestamp(d), lat, lon)
            print(d, f"{time.time() - t:.0f} s", r.shape, "nan", int(np.isnan(r).sum()), "max", round(float(r.max()), 1),
                  "mediane cumul 10 j", round(float(np.median(r.sum(axis=0))), 1), flush=True)
        return

    dates = pd.date_range(DEBUT, pd.Timestamp.today().normalize() - pd.Timedelta(days=1), freq="D")[::-1]
    a_faire = [d for d in dates if not (DEST / f"{d:%Y%m%d}.npy").exists()]
    print(f"{len(a_faire)} dates a faire sur {len(dates)}", flush=True)
    t0, faits, echecs = time.time(), 0, []
    lot = iter(a_faire)
    with ThreadPoolExecutor(TRAVAILLEURS) as ex:
        en_cours = {}
        while True:
            while len(en_cours) < TRAVAILLEURS * 2:
                d = next(lot, None)
                if d is None:
                    break
                en_cours[ex.submit(traiter, d, lat, lon)] = d
            if not en_cours:
                break
            f = next(as_completed(en_cours))
            d = en_cours.pop(f)
            try:
                np.save(DEST / f"{d:%Y%m%d}.npy", f.result())
                faits += 1
                if faits % 25 == 0:
                    print(f"{faits}/{len(a_faire)}, {d.date()}, {(time.time() - t0) / 60:.0f} min", flush=True)
            except (RuntimeError, requests.RequestException, eccodes.CodesInternalError, IndexError) as e:
                echecs.append(str(d.date()))
                print(f"{d.date()} ECHEC : {str(e)[:100]}", flush=True)
    print(f"Termine : {faits} dates, {len(echecs)} echecs : {echecs[:50]}")
    (DEST / "echecs.txt").write_text("\n".join(echecs), encoding="utf-8")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
