"""Tableau de bord : derniers titres d'actualite sur le cacao, via Google News RSS.

Seuls le titre, la source, la date et le lien sont gardes, jamais le texte des articles.
Les titres sont des donnees affichees, pas des instructions.
"""
import json
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests

FLUX = {
    "fr": ("cacao (cours OR prix OR récolte OR Côte d'Ivoire OR Ghana)", "fr", "FR", "FR:fr"),
    "en": ("cocoa (futures OR prices OR harvest OR Ivory Coast OR Ghana)", "en-US", "US", "US:en"),
}
MOTS_CLES = re.compile(r"cacao|cocoa|chocolat|chocolate|cabosse|f[eè]ves?", re.IGNORECASE)
ENTETE = {"User-Agent": "Mozilla/5.0 (projet etudiant cacao)"}


def url(langue: str) -> str:
    requete, hl, gl, ceid = FLUX[langue]
    return f"https://news.google.com/rss/search?q={quote_plus(requete + ' when:14d')}&hl={hl}&gl={gl}&ceid={ceid}"


def lire_flux(texte: str, langue: str) -> list[dict]:
    racine = ET.fromstring(texte)
    sortie = []
    for item in racine.iter("item"):
        titre = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        if source and titre.endswith(f" - {source}"):
            titre = titre[: -len(source) - 3].strip()
        date = item.findtext("pubDate")
        sortie.append({"titre": titre, "source": source, "lien": (item.findtext("link") or "").strip(), "langue": langue,
                       "date": parsedate_to_datetime(date).isoformat() if date else None})
    return sortie


def collecter(chemin: Path, par_langue: int = 20) -> list[dict]:
    """Telecharge les deux flux ; en cas d'echec, garde le dernier cache et le signale."""
    articles, erreurs = [], []
    for langue in FLUX:
        try:
            r = requests.get(url(langue), headers=ENTETE, timeout=30)
            r.raise_for_status()
            articles += sorted(lire_flux(r.text, langue), key=lambda a: a["date"] or "", reverse=True)[:par_langue]
        except (requests.RequestException, ET.ParseError) as e:
            erreurs.append(f"{langue} : {str(e)[:120]}")
    if not articles and chemin.exists():
        ancien = json.loads(chemin.read_text(encoding="utf-8"))
        ancien["erreurs"] = erreurs
        return ancien["articles"]
    vus, uniques = set(), []
    for a in sorted(articles, key=lambda a: a["date"] or "", reverse=True):
        # Google renvoie aussi des articles sans rapport : on garde ceux dont le titre parle du cacao.
        if not MOTS_CLES.search(a["titre"]):
            continue
        if a["titre"].lower() not in vus:
            vus.add(a["titre"].lower())
            uniques.append(a)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps({"articles": uniques, "erreurs": erreurs}, ensure_ascii=False, indent=1), encoding="utf-8")
    return uniques
