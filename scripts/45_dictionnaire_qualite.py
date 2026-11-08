"""Documentation des donnees : dictionnaire des 328 colonnes et controle qualite.

Le dictionnaire est construit par des regles explicites sur les noms de colonnes. Chaque
regle reprend ce que font les scripts de collecte (01 a 36), la grille (06) et le dataset
(29), avec leurs delais. Les periodes, completudes et controles sont calcules sur les
donnees reelles. Ce qui n'est pas documente dans le code est marque « Non documente ».

L'interet pour la prevision n'est jamais attribue a la main : on rapporte ce qui a ete
mesure (importance SHAP des variables derivees par horizon, perte au retrait de la
famille) et on rappelle qu'aucun modele n'a battu le benchmark.

Sorties dans outputs/metriques/ :
- dictionnaire_variables.csv : une ligne par colonne du dataset ;
- qualite_sources.csv : une ligne par source brute ;
- controles_colonnes.csv : doublons, valeurs extremes, trous, frequence, par colonne.

Usage : PYTHONPATH=src .venv/Scripts/python.exe scripts/45_dictionnaire_qualite.py
"""
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/raw"
OUT = ROOT / "outputs/metriques"
ND = "Non documenté"
PAYS = {"CIV": "Côte d'Ivoire", "GHA": "Ghana", "IDN": "Indonésie", "ECU": "Équateur", "CMR": "Cameroun", "BRA": "Brésil",
        "NGA": "Nigeria", "PER": "Pérou", "DOM": "Rép. dominicaine", "MONDE": "indice mondial (pays pondérés par la production FAOSTAT N-2)"}
UTILISES = ("CIV", "GHA", "IDN", "MONDE")
ALIGN = "Dernière valeur publiée strictement avant la séance (aligner_disponible)"
MANQ_MARCHE = "Dernière clôture strictement antérieure, 10 jours au plus ; au-delà vide. Aucune interpolation."

MARCHE = {
    "dx_y_nyb": ("Indice du dollar américain (DXY)", "indice", "marche_finance"),
    "tnx": ("Taux de l'État américain à 10 ans", "% par an", "marche_finance"),
    "irx": ("Taux de l'État américain à 13 semaines", "% par an", "marche_finance"),
    "cl_f": ("Pétrole brut WTI, contrat continu", "$/baril", "couts_production"),
    "ng_f": ("Gaz naturel Henry Hub, contrat continu", "$/MMBtu", "couts_production"),
    "eurusd_x": ("Taux de change euro / dollar", "$ pour 1 €", "couts_production"),
    "ghs_x": ("Taux de change dollar / cedi ghanéen", "GHS pour 1 $", "couts_production"),
    "idr_x": ("Taux de change dollar / roupie indonésienne", "IDR pour 1 $", "couts_production"),
    "ngn_x": ("Taux de change dollar / naira nigérian", "NGN pour 1 $", "couts_production"),
    "brl_x": ("Taux de change dollar / réal brésilien", "BRL pour 1 $", "couts_production"),
    "pen_x": ("Taux de change dollar / sol péruvien", "PEN pour 1 $", "couts_production"),
    "barn_sw": ("Action Barry Callebaut (SIX)", "CHF", "demande_substituts"),
    "hsy": ("Action Hershey (NYSE)", "$", "demande_substituts"),
    "mdlz": ("Action Mondelez (Nasdaq)", "$", "demande_substituts"),
    "nesn_sw": ("Action Nestlé (SIX)", "CHF", "demande_substituts"),
    "lisn_sw": ("Action nominative Lindt & Sprüngli (SIX)", "CHF", "demande_substituts"),
    "lisp_sw": ("Bon de participation Lindt & Sprüngli (SIX)", "CHF", "demande_substituts"),
}
DANS_MODELE_MARCHE = {"cacao_close", "dx_y_nyb", "ng_f", "eurusd_x", "ghs_x", "idr_x", "ngn_x", "barn_sw", "hsy", "mdlz", "nesn_sw",
                      "lisn_sw", "lisp_sw"}
NASA = {"T2M": ("Température moyenne à 2 m", "°C"), "T2M_MAX": ("Température maximale à 2 m", "°C"),
        "T2M_MIN": ("Température minimale à 2 m", "°C"), "RH2M": ("Humidité relative de l'air à 2 m", "%"),
        "GWETROOT": ("Humidité du sol dans la zone racinaire", "fraction 0 à 1"),
        "GWETTOP": ("Humidité du sol en surface", "fraction 0 à 1"), "WS2M": ("Vitesse du vent à 2 m", "m/s"),
        "ALLSKY_SFC_SW_DWN": ("Rayonnement solaire reçu au sol", "kWh/m²/jour")}
NASA_MODELE = {"T2M_MAX", "RH2M", "GWETROOT", "ALLSKY_SFC_SW_DWN", "WS2M"}
PRIX_BM = {"UREE": ("Urée", "engrais", "couts_production"), "DAP": ("Phosphate diammonique (DAP)", "engrais", "couts_production"),
           "TSP": ("Superphosphate triple (TSP)", "engrais", "couts_production"),
           "POTASSE": ("Chlorure de potassium", "engrais", "couts_production"), "SUCRE": ("Sucre, prix mondial", "proche", "demande_substituts"),
           "HUILE_PALME": ("Huile de palme", "proche", "demande_substituts"), "CAFE_ROBUSTA": ("Café robusta", "proche", "demande_substituts")}


def fiche(**k) -> dict:
    base = dict(signification=ND, formule=ND, unite=ND, frequence_native=ND, frequence_dataset="Quotidienne (séances CC=F)",
                source=ND, manquants=ND, transformation=ND, decalage=ND, publication=ND, utilisation=ND, famille="hors_famille",
                role="variable")
    base.update(k)
    return base


def decrire(c: str) -> dict:
    """Regles de documentation, dans l'ordre des scripts qui produisent les colonnes."""
    if c == "cacao_close":
        return fiche(signification="Prix de règlement du contrat à terme de cacao continu (ICE US, CC=F)", formule="Colonne Close de Yahoo Finance, sans ajustement",
                     unite="$/t", frequence_native="Quotidienne", source="Yahoo Finance (ICE Futures US)", manquants="Axe du dataset : aucune séance manquante par construction",
                     transformation="Aucune dans le dataset ; rendements et volatilités dans les modèles", decalage="Aucun : définit l'axe",
                     publication="Fin de séance, données retardées", utilisation="Base des cibles ; variables cacao_close_r, cacao_vol (modèle principal)",
                     famille="marche_finance", role="prix_cible")
    if c == "cacao_volume":
        return fiche(signification="Nombre de contrats CC=F échangés dans la séance", formule="Colonne Volume de Yahoo Finance", unite="contrats",
                     frequence_native="Quotidienne", source="Yahoo Finance", manquants="Aucun ; volume nul possible les jours de passage d'échéance",
                     transformation="Moyenne sur 21 séances rapportée à sa moyenne de l'année passée (cacao_volume_ecart)", decalage="Aucun",
                     publication="Fin de séance", utilisation="Modèle principal (cacao_volume_ecart)", famille="marche_finance")
    if c in ("volume_nul", "volume_faible"):
        seuil = "= 0" if c == "volume_nul" else "< 100 contrats"
        return fiche(signification=f"Indicateur de séance au volume {seuil}", formule=f"1 si Volume {seuil}, sinon 0 (scripts/06)", unite="0 ou 1",
                     frequence_native="Quotidienne", source="Calculé depuis Yahoo Finance", manquants="Aucun", transformation="Aucune", decalage="Aucun",
                     publication="Fin de séance", utilisation="Contrôle qualité, jamais une variable de modèle", role="controle")
    if c == "saut_echeance":
        return fiche(signification="Jour de saut de prix dû à un passage d'échéance de CC=F", formule="Pour chaque passage repéré par le volume (scripts/03), jour du plus grand |rendement| entre ce jour et le suivant (grille.jours_de_saut)",
                     unite="booléen", frequence_native="Événementielle (environ 5 par an)", source="Calculé depuis Yahoo Finance", manquants="Aucun",
                     transformation="Aucune", decalage="Repéré après coup : utilise le rendement du lendemain", publication="Non publiable en temps réel",
                     utilisation="Cibles sans sauts et lecture de contrôle seulement ; jamais une variable", role="controle")
    if c in MARCHE:
        nom, unite, fam = MARCHE[c]
        if c in DANS_MODELE_MARCHE:
            util = f"Modèle principal : rendement logarithmique sur les fenêtres courte et longue ({c}_r)"
        elif c == "cl_f":
            util = "Modèle principal : variation relative (cl_f_v), valable même si le prix passe sous zéro (avril 2020)"
        elif c in ("tnx", "irx"):
            util = f"Modèle principal : différence de taux ({c}_d)"
        else:
            util = "Collectée, non utilisée par les modèles"
        return fiche(signification=nom, formule="Clôture Yahoo Finance (Adj Close pour les actions)", unite=unite, frequence_native="Quotidienne",
                     source="Yahoo Finance", manquants=MANQ_MARCHE, transformation="Erreurs de cotation du change retirées (allers-retours > 15 %, scripts/06)" if c.endswith("_x") else "Aucune dans le dataset",
                     decalage="Clôture strictement antérieure à la séance du cacao", publication="Fin de séance de son propre marché",
                     utilisation=util, famille=fam)
    m = re.fullmatch(r"cible_(rendement|hausse|vol|hausse_neutre)_(\d+)", c)
    if m:
        t, h = m.groups()
        f = {"rendement": f"log(P[t+{h}] / P[t])", "hausse": f"1 si log(P[t+{h}] / P[t]) > 0", "vol": f"écart-type des rendements journaliers de t+1 à t+{h} × √252",
             "hausse_neutre": f"1 si la somme des rendements de t+1 à t+{h}, jours de saut mis à zéro, est > 0"}[t]
        return fiche(signification=f"Cible : {'sens' if 'hausse' in t else t} du cacao à {h} séances", formule=f, unite={"vol": "volatilité annualisée", "rendement": "log-rendement"}.get(t, "0 ou 1"),
                     frequence_native="Quotidienne", source="Calculé depuis cacao_close", manquants=f"Vide sur les {h} dernières séances (futur inconnu)",
                     transformation="Aucune", decalage=f"Regarde {h} séances dans le futur", publication="Non applicable", famille="cible",
                     utilisation="Cible à prévoir : jamais une variable", role="cible")
    m = re.fullmatch(r"passage_dans_(\d+)", c)
    if m:
        h = m.group(1)
        return fiche(signification=f"Un saut d'échéance tombe entre t+1 et t+{h}", formule=f"1 si saut_echeance est vrai sur l'une des {h} séances suivantes",
                     unite="0 ou 1", frequence_native="Quotidienne", source="Calculé", manquants="Aucun", transformation="Aucune",
                     decalage=f"Regarde {h} séances dans le futur", publication="Non applicable", famille="cible",
                     utilisation="Lecture de contrôle (exclusion des fenêtres) ; jamais une variable", role="controle")
    m = re.fullmatch(r"NASA_(.+)_([A-Z]+)", c)
    if m and m.group(1) in NASA:
        v, p = m.groups()
        nom, unite = NASA[v]
        delai = 6 if v == "ALLSKY_SFC_SW_DWN" else 3
        util = f"Modèle principal : écart à la normale passée de la moyenne sur 30 jours ({c}_a30)" if v in NASA_MODELE and p in UTILISES else "Collectée, non utilisée par les modèles"
        return fiche(signification=f"{nom}, {PAYS.get(p, p)}", formule="Moyenne des points météo du pays pondérée par MapSPAM 2010 (point vide ignoré)" + (" ; monde : pays pondérés par la production FAOSTAT N-2" if p == "MONDE" else ""),
                     unite=unite, frequence_native="Quotidienne", source="NASA POWER (points de scripts/13)", manquants=f"{ALIGN} ; 10 jours de tolérance",
                     transformation="Aucune dans le dataset", decalage=f"{delai} jours (retard observé sur l'API en novembre 2026)",
                     publication=f"Environ {delai} jours après la mesure", utilisation=util, famille="climat")
    m = re.fullmatch(r"ROBUSTESSE_PRECTOTCORR_([A-Z]+)", c)
    if m:
        p = m.group(1)
        return fiche(signification=f"Pluie NASA POWER, {PAYS.get(p, p)}", formule="Moyenne pondérée MapSPAM des points du pays", unite="mm/jour",
                     frequence_native="Quotidienne", source="NASA POWER", manquants=f"{ALIGN} ; 10 jours", transformation="Aucune", decalage="3 jours",
                     publication="Environ 3 jours", famille="climat",
                     utilisation="Test de robustesse 1 seulement (pluie NASA suspecte en 2020-2023, remplacée par ERA5 et CHIRPS)", role="robustesse")
    m = re.fullmatch(r"ERA5_ANOM(\d+)J_([A-Z]+)", c)
    if m:
        n, p = m.groups()
        return fiche(signification=f"Pluie des {n} derniers jours, écart à la normale, {PAYS.get(p, p)}", formule=f"Somme glissante de {n} jours par point, écart à la moyenne du même mois des années strictement passées divisé par leur écart-type (3 ans minimum), puis moyenne pondérée",
                     unite="écart-type", frequence_native="Quotidienne", source="ERA5 via Open-Meteo (models=era5)", manquants=f"{ALIGN} ; 10 jours ; vide de 2005 à 2007 (pas encore 3 ans de passé)",
                     transformation="Anomalie passée (cacao.meteo.anomalie_passee)", decalage="7 jours (retard observé de l'API)", publication="Environ 7 jours",
                     utilisation="Modèle principal, telle quelle" if p in UTILISES else "Collectée, non utilisée par les modèles", famille="climat")
    m = re.fullmatch(r"CHIRPS_ANOM(\d+)M_([A-Z]+)", c)
    if m:
        n, p = m.groups()
        return fiche(signification=f"Pluie des {n} derniers mois, écart à la normale, {PAYS.get(p, p)}", formule=f"Cumul de {n} mois par point, écart à la normale fixe 1991-2004 du même mois divisé par son écart-type, puis moyenne pondérée",
                     unite="écart-type", frequence_native="Mensuelle", source="CHIRPS v2.0 (Climate Hazards Center), fichier mondial", manquants=f"{ALIGN} ; 45 jours",
                     transformation="Anomalie de référence (cacao.meteo.anomalie_reference)", decalage="Le 25 du mois suivant (marge au-dessus de la 3e semaine annoncée)",
                     publication="Vers la 3e semaine du mois suivant", utilisation="Modèle principal, telle quelle" if p in UTILISES else "Collectée, non utilisée par les modèles", famille="climat")
    m = re.fullmatch(r"GEFS_(PLUIE|TMAX)(\d)J_ANOM_([A-Z]+)", c)
    if m:
        v, n, p = m.groups()
        j = "2 à 6" if n == "5" else "2 à 10"
        return fiche(signification=f"{'Pluie' if v == 'PLUIE' else 'Température maximale'} prévue pour les jours {j}, écart à la normale, {PAYS.get(p, p)}",
                     formule=("Cumul prévu des jours " if v == "PLUIE" else "Moyenne prévue des jours ") + f"{j}, niveau corrigé par pays et régime face à " + ("CHIRPS (rapport)" if v == "PLUIE" else "NASA T2M_MAX (écart)") + " sur le passé, puis anomalie passée",
                     unite="écart-type", frequence_native="Quotidienne (émission 00 UTC)", source="NOAA GEFS : reprévisions v12 (2005-2019), opérationnel (depuis le 23/09/2020), membre de contrôle",
                     manquants="Janvier à septembre 2020 écartés (ancien modèle) ; date manquante : dernière prévision, 3 jours au plus ; vide avant avril 2008",
                     transformation="scripts/36 : correction de niveau, puis anomalie passée", decalage="Utilisée dès la séance suivant l'émission",
                     publication="Quelques heures après l'émission", famille="climat", utilisation="Test de robustesse 5 seulement", role="robustesse")
    if c == "ONI":
        return fiche(signification="Indice océanique El Niño (anomalie de température du Pacifique tropical, saison de 3 mois)", formule="Valeur publiée par la NOAA (fichier oni.txt)",
                     unite="°C", frequence_native="Mensuelle (saisons glissantes)", source="NOAA Climate Prediction Center", manquants=f"{ALIGN} ; 45 jours",
                     transformation="Aucune ; variation sur 63 séances dans les modèles", decalage="45 jours après la fin de la saison (hypothèse prudente, à confirmer)",
                     publication="Vers le milieu du mois suivant la saison (hypothèse)", utilisation="Modèle principal (ONI et ONI_d63)", famille="climat")
    m = re.fullmatch(r"FEUX_([A-Z]+)", c)
    if m:
        p = m.group(1)
        return fiche(signification=f"Nombre quotidien de feux de végétation détectés dans les zones de cacao, {PAYS.get(p, p)}", formule="Détections de type 0 (végétation) et de confiance ≥ 30, comptées par jour",
                     unite="détections/jour", frequence_native="Quotidienne", source="NASA FIRMS, MODIS (archive 2005-2025)",
                     manquants="Jour sans détection = 0 ; 2026 vide (clé d'accès gratuite non créée)", transformation="Aucune dans le dataset",
                     decalage="1 jour (hypothèse : quasi temps réel)", publication="Quelques heures (produit temps réel)",
                     utilisation=f"Modèle principal : log(1 + cumul 30 jours) en écart à la normale passée ({c}_a30)" if p in UTILISES else "Collectée, non utilisée par les modèles",
                     famille="biodiversite")
    m = re.fullmatch(r"CFTC_(.+)", c)
    if m:
        v = m.group(1)
        noms = {"INTERET_OUVERT": ("Intérêt ouvert total sur le cacao ICE US", "contrats"),
                "NET_NON_COMMERCIAUX": ("Position nette des non-commerciaux (rapport historique)", "part de l'intérêt ouvert"),
                "NET_COMMERCIAUX": ("Position nette des commerciaux (rapport historique)", "part de l'intérêt ouvert"),
                "NET_FONDS": ("Position nette des fonds gérés (managed money, rapport désagrégé)", "part de l'intérêt ouvert"),
                "NET_PRODUCTEURS": ("Position nette des producteurs, négociants et transformateurs", "part de l'intérêt ouvert")}
        nom, unite = noms.get(v, (ND, ND))
        util = {"INTERET_OUVERT": "Modèle principal : log-variation sur la fenêtre longue", "NET_COMMERCIAUX": "Collectée, non utilisée par les modèles"}.get(
            v, "Modèle principal : niveau et variation sur la fenêtre longue")
        return fiche(signification=nom, formule="(positions longues − courtes) / intérêt ouvert" if v.startswith("NET") else "Intérêt ouvert publié",
                     unite=unite, frequence_native="Hebdomadaire (positions du mardi)", source="CFTC, Commitments of Traders (API publique)",
                     manquants=f"{ALIGN} ; 10 jours", transformation="Aucune dans le dataset", decalage="Mardi + 3 jours : publiée le vendredi après la clôture, utilisée à la séance suivante",
                     publication="Vendredi 15 h 30 heure de New York", utilisation=util, famille="investisseurs_biais")
    m = re.fullmatch(r"GPR_(GPRD(?:_ACT|_THREAT)?)", c)
    if m:
        v = m.group(1)
        nom = {"GPRD": "Indice quotidien de risque géopolitique", "GPRD_ACT": "Indice quotidien des actes géopolitiques", "GPRD_THREAT": "Indice quotidien des menaces géopolitiques"}[v]
        return fiche(signification=nom + " (Caldara et Iacoviello)", formule="Part des articles de grands journaux évoquant des tensions, normalisée (méthode des auteurs)",
                     unite="indice (100 = moyenne de référence des auteurs)", frequence_native="Quotidienne", source="Caldara et Iacoviello, matteoiacoviello.com",
                     manquants=f"{ALIGN} ; 10 jours", transformation="Aucune dans le dataset", decalage="7 jours (retard observé)", publication="Mise à jour régulière des auteurs",
                     utilisation="Modèle principal : moyenne mobile du log sur les fenêtres courte et longue", famille="geopolitique")
    m = re.fullmatch(r"GPR_MENSUEL_(.+)", c)
    if m:
        v = m.group(1)
        nom = {"GPR": "Indice mensuel de risque géopolitique mondial"}.get(v, f"Indice mensuel de risque géopolitique, {PAYS.get(v[-3:], v[-3:])}")
        return fiche(signification=nom + " (Caldara et Iacoviello)", formule="Méthode des auteurs", unite="indice", frequence_native="Mensuelle",
                     source="Caldara et Iacoviello", manquants=f"{ALIGN} ; 45 jours", transformation="Aucune ; log dans les modèles",
                     decalage="10 jours après la fin du mois (hypothèse)", publication="Début du mois suivant (hypothèse)", utilisation="Modèle principal (log)",
                     famille="geopolitique")
    m = re.fullmatch(r"GDELT_(cacao(?:_afrique)?)_(volume|ton)", c)
    if m:
        q, v = m.groups()
        req = "cocoa" if q == "cacao" else 'cocoa (Ghana OR "Ivory Coast")'
        return fiche(signification=f"{'Volume' if v == 'volume' else 'Ton moyen'} des articles de presse en ligne sur la requête « {req} »",
                     formule="API GDELT DOC 2.0, mode " + ("timelinevol : part des articles suivis par GDELT" if v == "volume" else "timelinetone : ton moyen des articles"),
                     unite="% des articles" if v == "volume" else "score de ton (négatif = défavorable)", frequence_native="Quotidienne", source="GDELT DOC 2.0",
                     manquants=f"{ALIGN} ; 10 jours ; commence en 2017", transformation="Aucune ; moyenne mobile sur la fenêtre longue dans les modèles",
                     decalage="1 jour", publication="Quasi temps réel", utilisation="Modèle principal (moyenne mobile)", famille="investisseurs_biais")
    m = re.fullmatch(r"TRENDS_(.+)_D(1|12)", c)
    if m:
        t, n = m.groups()
        terme = t.replace("_", " ").lower()
        return fiche(signification=f"Variation des recherches Google sur « {terme} » sur {n} mois", formule=f"log(1 + indice Trends) du mois − celui de {n} mois avant",
                     unite="différence de log", frequence_native="Mensuelle", source="Google Trends (pytrends), monde, depuis 2004",
                     manquants=f"{ALIGN} ; 45 jours", transformation="Seules les variations sont gardées : l'échelle de Trends dépend de toute la période téléchargée",
                     decalage="5 jours après la fin du mois (hypothèse)", publication="Disponible quelques jours après le mois", utilisation="Modèle principal, telle quelle",
                     famille="investisseurs_biais")
    m = re.fullmatch(r"GDELT_EV_(PART|CONFLIT|PROTESTATION)_([A-Z]+)", c)
    if m:
        v, p = m.groups()
        f = {"PART": "événements du pays sur 30 jours / événements mondiaux sur 30 jours × 1 000",
             "CONFLIT": "événements de conflit (classes 3 et 4 de GDELT) sur 30 jours / événements du pays sur 30 jours",
             "PROTESTATION": "événements de protestation (code racine 14) sur 30 jours / événements du pays sur 30 jours"}[v]
        nom = {"PART": "Part du pays dans l'actualité mondiale", "CONFLIT": "Part des événements de conflit", "PROTESTATION": "Part des manifestations"}[v]
        return fiche(signification=f"{nom}, {PAYS.get(p, p)}", formule=f, unite="pour mille" if v == "PART" else "fraction", frequence_native="Quotidienne",
                     source="Fichiers bruts d'événements GDELT 1.0 (scripts/32)", manquants=f"{ALIGN} ; 10 jours ; ton écarté (échelle cassée en 2013)",
                     transformation="Part : écart à la moyenne de l'année passée dans les modèles" if v == "PART" else "Aucune",
                     decalage="1 jour", publication="Fichier quotidien du lendemain",
                     utilisation="Modèle principal" if p in ("CIV", "GHA", "IDN") else "Collectée, non utilisée par les modèles", famille="geopolitique")
    m = re.fullmatch(r"PRIX_(.+)", c)
    if m and m.group(1) in PRIX_BM:
        nom, _, fam = PRIX_BM[m.group(1)]
        return fiche(signification=f"{nom}, prix mondial mensuel (logarithme)", formule="log(prix moyen du mois), Pink Sheet de la Banque mondiale", unite="log($/t)",
                     frequence_native="Mensuelle", source="Banque mondiale, Commodity Markets (Pink Sheet)", manquants=f"{ALIGN} ; 45 jours",
                     transformation="Logarithme ; différences sur 21 et 63 séances dans les modèles", decalage="5 jours après la fin du mois (hypothèse soutenue par la publication début de mois)",
                     publication="Début du mois suivant", utilisation="Modèle principal (variations sur 1 et 3 mois)", famille=fam)
    m = re.fullmatch(r"FAO_(RENDEMENT|PRODUCTION|PESTICIDES|AZOTE)_([A-Z]+)", c)
    if m:
        v, p = m.groups()
        nom, unite = {"RENDEMENT": ("Rendement du cacao", "kg/ha"), "PRODUCTION": ("Production de fèves de cacao", "t"),
                      "PESTICIDES": ("Pesticides utilisés par hectare cultivé", "kg/ha"), "AZOTE": ("Azote utilisé par hectare cultivé", "kg/ha")}[v]
        fam = "production_offre" if v == "PRODUCTION" else "biodiversite"
        return fiche(signification=f"{nom}, {PAYS.get(p, p)}", formule="Valeur annuelle FAOSTAT" + (" (souvent estimée par la FAO, code E)" if v == "RENDEMENT" else ""),
                     unite=unite, frequence_native="Annuelle", source="FAOSTAT", manquants=f"{ALIGN} ; 400 jours",
                     transformation="Variation annuelle du log dans les modèles", decalage="Année N utilisée à partir du 1er janvier N+2",
                     publication="Environ 1 an et demi après l'année ; valeurs révisées ensuite", utilisation="Modèle principal (variation annuelle)" if p in ("CIV", "GHA", "IDN") else "Collectée, non utilisée par les modèles",
                     famille=fam)
    return fiche()


def frequence_observee(s: pd.Series) -> str:
    """Nombre moyen de changements de valeur par an : distingue quotidien, hebdo, mensuel, annuel."""
    s = s.dropna()
    if len(s) < 30:
        return "Trop peu de valeurs"
    ans = (s.index[-1] - s.index[0]).days / 365.25
    n = (s.diff().fillna(0) != 0).sum() / max(ans, 0.1)
    for seuil, nom in ((150, "Quotidienne"), (30, "Hebdomadaire"), (8, "Mensuelle"), (0.5, "Annuelle")):
        if n >= seuil:
            return nom
    return "Quasi constante"


def controles(d: pd.DataFrame) -> pd.DataFrame:
    lignes = []
    for c in d.columns:
        s = pd.to_numeric(d[c], errors="coerce")
        v = s.dropna()
        if v.empty:
            lignes.append({"variable": c, "n_valides": 0})
            continue
        debut, fin = v.index[0], v.index[-1]
        dedans = s.loc[debut:fin]
        trous = dedans.isna().astype(int)
        plus_long = int(trous.groupby((trous == 0).cumsum()).sum().max())
        med = v.median()
        mad = (v - med).abs().median() * 1.4826
        extremes = int(((v - med).abs() > 8 * mad).sum()) if mad > 0 else 0
        lignes.append({"variable": c, "n_valides": len(v), "premiere_date": debut.date(), "derniere_date": fin.date(),
                       "completude_dans_periode": float(dedans.notna().mean()), "plus_long_trou_seances": plus_long,
                       "valeurs_extremes_8mad": extremes, "frequence_observee": frequence_observee(s),
                       "constante": bool(v.nunique() <= 1)})
    return pd.DataFrame(lignes)


def importance(dico: pd.DataFrame) -> pd.DataFrame:
    """Rang SHAP median (par annee de test) des variables derivees de chaque colonne, par cible et horizon."""
    s = pd.read_csv(OUT / "shap_variables.csv")
    rang = s.groupby(["cible", "horizon", "annee"])["shap"].rank(ascending=False)
    s = s.assign(rang=rang).groupby(["cible", "horizon", "variable"])["rang"].median().reset_index()
    n_var = s.groupby(["cible", "horizon"])["variable"].count()
    sortie = {}
    for c in dico["variable"]:
        derivees = s[s["variable"].str.startswith(c + "_") | (s["variable"] == c)]
        if c == "cacao_close":
            derivees = s[s["variable"].str.match(r"cacao_(close_r|vol)\d+")]
        if derivees.empty:
            continue
        morceaux = []
        for (cible, h), g in derivees.groupby(["cible", "horizon"]):
            morceaux.append(f"{'sens' if cible == 'sens' else 'vol.'} {h} : {int(g['rang'].min())}/{n_var[(cible, h)]}")
        sortie[c] = " ; ".join(morceaux)
    return pd.Series(sortie, name="rang_shap_par_horizon")


def qualite_sources() -> pd.DataFrame:
    """Une ligne par source brute : attendu, recu, valide, manquant, completude, dates."""
    def fichiers(dossier, motif):
        return sorted((R / dossier).glob(motif)) if (R / dossier).exists() else []

    def valide(f):
        return f.stat().st_size > 60

    def fin_csv(f, col):
        try:
            return str(pd.read_csv(f, usecols=[col])[col].dropna().iloc[-1])[:10]
        except Exception:
            return ND

    def ligne(famille, nom, fs, attendu, fin, na=None, note=""):
        recu = len(fs)
        ok = sum(valide(f) for f in fs)
        if na:
            statut = "NON APPLICABLE"
        elif recu > attendu:
            statut = "EXCÉDENTAIRE"
        elif ok >= attendu:
            statut = "COMPLET"
        else:
            statut = "INCOMPLET"
        maj = max((f.stat().st_mtime for f in fs), default=None)
        return {"famille": famille, "source": nom, "attendu": attendu, "recu": recu, "valide": ok, "manquant": max(attendu - ok, 0),
                "completude": ok / attendu if attendu else np.nan, "derniere_recuperation": datetime.fromtimestamp(maj).strftime("%Y-%m-%d") if maj else ND,
                "derniere_date_couverte": fin, "statut": statut, "note": note}

    def oni_fin():
        o = pd.read_csv(R / "t2_climat/oni.txt", sep=r"\s+").iloc[-1]
        return f"saison {o['SEAS']} {o['YR']}"

    def gpr_fin():
        q = pd.read_excel(R / "t5_geopolitique/gpr_quotidien.xls")["date"].max().date()
        m = pd.read_excel(R / "t5_geopolitique/gpr_mensuel.xls")["month"].max()
        return f"quotidien {q}, mensuel {m:%Y-%m}"

    pts = 349
    gefs = fichiers("t2_climat/gefs", "*.npy")
    attendu_gefs = len(pd.date_range("2005-01-01", max(pd.to_datetime(f.stem) for f in gefs), freq="D"))
    ev = fichiers("t5_geopolitique/gdelt_evenements", "*.csv")
    dernier_ev = max(pd.to_datetime(f.name[:8]) for f in ev if f.name[:8].isdigit() and len(f.name.split(".")[0]) == 8)
    attendu_ev = 1 + 12 * 7 + 3 + len(pd.date_range("2013-04-01", dernier_ev, freq="D"))
    firms26 = fichiers("t2_climat/firms", "*_2026.csv")
    lignes = [
        ligne("marche_finance", "Yahoo Finance (19 séries)", fichiers("t1_marches", "*.csv"), 19, fin_csv(R / "t1_marches/CC_F.csv", "date"),
              note="dont 2 non utilisées par les modèles (réal, sol) et EUR/XOF de contrôle"),
        ligne("marche_finance", "Banque mondiale, Pink Sheet", fichiers("t1_marches/controle", "*.xlsx"), 1, "Mensuelle (voir PRIX_)"),
        ligne("climat", "NASA POWER, 7 variables", fichiers("t2_climat/power", "*.csv"), pts, fin_csv(R / "t2_climat/power/CIV_000.csv", "date")),
        ligne("climat", "NASA POWER, rayonnement et vent", fichiers("t2_climat/power_complement", "*.csv"), pts, fin_csv(R / "t2_climat/power_complement/CIV_000.csv", "date")),
        ligne("climat", "ERA5 pluie (Open-Meteo)", fichiers("t2_climat/era5", "*.csv"), pts, fin_csv(R / "t2_climat/era5/CIV_000.csv", "date")),
        ligne("climat", "ERA5 contrôle, 14 points", fichiers("t2_climat/era5_controle", "*.csv"), 14, fin_csv(sorted((R / "t2_climat/era5_controle").glob("*.csv"))[0], "date")),
        ligne("climat", "CHIRPS, points", fichiers("t2_climat/chirps", "*.csv"), pts, fin_csv(R / "t2_climat/chirps/CIV_000.csv", "mois"),
              note="2 points indonésiens sans donnée (IDN_008, IDN_013) : fichiers présents mais vides"),
        ligne("climat", "NOAA ONI", fichiers("t2_climat", "oni.txt"), 1, oni_fin()),
        ligne("climat", "NOAA GEFS pluie", gefs, attendu_gefs, str(max(pd.to_datetime(f.stem) for f in gefs).date()), note="une échéance absente (2020-08-28, jour 7), période écartée"),
        ligne("climat", "NOAA GEFS Tmax", fichiers("t2_climat/gefs_tmax", "*.npy"), attendu_gefs, str(max(pd.to_datetime(f.stem) for f in fichiers("t2_climat/gefs_tmax", "*.npy")).date())),
        ligne("biodiversite", "NASA FIRMS 2005-2025", [f for f in fichiers("t2_climat/firms", "*.csv") if not f.stem.endswith("2026")], 9 * 21, "2025-12-31"),
        ligne("biodiversite", "NASA FIRMS 2026", firms26, 9, ND, na=not firms26, note="clé d'accès gratuite non créée : source non interrogée"),
        ligne("biodiversite", "FAOSTAT pesticides et azote", fichiers("t3_offre", "faostat_[pe]*.csv"), 2, "2024 (annuel)"),
        ligne("production_offre", "FAOSTAT cacao", fichiers("t3_offre", "faostat_cacao.csv"), 1, "2024 (annuel)"),
        ligne("investisseurs_biais", "CFTC (2 rapports)", fichiers("t4_investisseurs", "cftc_*.csv"), 2, fin_csv(R / "t4_investisseurs/cftc_legacy.csv", "report_date_as_yyyy_mm_dd")),
        ligne("investisseurs_biais", "Google Trends", fichiers("t4_investisseurs", "google_trends_mensuel.csv"), 1, fin_csv(R / "t4_investisseurs/google_trends_mensuel.csv", "date")),
        ligne("investisseurs_biais", "GDELT presse cacao (API)", fichiers("t5_geopolitique", "gdelt_cacao*.csv"), 4, fin_csv(R / "t5_geopolitique/gdelt_cacao_volume.csv", "date"),
              note="2 séries de tensions par mots-clés abandonnées (blocage 429), couvertes par les fichiers bruts"),
        ligne("geopolitique", "GPR quotidien et mensuel", fichiers("t5_geopolitique", "gpr_*.xls"), 2, gpr_fin()),
        ligne("geopolitique", "GDELT événements bruts", ev, attendu_ev, str(dernier_ev.date()),
              note="annuel 2005, mensuel 2006 à mars 2013, quotidien ensuite ; un jour absent n'est pas une erreur (trous connus de GDELT)"),
    ]
    return pd.DataFrame(lignes)


def main() -> None:
    d = pd.read_parquet(ROOT / "data/processed/dataset_quotidien.parquet")
    dico = pd.DataFrame([{"variable": c, **decrire(c)} for c in d.columns])
    ctrl = controles(d)
    dico = dico.merge(ctrl[["variable", "premiere_date", "derniere_date", "n_valides", "completude_dans_periode", "frequence_observee"]], on="variable", how="left")
    dico = dico.merge(importance(dico), left_on="variable", right_index=True, how="left")
    r = pd.read_csv(OUT / "retrait_familles.csv")
    sig = r.assign(sig=(r["ic_bas"] > 0) | (r["ic_haut"] < 0))
    resume = sig.groupby("famille").apply(lambda g: " ; ".join(f"{'sens' if c == 'sens' else 'vol.'} {h} : {p:+.3f}{'*' if s else ''}"
                                                                for c, h, p, s in zip(g["cible"], g["horizon"], g["perte"], g["sig"])), include_groups=False)
    dico["perte_retrait_famille"] = dico["famille"].map(resume)
    dico["interet_prevision"] = np.where(dico["role"].isin(["cible", "controle"]), "Sans objet",
                                         "Hypothèse à tester. Mesuré : aucune famille ne permet de battre le benchmark ; voir le rang SHAP et la perte au retrait")
    dico["n_documente"] = (dico[["signification", "formule", "unite", "source", "decalage", "utilisation"]] != ND).sum(axis=1)
    dico.to_csv(OUT / "dictionnaire_variables.csv", index=False)
    ctrl.to_csv(OUT / "controles_colonnes.csv", index=False)
    q = qualite_sources()
    q.to_csv(OUT / "qualite_sources.csv", index=False)

    print(f"Dictionnaire : {len(dico)} colonnes ; non documentées : {int((dico['signification'] == ND).sum())}")
    print(dico["famille"].value_counts().to_string())
    print(dico["role"].value_counts().to_string())
    print("Fréquences observées :", dico["frequence_observee"].value_counts().to_dict())
    print(q[["source", "attendu", "recu", "valide", "completude", "derniere_date_couverte", "statut"]].to_string(index=False))
    print("Colonnes avec valeurs extrêmes (8 MAD) :", int((ctrl["valeurs_extremes_8mad"] > 0).sum()), "; doublons de date :", int(d.index.duplicated().sum()))
    print(dico[dico["signification"] == ND]["variable"].tolist())


if __name__ == "__main__":
    main()
