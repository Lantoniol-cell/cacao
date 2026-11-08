"""Actualisation quotidienne du tableau de bord : cours, indicateurs, actualites, puis site.

Etapes :
1. cours CC=F (data/live/cc_f.parquet), ajout des nouvelles seances et controles ;
2. indicateurs du jour (data/live/indicateurs.json et indicateurs_historique.parquet) :
   HAR a 5 et 20 seances, ecarts aux MM60 et MM120, regime de volatilite ;
3. actualites Google News (data/live/actualites.json) ;
4. rendu du site Quarto dans docs/, sauf avec --sans-rendu ;
5. envoi du seul dossier docs/ sur GitHub, sauf avec --sans-envoi (voir publier_docs).
Chaque execution ajoute une ligne a data/live/journal.csv.

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/40_actualiser_marche.py [--sans-rendu]
"""
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cacao.actualites import collecter  # noqa: E402
from cacao.indicateurs import ecarts_moyennes, prevision_har, regime  # noqa: E402
from cacao.marche import avertissements, mettre_a_jour, resume  # noqa: E402

LIVE = ROOT / "data/live"
QUARTO = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Positron/resources/app/quarto/bin/quarto.exe"
GIT = Path(r"C:\Program Files\Git\cmd\git.exe")


def journal(etat: str, detail: str) -> None:
    f = LIVE / "journal.csv"
    ligne = pd.DataFrame([{"execution": datetime.now().isoformat(timespec="seconds"), "etat": etat, "detail": detail[:300]}])
    ligne.to_csv(f, mode="a", header=not f.exists(), index=False)


def main() -> None:
    LIVE.mkdir(parents=True, exist_ok=True)
    df, ajout = mettre_a_jour(LIVE / "cc_f.parquet")
    close = df["Close"]
    r = resume(df)
    print(f"Cours : {len(df)} seances, {ajout} ajoutees, derniere {r['date'].date()} a {r['dernier']:.0f} ({r['variation_pct']:+.2f} %)"
          + (" PROVISOIRE" if r["provisoire"] else ""), flush=True)

    # Le HAR et le regime sont calcules a la derniere seance definitive.
    base = close.iloc[:-1] if r["provisoire"] else close
    har = {h: prevision_har(base, h) for h in (5, 20)}
    e = ecarts_moyennes(close)
    g = regime(base)
    histo = pd.concat([df, e, g], axis=1)
    histo.to_parquet(LIVE / "indicateurs_historique.parquet")
    etat = {"maj": datetime.now().isoformat(timespec="seconds"), "date_cours": str(r["date"].date()),
            "date_indicateurs": str(base.index[-1].date()), "resume": {k: (str(v.date()) if hasattr(v, "date") else v) for k, v in r.items()},
            "har": har, "ecart_mm60_pct": float(e["ecart_mm60_pct"].iloc[-1]), "ecart_mm120_pct": float(e["ecart_mm120_pct"].iloc[-1]),
            "regime_agite": bool(g["agite"].iloc[-1] == 1), "vol60": float(g["vol60"].iloc[-1]), "seuil_regime": float(g["seuil"].iloc[-1]),
            "avertissements": avertissements(df)}
    (LIVE / "indicateurs.json").write_text(json.dumps(etat, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"HAR : 5 seances {har[5]['prevision']:.1%}, 20 seances {har[20]['prevision']:.1%} ; "
          f"ecart MM120 {etat['ecart_mm120_pct']:+.1f} % ; regime {'agite' if etat['regime_agite'] else 'calme'}", flush=True)

    articles = collecter(LIVE / "actualites.json")
    print(f"Actualites : {len(articles)} titres", flush=True)

    if "--sans-rendu" not in sys.argv:
        env = os.environ | {"QUARTO_PYTHON": sys.executable}
        res = subprocess.run([str(QUARTO), "render", str(ROOT / "site")], env=env, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError("Rendu Quarto en echec : " + res.stderr[-500:])
        print("Site rendu dans docs/", flush=True)
    envoi = publier_docs() if "--sans-envoi" not in sys.argv and "--sans-rendu" not in sys.argv else "non demande"
    print(f"Envoi GitHub : {envoi}", flush=True)
    journal("ok", f"cours {r['date'].date()} ; {ajout} seances ajoutees ; {len(articles)} actualites ; envoi : {envoi}")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(GIT), *args], cwd=ROOT, capture_output=True, text=True, env=os.environ | {"GIT_TERMINAL_PROMPT": "0"})


def publier_docs() -> str:
    """Envoie sur GitHub le seul dossier docs/ (accord de l'utilisatrice le 2026-11-08).

    Regle de securite : rien d'autre que docs/ ne part sans controle. On commite uniquement
    docs/, puis on verifie que tous les commits en attente d'envoi ne touchent que docs/.
    Sinon, l'envoi est annule et note dans le journal.
    """
    if not GIT.exists():
        return "git introuvable"
    git("add", "docs")
    if git("diff", "--cached", "--quiet", "--", "docs").returncode != 0:
        res = git("commit", "-m", f"Actualisation quotidienne du site ({datetime.now():%Y-%m-%d})", "--", "docs")
        if res.returncode != 0:
            return "echec du commit : " + res.stderr.strip()[:150]
    git("fetch", "--quiet", "origin")
    fichiers = git("diff", "--name-only", "origin/main..HEAD").stdout.split()
    if not fichiers:
        return "rien de nouveau"
    hors_docs = [f for f in fichiers if not f.startswith("docs/")]
    if hors_docs:
        return f"annule : commits en attente hors de docs/ ({', '.join(hors_docs[:3])})"
    res = git("push", "origin", "main")
    return "envoye" if res.returncode == 0 else "echec : " + res.stderr.strip()[:150]


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # le journal garde la trace de l'echec, puis l'erreur remonte
        journal("echec", f"{type(exc).__name__} : {exc}")
        traceback.print_exc()
        sys.exit(1)
