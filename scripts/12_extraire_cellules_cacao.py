"""Extrait de MapSPAM les cellules de cacao et leur densite dans chaque pays.

MapSPAM sert uniquement a localiser et a pondérer a l'interieur d'un pays. Les
volumes nationaux viennent de FAOSTAT : la densite est une part, pas un volume.

Sorties :
- data/interim/mapspam_cacao.parquet : cellules de 5 minutes d'arc
- data/interim/points_meteo_cacao.parquet : mailles de 0,25 degre

Usage : .venv/Scripts/python.exe scripts/12_extraire_cellules_cacao.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTRAIT = ROOT / "MapSPAM zones de production/extrait"
PAS = 0.25
PAYS = {"Cote dIvoire": "CIV", "Ghana": "GHA", "Indonesia": "IDN", "Ecuador": "ECU", "Cameroon": "CMR",
        "Brazil": "BRA", "Nigeria": "NGA", "Peru": "PER", "Dominican Republic": "DOM"}
ISO = list(PAYS.values())
pd.set_option("display.width", 200, "display.max_columns", None, "display.max_rows", 100)


def fichier(nom: str) -> Path:
    return next(p for p in EXTRAIT.rglob(nom) if p.is_file())


def lire_2005() -> pd.DataFrame:
    d = pd.read_csv(fichier("spam2005V3r2_global_P_TA.csv"), usecols=["iso3", "alloc_key", "coco_a"],
                    dtype={"alloc_key": str}, encoding="latin-1")
    xy = pd.read_csv(fichier("cell5m_allockey_xy.csv"), usecols=["x", "y", "alloc_key"],
                     dtype={"alloc_key": str})
    d = d[d["coco_a"] > 0].merge(xy, on="alloc_key", how="left")
    if d["x"].isna().any():
        raise ValueError(f"{int(d['x'].isna().sum())} cellules 2005 sans coordonnees")
    return d.rename(columns={"iso3": "pays", "coco_a": "production_t"})[["pays", "x", "y", "production_t"]]


def lire_2010() -> pd.DataFrame:
    d = pd.read_csv(fichier("spam2010V2r0_global_P_TA.csv"), usecols=["iso3", "x", "y", "coco_a"],
                    encoding="latin-1")
    return d[d["coco_a"] > 0].rename(columns={"iso3": "pays", "coco_a": "production_t"})


def lire_2017() -> pd.DataFrame:
    """Afrique subsaharienne uniquement."""
    d = pd.read_csv(fichier("spam2017V2r1_SSA_P_TA.csv"), usecols=["iso3", "x", "y", "coco_a"],
                    encoding="latin-1")
    return d[d["coco_a"] > 0].rename(columns={"iso3": "pays", "coco_a": "production_t"})


def lire_2020() -> pd.DataFrame:
    d = pd.read_csv(fichier("spam2020V2r2_global_P_TA.csv"), usecols=["x", "y", "ADM0_NAME", "ADM1_NAME", "coco"],
                    encoding="utf-8", encoding_errors="replace")
    d = d[d["coco"] > 0]
    return pd.DataFrame({"pays": d["ADM0_NAME"].map(PAYS).fillna(d["ADM0_NAME"]), "x": d["x"], "y": d["y"],
                         "adm1": d["ADM1_NAME"], "production_t": d["coco"]})


def maille(s: pd.Series) -> pd.Series:
    return (np.floor(s / PAS) * PAS + PAS / 2).round(3)


def main() -> None:
    cellules = pd.concat([lire_2005().assign(millesime=2005), lire_2010().assign(millesime=2010),
                          lire_2017().assign(millesime=2017), lire_2020().assign(millesime=2020)],
                         ignore_index=True)
    cellules["pays"] = cellules["pays"].str.strip('"')
    cellules["densite"] = cellules["production_t"] / cellules.groupby(["millesime", "pays"])["production_t"].transform("sum")
    cellules.to_parquet(ROOT / "data/interim/mapspam_cacao.parquet")

    cellules["lon"], cellules["lat"] = maille(cellules["x"]), maille(cellules["y"])
    points = cellules.groupby(["millesime", "pays", "lat", "lon"], as_index=False)[["production_t", "densite"]].sum()
    points.to_parquet(ROOT / "data/interim/points_meteo_cacao.parquet")

    print("Cellules par millesime :", cellules.groupby("millesime").size().to_dict())
    print("\n=== Controle : somme des densites par pays (doit valoir 1) ===")
    print(points.groupby(["millesime", "pays"])["densite"].sum().round(6).agg(["min", "max"]).to_dict())

    print(f"\n=== Points necessaires, mailles de {PAS} degre, millesime 2020 ===")
    lignes = []
    for iso in ISO:
        p = points[(points["millesime"] == 2020) & (points["pays"] == iso)].sort_values("densite", ascending=False)
        cum = p["densite"].cumsum()
        lignes.append({"pays": iso, "cellules_5min": int(((cellules["millesime"] == 2020) & (cellules["pays"] == iso)).sum()),
                       "mailles": len(p), "pour_80pct": int((cum < 0.80).sum() + 1),
                       "pour_90pct": int((cum < 0.90).sum() + 1), "pour_95pct": int((cum < 0.95).sum() + 1)})
    t = pd.DataFrame(lignes).set_index("pays")
    print(t)
    print("Total :", t.sum().to_dict())

    print("\n=== Stabilite de la geographie : part commune de la densite (100 % = identique) ===")
    lignes = []
    for iso in ISO:
        p = points[points["pays"] == iso].pivot_table(index=["lat", "lon"], columns="millesime",
                                                      values="densite", fill_value=0)
        ligne = {"pays": iso}
        for a, b in [(2005, 2010), (2010, 2017), (2017, 2020), (2010, 2020), (2005, 2020)]:
            ligne[f"{a}-{b}"] = round((1 - 0.5 * (p[a] - p[b]).abs().sum()) * 100, 1) if a in p and b in p else None
        lignes.append(ligne)
    print(pd.DataFrame(lignes).to_string(index=False))

    print("\n=== Centre de gravite de la production (latitude, longitude) ===")
    def centre(d: pd.DataFrame) -> str:
        return f"{(d['y'] * d['densite']).sum():6.2f}, {(d['x'] * d['densite']).sum():7.2f}"
    print(cellules[cellules["pays"].isin(ISO)].groupby(["pays", "millesime"]).apply(
        centre, include_groups=False).unstack().to_string())

    print("\n=== Bresil 2020 : principaux Etats (%) ===")
    bra = cellules[(cellules["millesime"] == 2020) & (cellules["pays"] == "BRA")]
    print((bra.groupby("adm1")["densite"].sum().sort_values(ascending=False).head(6) * 100).round(1).to_string())
    print("\n=== Cameroun 2020 : regions (%) ===")
    cmr = cellules[(cellules["millesime"] == 2020) & (cellules["pays"] == "CMR")]
    print((cmr.groupby("adm1")["densite"].sum().sort_values(ascending=False) * 100).round(1).to_string())

    print("\n=== Indonesie 2020 : principales provinces ===")
    idn = cellules[(cellules["millesime"] == 2020) & (cellules["pays"] == "IDN")]
    prov = idn.groupby("adm1")["densite"].sum().sort_values(ascending=False) * 100
    print(prov.head(12).round(1).to_string())
    print(f"Sulawesi (nom de province contenant 'Sulawesi') : {prov[prov.index.str.contains('Sulawesi')].sum():.1f} %")
    print("Toutes les provinces :", list(prov.index))


if __name__ == "__main__":
    main()
