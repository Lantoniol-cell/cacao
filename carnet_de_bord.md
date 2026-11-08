# Carnet de bord — Projet Cacao

> **Quel facteur a le plus d'impact sur le prix du cacao sur les marchés financiers ?**
> Projet individuel du cours *Machine Learning for Finance* (G. Coqueret).
> Ce carnet est tenu en continu et sert de base au rapport final.

---

## Introduction du projet

### Contexte

Le cacao a connu l'une des flambées les plus marquantes de l'histoire des matières premières : son prix a plus que triplé en 2024, avant de rechuter fortement. Environ 60 % de la production mondiale vient de deux pays, la Côte d'Ivoire et le Ghana. Ce marché concentré est donc exposé à des chocs climatiques, politiques, écologiques, financiers et comportementaux.

### Objectif

Estimer, sur les semaines à venir, la **direction** du cours du cacao (hausse ou baisse) et son **niveau de risque** (volatilité), puis identifier les facteurs qui pèsent le plus parmi sept familles. Le sujet précise que prédire le prix exact n'est pas le but ; le prix pourra rester une sortie secondaire.

| # | Famille | Exemples d'indicateurs |
|---|---------|------------------------|
| 1 | Climat et conditions de culture | Pluie, température, sécheresses, harmattan, saisonnalité des récoltes |
| 2 | Géopolitique | Tensions en Côte d'Ivoire et au Ghana (GDELT), Sahel, prix garantis aux paysans, droits de douane |
| 3 | Biodiversité et environnement | Swollen shoot, vieillissement des arbres, orpaillage illégal |
| 4 | Coûts de production | Pétrole, gaz, engrais |
| 5 | Marché et finance | Dollar, taux, contrats ouverts, rééquilibrage des indices, change |
| 6 | Investisseurs et biais | Positions CFTC, momentum, Google Trends |
| 7 | Demande et actions liées | Fêtes, Barry Callebaut, Hershey, Mondelez, Lindt, Nestlé, broyages |

### Démarche prévue

1. **Données** : inspection, nettoyage, imputation, alignement des dates selon les retards de publication, création de la cible.
2. **Benchmark** : modèle simple de référence.
3. **Machine learning** : entraînement chronologique sans biais de look-ahead, avec `random_state` fixé.
4. **Interprétation** : importance des variables, notamment avec SHAP. SHAP mesure une contribution aux prédictions et n'établit pas de causalité.
5. **Site** : site Quarto interactif hébergé sur GitHub Pages (Plotly ou Bokeh).

### Règles du projet

- **Aucune donnée brute inventée ou simulée.** Le nettoyage et l'imputation par méthodes statistiques documentées sont autorisés.
- **Fichier manquant ou insuffisant** : le signaler et demander le fichier ou la source.
- **Traçabilité** : ce carnet est mis à jour à chaque modification.
- **Consignes du cours** : l'usage des LLM doit être mentionné (règle 1) et le travail doit rester individuel (règle 2).

### Cadrage des données (depuis le 2026-11-04)

Le point de départ temporel est **2005**. Les données sont organisées en six thématiques, détaillées dans l'entrée de journal « Phase 1 : cadrage ».

1. Cours du cacao, marchés financiers et taux de change
2. Météo et climat localisé
3. Production, coûts et offre mondiale
4. Investisseurs, spéculation et comportement
5. Géopolitique et contexte
6. Biodiversité et environnement, par proxys

Règle supplémentaire : aucun chiffre, date ou événement ne doit être inventé. Tout fait marquant doit être recoupé et vérifiable dans des médias de référence.

### Livrables et échéances

| Date | Livrable |
|------|----------|
| 18 novembre 2026 | Oral de 5 minutes, 3 slides |
| 31 décembre 2026 | Objet accessible par URL et rapport de 2 à 5 pages (démarche, outils d'IA et exemples de prompts, problèmes, limites, extensions), à déposer sur Brightspace |

---

## Journal

### 2026-11-04 — Étape 0 : inspection du dossier de travail

**Statut : inspection terminée, bloquée sur les séries temporelles.**

#### Démarche

- Parcours récursif de `Projet CACAO`, du Bureau, de Téléchargements et de Documents.
- Lecture de `ml_project_specs.html`, `Projet.docx`, `PROMPT.docx` et du notebook `etape1_donnees_cacao.ipynb`.
- Lecture des archives MapSPAM **sans extraction sur disque** : en-têtes des CSV de production et fichiers ReadMe.
- Vérification de l'environnement technique.

Aucun script n'a été ajouté au projet : les scripts d'inspection sont restés temporaires. Le seul fichier créé dans le projet est ce carnet.

#### Inventaire des fichiers

Dossier **`Consignes du projet/`** :

| Fichier | Contenu |
|---------|---------|
| `ml_project_specs.html` | Consignes officielles du cours |
| `EXPLICATION PROJET/Projet.docx` | Description du sujet, sept familles, planning, retours méthodologiques |
| `PROMPT/PROMPT.docx` | Prompt de démarrage du projet |

Dossier **`MapSPAM zones de production/`** : statistiques agricoles spatialisées MapSPAM (IFPRI), soit 6,27 Go.

| Millésime | Couverture | Taille | Colonne cacao | Exploitable |
|-----------|-----------|--------|---------------|-------------|
| 2000 v3.0.7 | Mondiale, 20 cultures | 738 Mo | **Aucune** | **Non** |
| 2005 v3.2 | Mondiale | 2 000 Mo | `coco_a` | Oui |
| 2010 v2.0 | Mondiale | 2 300 Mo | `coco_a` | Oui |
| 2017 v2r1 | **Afrique subsaharienne seulement** | 468 Mo | `coco_a` | Oui, Afrique seulement |
| 2020 v2.0 r2 | Mondiale | 767 Mo | `coco` | Oui |

MapSPAM est une carte de la production par cellule de 5 minutes d'arc, avec un instantané par millésime. **Ce n'est pas une série temporelle.**

Hors du projet :

- `Téléchargements/etape1_donnees_cacao.ipynb` : notebook de test (`CC=F` via yfinance, météo Open-Meteo pour Soubré et Kumasi). Il ne contient aucun résultat enregistré et aucun des CSV qu'il doit produire n'a été trouvé.
- `Téléchargements/dataverse_files.zip` : doublon du millésime 2020.

#### Problèmes rencontrés

1. **Dossier « Cacao » introuvable.** Aucun dossier de ce nom n'existe sur le Bureau, dans Téléchargements ou dans Documents.
2. **Aucune série temporelle disponible.** Les prix, la météo, les indicateurs financiers, les positions CFTC et les cours des chocolatiers sont absents. Les phases 1 à 5 ne peuvent pas démarrer. Conformément à la règle 1, rien n'a été simulé et la demande a été transmise à l'utilisatrice.
3. **MapSPAM 2000 sans cacao.** Le cacao y est au mieux inclus dans la catégorie `othe`. Le premier millésime utile est 2005.
4. **Schémas MapSPAM hétérogènes.** Les noms de colonnes, les identifiants de cellule et le découpage des fichiers varient selon le millésime. Il faudra harmoniser leur lecture.
5. **Git absent, Quarto hors du PATH.** Git n'est pas détecté. Quarto 1.10.18 est bien présent, mais seulement dans Positron. Git sera nécessaire pour GitHub Pages.
6. **Python 3.14 uniquement.** La compatibilité de `shap` et des dépendances avec cette version n'a pas été testée. À vérifier dès l'installation, avec Python 3.12 en solution de repli.

#### Points de vigilance méthodologiques

- **Biais de look-ahead dans les pondérations.** Les millésimes MapSPAM sont publiés des années après leur année de référence (le millésime 2020 est cité avec la date 2025). Une pondération fixe sur 2020 appliquée à 2010 utiliserait une information future. Une analyse de sensibilité devra comparer plusieurs millésimes.
- **Cohérence entre les consignes et le prompt.** Le prompt vise un historique depuis 2000 et sept familles. `Projet.docx` recommande de commencer par quatre familles et un historique réellement constructible. La couverture réelle de chaque série décidera de la période commune.
- **Prix en contrat continu.** `CC=F`, s'il est retenu, devra être contrôlé : discontinuités de changement d'échéance et droit de redistribution des données sur un site public.

#### Pistes d'utilisation de MapSPAM

MapSPAM peut servir à construire un **indice météo pondéré par les zones de culture** : au lieu de deux villes, chaque cellule compte selon sa production de cacao. C'est un élément différenciant pour la note d'originalité. Seules les colonnes cacao seraient extraites, ce qui évite de manipuler 6 Go par la suite.

#### Données à obtenir

Les sources ci-dessous sont des **candidates non testées**. Leur couverture, leur licence et leur retard de publication restent à vérifier.

| Besoin | Famille | Source candidate | Priorité |
|--------|---------|------------------|----------|
| Prix et volume du cacao | Cible, 5, 6 | Dossier « Cacao », sinon Yahoo Finance `CC=F` | **Bloquant** |
| Pluie et température par pays producteur | 1 | Dossier « Cacao », sinon Open-Meteo ou ERA5 | Haute |
| Dollar, taux, change | 5 | FRED, Yahoo Finance | Haute |
| Positions des spéculateurs | 6 | Rapports CFTC COT | Haute |
| Pétrole, gaz, engrais | 4 | Yahoo Finance, FRED, Banque mondiale | Moyenne |
| Actions des chocolatiers | 7 | Yahoo Finance | Moyenne |
| Attention du public | 6 | Google Trends | Basse |
| Tensions politiques | 2 | GDELT | Basse |
| Biodiversité | 3 | Pas de source hebdomadaire identifiée, analyse de contexte | Basse |

#### Structure de répertoires proposée (non créée, en attente de validation)

```text
Projet CACAO/
├── carnet_de_bord.md           # Ce carnet
├── README.md                   # Présentation et mode d'emploi
├── requirements.txt            # Dépendances figées
├── .gitignore                  # Exclut données lourdes et consignes
├── config/
│   └── sources.yaml            # Sources, couverture, retards de publication
├── data/
│   ├── raw/                    # Données brutes, jamais modifiées
│   ├── interim/                # Données nettoyées, une série par fichier
│   └── processed/              # Table hebdomadaire finale
├── src/cacao/
│   ├── ingestion/              # Chargement par source
│   ├── cleaning/               # Nettoyage, imputation
│   ├── features/               # Variables par famille, alignement des dates
│   ├── models/                 # Benchmark, ML, validation walk-forward
│   └── interpretation/         # SHAP, agrégation par famille
├── scripts/                    # Exécution des phases dans l'ordre
├── notebooks/                  # Exploration uniquement
├── tests/                      # Contrôles anti-look-ahead notamment
├── outputs/
│   ├── figures/
│   ├── models/
│   └── metrics/
├── site/                       # Projet Quarto
│   ├── _quarto.yml
│   ├── index.qmd
│   └── pages/
├── Consignes du projet/        # Existant, exclu du dépôt
└── MapSPAM zones de production/   # Existant, exclu du dépôt
```

Raisons principales :

- `data/raw/` reste immuable et les étapes sont séparées, ce qui rend chaque imputation traçable.
- La logique est dans `src/`, et non dans les notebooks, pour être réutilisable par les tests, les scripts et le site.
- `config/sources.yaml` centralise les retards de publication, point clé contre le look-ahead.
- Les archives MapSPAM dépassent largement la limite de GitHub (100 Mo par fichier). Elles restent locales, seul l'extrait cacao serait versionné.
- Les consignes du cours n'ont pas à figurer dans un dépôt public.

#### Résultats

- Inventaire complet des fichiers disponibles.
- Cacao confirmé dans quatre millésimes MapSPAM sur cinq.
- **Aucune série temporelle disponible à ce stade.**
- Aucun modèle ni résultat chiffré.

#### Prochaines étapes

1. Obtenir le dossier « Cacao » ou l'accord pour récupérer les sources publiques.
2. Valider la structure proposée et la créer.
3. Installer Git, créer l'environnement Python et tester `shap`.
4. Reprendre la phase 1, avec un premier modèle simple visé pour l'oral du 18 novembre.

---

### 2026-11-04 — Extraction des archives MapSPAM

**Statut : terminée et vérifiée.**

#### Démarche

- Script créé : `scripts/00_extraire_mapspam.py`. Il extrait chaque ZIP restant vers `MapSPAM zones de production/extrait/<millésime>/`, puis écrit `extrait/manifeste_extraction.csv` (chemin et taille de chaque fichier).
- Dossiers courts par millésime (`spam2005`, `spam2017_ssa`, etc.) pour rester sous la limite de 260 caractères des chemins Windows.
- Aucun fichier source n'est modifié ni supprimé, et une relance saute les ZIP déjà terminés.

#### Problèmes rencontrés et solutions

1. **Premier lancement sans effet.** Le script a trouvé 0 archive, puis a planté en écrivant le manifeste (dossier `extrait/` inexistant). Cause : pendant l'échange, les archives de premier niveau avaient été décompressées à la main et les ZIP d'origine étaient passés dans la Corbeille. Rien n'a été modifié par ce lancement.
2. **Risque de perte de données.** La première version supprimait ses copies intermédiaires de ZIP. Ces ZIP étant devenus les seuls exemplaires hors Corbeille, toute suppression a été retirée du script.
3. **Extraction manuelle partielle.** Les cinq ZIP imbriqués déjà décompressés à la main (quatre de 2000, `harv_area.csv` de 2005) n'ont pas été refaits. Ils restent dans les dossiers d'origine à noms longs et ne figurent pas dans `extrait/` ni dans le manifeste.

#### Résultats

- 52 ZIP extraits, 6 821 fichiers, 209,7 Go, aucun échec.
- Contrôle : les 6 821 fichiers correspondent à leur ZIP source par nom et par taille, et les CRC sont vérifiés à l'extraction.
- Chemin le plus long : 232 caractères.

| Millésime | Fichiers | Volume |
|-----------|----------|--------|
| `spam2000` | 508 | 18,8 Go |
| `spam2005` | 3 271 | 53,7 Go |
| `spam2010` | 1 122 | 61,5 Go |
| `spam2017_ssa` | 1 350 | 51,2 Go |
| `spam2020` | 570 | 24,5 Go |

Lecture de contrôle de `spam2020V2r2_global_P_TA.csv`, colonne `coco`, en tonnes :

| Pays | Production |
|------|-----------|
| Côte d'Ivoire | 2 221 250 |
| Ghana | 881 499 |
| Indonésie | 728 816 |
| Équateur | 304 549 |
| Cameroun | 283 330 |
| Brésil | 276 450 |
| Nigeria | 273 333 |
| Pérou | 153 629 |
| Total mondial | 5 615 585 |

#### Point de vigilance

Ces volumes dépassent nettement ceux de `Projet.docx` pour plusieurs pays (Côte d'Ivoire environ 1,8 Mt, Ghana environ 0,5 Mt, Indonésie environ 0,16 Mt). L'écart n'est pas expliqué à ce stade. Il n'empêche pas d'utiliser MapSPAM pour localiser les cultures à l'intérieur d'un pays, mais les niveaux par pays devront être comparés à une source de référence avant de pondérer entre pays.

#### Prochaines étapes

Inchangées : l'extraction ne fournit toujours aucune série temporelle, le blocage de la phase 1 demeure. L'extrait de 209,7 Go reste hors du dépôt ; seul un fichier réduit aux colonnes cacao serait versionné.

---

### 2026-11-04 — Correction : le dossier « Cacao » est `Projet CACAO`

L'utilisatrice a précisé que le dossier nommé « Cacao » dans le prompt initial est en réalité `Projet CACAO`. Il n'y a donc pas de dossier manquant à retrouver : l'inventaire du jour est complet.

Conséquences :

- Le problème 1 de l'étape 0 (« dossier Cacao introuvable ») est clos.
- Les seules données présentes sont les cartes MapSPAM. Les séries temporelles depuis 2000 annoncées dans le prompt n'existent pas dans ce dossier.
- Les mentions « Dossier Cacao » des sources candidates sont caduques : les prix et la météo doivent venir de sources externes, à valider par l'utilisatrice.

---

### 2026-11-04 — Renommage du dossier MapSPAM

Le dossier des données spatiales s'appelle désormais `MapSPAM zones de production`. Son nom d'origine, supprimé ici de tout le carnet, parlait de « localisation géographique des fermes », ce qui était trompeur : MapSPAM estime par modélisation la production par cellule d'environ 10 km et ne localise pas des fermes individuelles.

- **Rappel :** aucune localisation du cacao n'existe pour 2000. Le premier millésime utile est 2005. L'utiliser pour 2000-2004 serait une approximation à déclarer dans le rapport.
- **Script modifié :** `scripts/00_extraire_mapspam.py` pointe vers le nouveau nom.
- **Contrôle :** `extrait/` contient toujours 209,7 Go. Les 6 874 fichiers comptés sont les 6 821 fichiers extraits, 52 marqueurs de fin et le manifeste. Le manifeste utilise des chemins relatifs et reste valable.

---

### 2026-11-04 — Retrait du millésime MapSPAM 2000

Le millésime 2000 ne contient pas de cacao et a été retiré du projet à la demande de l'utilisatrice pour gagner de la place.

- **Déplacés vers la Corbeille Windows :** `extrait/spam2000` (18,82 Go) et le dossier d'origine du millésime 2000 (5,46 Go). Ils restent récupérables tant que la Corbeille n'est pas vidée.
- **Espace disque :** il ne sera libéré qu'une fois la Corbeille vidée. Ce choix est volontaire : la suppression définitive est laissée à l'utilisatrice.
- **Manifeste régénéré :** `extrait/manifeste_extraction.csv` compte 6 313 fichiers pour 190,9 Go et ne contient plus de ligne `spam2000`. Le tableau de la section sur l'extraction garde les chiffres de l'extraction initiale.
- **Conséquence :** pour remonter avant 2005, la seule option est d'utiliser la carte 2005 comme approximation.

---

### 2026-11-04 — Phase 1 : cadrage à partir de 2005 et revue des sources

**Statut : cadrage terminé, structure en attente de validation, aucune donnée téléchargée.**

#### Démarche

Nouvelles instructions de l'utilisatrice : départ en 2005, six thématiques de données, collecte par scripts pour les sources en ligne, règle stricte contre l'invention de faits. La revue ci-dessous confronte ce plan aux contraintes connues de chaque source.

**Aucune source n'a encore été testée.** Les points de cette revue viennent de connaissances générales et devront être confirmés à la collecte.

#### Inventaire actualisé

- Aucun dossier « Cacao » distinct n'existe sur le Bureau, et le terme désigne ici `Projet CACAO`.
- Aucune série temporelle n'est présente. Le seul jeu de données reste MapSPAM : 190,9 Go dans `extrait/` pour 2005, 2010, 2017 et 2020.
- Outils inchangés : Git absent, Quarto dans Positron uniquement, Python 3.14 seul.

#### Revue des sources par thématique

| Thématique | Données | Sources prévues | Risques à contrôler |
|-----------|---------|-----------------|---------------------|
| 1. Marchés | Cacao, dollar, pétrole, taux, change, actions | Yahoo Finance, banques centrales | Voir ci-dessous |
| 2. Climat | Pluie, température, humidité des sols | NASA POWER, ERA5, Open-Meteo | Agrégation des cellules MapSPAM, quotas des API |
| 3. Offre | Production, bilans, stocks, engrais | FAOSTAT, USDA PS&D, ICCO | Données annuelles publiées avec retard, accès ICCO |
| 4. Investisseurs | Positions CFTC, Google Trends | CFTC, Google Trends | Changement de nomenclature, indice échantillonné |
| 5. Géopolitique | Tensions, événements datés | GDELT, médias de référence | Rupture de série, articles payants |
| 6. Biodiversité | Rendements, révisions de production | FAOSTAT, USDA, ICCO | Variables annuelles lentes |

#### Points de vigilance identifiés

1. **`EUR/XOF` est une parité fixe (655,957 XOF pour 1 euro).** Une série constante n'apporte aucune information au modèle. Le franc CFA devra plutôt être représenté par `EUR/USD`.
2. **`CL=F` a clôturé en négatif en avril 2020.** Un rendement logarithmique serait indéfini ce jour-là. Il faudra un traitement explicite et documenté.
3. **Le cedi a été redénominé en 2007.** Sans contrôle, cela créerait un faux saut de change. Une série ajustée sera nécessaire.
4. **`CC=F` est un contrat continu.** Les changements d'échéance peuvent créer de faux rendements. La redistribution de ces prix sur un site public reste aussi à vérifier.
5. **`MDLZ` précède la scission de Kraft en 2012** si Yahoo fournit l'historique antérieur. Ce début de série ne reflète pas la société actuelle.
6. **Positions CFTC.** Les positions du mardi sont publiées le vendredi, avec un décalage à appliquer. La catégorie Managed Money du rapport désagrégé pourrait ne pas couvrir toute la période depuis 2005, et le rapport historique resterait alors nécessaire pour la continuité.
7. **Google Trends.** L'indice est relatif et échantillonné, et sa granularité dépend de la période demandée. Une série hebdomadaire depuis 2005 doit être reconstruite par raccordement de fenêtres.
8. **GDELT.** Les versions et la profondeur historique diffèrent, ce qui peut créer une rupture. La cohérence depuis 2005 doit être testée avant usage.
9. **USDA PS&D pourrait ne pas couvrir le cacao.** À vérifier en priorité : FAOSTAT et ICCO deviendraient alors les sources principales.
10. **Accès ICCO.** Les bulletins détaillés peuvent être payants. Seules les données réellement accessibles seront utilisées.
11. **Prévisions météo.** Les archives de prévisions historiques ne couvrent pas toute la période depuis 2005. Pour le backtest, seule l'observation disponible à la date de prévision sera utilisée. Les prévisions serviront au signal courant du site, séparément.
12. **ERA5 et Open-Meteo sont des réanalyses :** ce sont des estimations de modèle, disponibles avec quelques jours de retard, qu'il faudra déclarer comme telles.
13. **Variables annuelles dans un modèle hebdomadaire.** Répétée 52 fois par an, une variable lente peut servir au modèle d'horloge du régime de marché et gonfler artificiellement son importance SHAP. Elle doit aussi rester décalée selon sa vraie date de publication.
14. **Événements (thématique 5).** Chaque ligne du calendrier devra porter la date, le fait, la source et l'URL. Les articles payants devront être vérifiés par l'utilisatrice. Aucun événement ne sera ajouté de mémoire.
15. **MapSPAM.** Il donne des zones de production estimées, pas des positions de fermes. Les cartes 2005 et suivantes ont été publiées après leur année de référence. Ces zones évoluent lentement, mais l'hypothèse sera déclarée.
16. **Familles et thématiques.** Le sujet compte sept familles et le plan six thématiques : la demande (fêtes, broyages) n'y a plus de place dédiée et les coûts sont répartis entre les thématiques 1 et 3. Un rattachement de chaque variable à une famille reste nécessaire pour répondre à la problématique avec SHAP.

#### Structure de répertoires actualisée (non créée, remplace la proposition de l'étape 0)

```text
Projet CACAO/
├── carnet_de_bord.md
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   ├── sources.yaml            # URL, couverture, fréquence, retard de publication
│   └── familles.yaml           # Rattachement variable -> famille pour SHAP
├── data/
│   ├── raw/                    # Données brutes, jamais modifiées
│   │   ├── t1_marches/
│   │   ├── t2_climat/
│   │   ├── t3_offre/
│   │   ├── t4_investisseurs/
│   │   ├── t5_geopolitique/    # GDELT + evenements.csv sourcé
│   │   └── t6_biodiversite/
│   ├── interim/                # Séries nettoyées + mapspam_cacao.parquet
│   └── processed/              # Table hebdomadaire finale depuis 2005
├── src/cacao/
│   ├── collecte/               # Un module par thématique
│   ├── nettoyage/              # Nettoyage, imputation
│   ├── alignement/             # Date de disponibilité, passage à l'hebdomadaire
│   ├── variables/              # Variables explicatives et cible
│   ├── modeles/                # Benchmark, RF, GB, walk-forward
│   └── interpretation/         # SHAP par variable et par famille
├── scripts/                    # 00_extraire_mapspam.py, puis une étape par script
├── notebooks/                  # Exploration uniquement
├── tests/                      # Contrôles anti-look-ahead
├── outputs/                    # figures/, modeles/, metriques/
├── site/                       # Projet Quarto
├── Consignes du projet/        # Existant, exclu du dépôt
└── MapSPAM zones de production/  # Existant, exclu du dépôt
```

Le changement principal est le rangement de `data/raw/` par thématique et un fichier `config/familles.yaml`. Le dossier `alignement/` isole la règle centrale de la phase 1 : chaque valeur porte sa date de disponibilité réelle, pas seulement sa date d'observation.

#### Ordre de collecte proposé

1. Thématique 1, indispensable car elle contient la cible.
2. Extrait cacao de MapSPAM, puis thématique 2.
3. Thématique 4 : CFTC d'abord, Google Trends ensuite.
4. Thématiques 3 et 6, qui partagent FAOSTAT.
5. Thématique 5, la plus longue à fiabiliser.

Ce rapport de priorités tient compte de l'oral du 18 novembre.

#### Résultats

Aucune donnée collectée et aucun résultat chiffré à cette étape.

---

### 2026-11-04 — Mise en place du projet et blocage de l'environnement Python

**Statut : structure créée, collecte de la thématique 1 bloquée par Smart App Control.**

L'utilisatrice a confirmé que « dossier Cacao » désigne `Projet CACAO` dans toutes ses instructions. Le dossier n'a pas été renommé, car c'est le dossier de travail de la session.

#### Réalisé

- Structure de répertoires créée, à partir de la proposition de l'étape précédente.
- Fichiers créés : `.gitignore`, `requirements.txt` (versions non figées pour l'instant), `config/t1_marches.yaml` (19 tickers) et `scripts/01_collecter_t1_marches.py`.
- Environnement `.venv` créé en Python 3.14.10, et installation des paquets réussie, y compris `shap`.

Le script de collecte enregistre les valeurs telles que reçues, un CSV par ticker, signale un ticker vide sans le remplacer et produit `outputs/metriques/t1_couverture.csv`. **Il n'a pas encore été exécuté.**

#### Problème rencontré

L'import de pandas échoue avec `ImportError: DLL load failed [...] Une stratégie de contrôle d'application a bloqué ce fichier`. L'import de `shap` échoue pour la même raison, puisqu'il dépend de pandas.

Diagnostic en lecture seule :

- Smart App Control est à l'état `On`.
- Le journal Code Integrity enregistre des événements au moment des échecs.
- `algos.cp314-win_amd64.pyd` n'est pas signé numériquement.

Les scripts d'inspection précédents fonctionnaient car ils n'utilisaient que la bibliothèque standard de Python.

Ce réglage de sécurité n'a pas été modifié et n'a pas été contourné. La décision revient à l'utilisatrice. Tous les paquets scientifiques compilés sont concernés, et pas seulement pandas.

#### Options

| Option | Avantage | Inconvénient |
|--------|----------|--------------|
| Désactiver Smart App Control | Tout fonctionne en local dans Positron | Réduit la protection du PC, retour en arrière impossible sans réinstaller Windows ou le réinitialiser |
| Travailler dans le cloud (Colab, GitHub Codespaces) | Protection du PC conservée | Hors de Positron local ; les données MapSPAM utiles doivent être transférées |

#### Résultats

Aucune donnée téléchargée et aucun résultat chiffré.

---

### 2026-11-04 — Thématique 1 : collecte et contrôle qualité

**Statut : 19 séries téléchargées, aucune nettoyée. Problème majeur sur la variable cible, décision en attente.**

#### Démarche

- L'utilisatrice a désactivé Smart App Control. L'état `Off` a été vérifié et tous les paquets se chargent : pandas 3.1.0, numpy 2.5.4, yfinance 1.8.0, scikit-learn 1.9.1, shap 0.54.1.
- `scripts/01_collecter_t1_marches.py` a été exécuté sans échec. Les CSV bruts sont dans `data/raw/t1_marches/` (9,3 Mo).
- Deux scripts de contrôle ont été créés. Ils ne modifient pas les données : `scripts/02_controler_t1.py` (sortie `outputs/metriques/t1_anomalies.csv`) et `scripts/03_mesurer_echeances_cacao.py` (sortie `outputs/metriques/t1_echeances_cacao.csv`).

#### Couverture

| Groupe | Séries | Début | Fin |
|--------|--------|-------|-----|
| Cacao | `CC=F` | 2005-01-03 | 2026-11-03 |
| Dollar et taux | `DX-Y.NYB`, `^TNX`, `^IRX` | 2005-01-03 | 2026-11-03 |
| Énergie | `CL=F`, `NG=F` | 2005-01-03 | 2026-11-03 |
| Change complet | `EURUSD=X`, `IDR=X`, `NGN=X`, `PEN=X` | 2005-01-03 | 2026-11-04 |
| Change partiel | `BRL=X` | 2006-03-24 | 2026-11-04 |
| Change partiel | `GHS=X` | 2007-07-11 | 2026-11-04 |
| Parité | `EURXOF=X` | 2006-05-16 | 2026-11-04 |
| Chocolatiers | `HSY`, `MDLZ` | 2005-01-03 | 2026-11-03 |
| Chocolatiers | `BARN.SW`, `NESN.SW`, `LISN.SW`, `LISP.SW` | 2005-01-03 | 2026-11-02 |

Le prix du cacao évolue entre 1 318 $/t (août 2005) et 12 565 $/t (décembre 2024). Il finit 2023 à 4 196 $ et 2024 à 11 675 $, ce qui est cohérent avec le triplement décrit dans le sujet.

#### Problème majeur : changements d'échéance dans `CC=F`

`CC=F` conserve parfois un contrat proche de l'expiration alors que le marché est déjà passé au suivant. Au passage, le prix saute sans qu'il y ait eu de vraie variation de marché.

Constats :

- 32,5 % des séances ont moins de 100 contrats échangés, ce qui indique que le volume affiché n'est pas celui du marché.
- 106 passages suspects sont détectés (trois séances sous 100 contrats, puis 1 000 ou plus), soit **4,8 par an**. Cela correspond aux cinq échéances annuelles du cacao, ce qui renforce fortement cette explication.
- Le saut moyen est de 2,7 % sur 2005-2022 et de **7,3 % sur 2023-2026**, avec des sauts de 22,6 % le 16 mai 2024 et de 29,8 % le 16 septembre 2024.
- Neutraliser ces passages change le sens de **28 semaines sur 1 139**, dont 7 sur 2023-2026.

**Limite de la preuve.** Il s'agit d'une déduction solide, pas d'une preuve directe : Yahoo ne fournit pas les contrats expirés (`CCU24.NYB`, `CCZ24.NYB`, etc. renvoient une réponse vide). `CCZ26.NYB` existe, ce qui suggère que seuls les contrats encore cotés sont disponibles.

**Conséquence.** Ces faux sauts seraient appris comme de vrais mouvements et fausseraient la cible et la volatilité, surtout pendant la crise de 2024, précisément la période que le projet veut étudier. Yahoo ne donne pas non plus les contrats ouverts (open interest).

Solutions possibles :

1. Exporter une série continue propre depuis Bloomberg, si l'utilisatrice y a accès (par exemple `CC1 Comdty` avec open interest). La redistribution de ces données sur le site public devra être vérifiée.
2. À défaut, garder `CC=F` et neutraliser les rendements des 106 passages. C'est gratuit, mais moins précis.

#### Autres anomalies

| Séries | Constat | Traitement proposé |
|--------|---------|-------------------|
| `GHS=X`, `IDR=X`, `NGN=X`, `PEN=X`, `EURUSD=X` | Erreurs de cotation : 24 allers-retours sur un jour, dont naira à 1,00, cedi à 573, roupie divisée par 10 | Mettre à NaN puis interpoler, avec revue séparée des vrais sauts (dévaluations) |
| `NGN=X` | 29 sauts quotidiens de plus de 16 %, dont environ 20 dus aux 10 allers-retours | Revue manuelle des sauts restants |
| `EURXOF=X` | **Six valeurs distinctes**, dont 629,957 et 642,957, incompatibles avec une parité fixe | Série écartée, `EUR/USD` retenu |
| `CL=F`, `NG=F`, `^TNX` | Points signalés en mars-avril 2020 et sur le gaz, plausibles comme vrais mouvements | **Ne pas nettoyer**, le filtre automatique ne s'applique pas à ces séries |
| `CL=F` | -37,63 $ le 2020-04-20, cours négatif réel | Pas de rendement logarithmique, méthode à documenter |
| `^IRX` | Proche de zéro et parfois négatif, 763 sauts relatifs sans signification | Utiliser le niveau et les variations en points |
| `MDLZ` | -34 % sur `Close` le 2012-10-02, scission de Kraft | Utiliser `Adj Close` pour les rendements |
| Actions | Une ligne de cotation sans `Close` pour chaque action suisse | Retirer ces lignes à l'alignement |
| Change | Barres du 2026-11-04 incomplètes | Écarter la journée en cours |

Le filtre d'allers-retours ne doit pas être appliqué aveuglément : sur les matières premières et les taux, il signale de vrais mouvements de marché, et ne doit donc servir que pour le change.

#### Suivi des points de vigilance

- Point 1 confirmé, et aggravé : `EURXOF=X` n'est pas constant sur Yahoo, à cause d'erreurs de données.
- Point 2 confirmé : cours négatif de `CL=F`.
- Point 3 : `GHS=X` ne commence qu'en juillet 2007, ce qui évite le saut de redénomination mais laisse un trou de 2,5 ans.
- Point 4 confirmé : c'est le problème majeur ci-dessus.
- Point 5 : à traiter, l'historique de `MDLZ` remonte bien à 2005.

#### Résultats

Données brutes disponibles et contrôlées pour la thématique 1. Aucun nettoyage ni modèle à ce stade.

---

### 2026-11-04 — Contrôle croisé du cacao avec la Banque mondiale

**Statut : `CC=F` validé en moyenne mensuelle, conclusion de l'entrée précédente corrigée.**

Sur proposition de l'utilisatrice, `CC=F` a été comparé à une source indépendante pour tester l'hypothèse des changements d'échéance.

#### Démarche

- `scripts/04_telecharger_controles_cacao.py` : téléchargement du Pink Sheet de la Banque mondiale, série cacao (ICCO), dans `data/raw/t1_marches/controle/`.
- `scripts/05_controle_croise_cacao.py` : comparaison mensuelle, avec sortie dans `outputs/metriques/t1_controle_mensuel.csv`.
- Paquet ajouté : `openpyxl`.

**Limites du contrôle.** Le prix de la Banque mondiale n'a pas la même définition que `CC=F` et il est mensuel. Un écart est donc normal, et ce contrôle ne valide pas les mouvements hebdomadaires.

**Sources non utilisées.** FRED (`PCOCOUSDM`) n'a pas répondu aux deux tentatives. Barchart n'a pas été utilisé, car ce site demande en général un compte et limite l'extraction automatique. Il n'y a donc qu'une seule source de contrôle.

#### Résultats

- **Aucun trou** : 262 mois comparés de 2005-01 à 2026-10, sans valeur manquante.
- **Variations mensuelles proches** : corrélation de 0,953, même sens dans 92 % des mois.

| Période | Écart absolu moyen CC=F / contrôle | Écart maximal |
|---------|-----------------------------------|---------------|
| 2005-2022 | 2,8 % | 11,2 % |
| 2023 | 1,4 % | 5,4 % |
| **2024** | **12,5 %** | **33,4 %** |
| 2025 | 5,3 % | 15,2 % |
| 2026 | 2,0 % | 3,6 % |

#### Correction de l'entrée précédente

Neutraliser les passages d'échéance **éloigne** `CC=F` du contrôle mensuel :

| Série testée | Passages | Corrélation 2005-2026 | Écart-type 2005-2026 | Corrélation 2023-2026 |
|--------------|----------|----------------------|----------------------|----------------------|
| **`CC=F` brut** | 0 | **0,953** | **2,36 pts** | **0,940** |
| Sauts > 15 % | 2 | 0,945 | 2,53 pts | 0,927 |
| Sauts > 10 % | 3 | 0,945 | 2,52 pts | 0,928 |
| Sauts > 5 % | 19 | 0,934 | 2,83 pts | 0,920 |
| Tous | 106 | 0,926 | 2,98 pts | 0,918 |

La recommandation de neutraliser ces passages est donc **retirée**, et le qualificatif de « faux sauts » était trop fort. Les passages sont bien réels dans les données, mais le saut est en partie le rattrapage d'un écart entre contrats, pas une pure erreur à effacer. Un filtre de neutralisation retire aussi le vrai mouvement du jour.

#### Le cas de 2024

La remarque de l'utilisatrice est confirmée par les données :

- **Volatilité annualisée hors passages :** 63 % en 2024, contre 17 % à 39 % sur 2005-2023. Elle reste élevée ensuite, à 53 % en 2025 et 59 % en 2026. Il s'agit d'un changement de régime durable, pas d'une seule année atypique.
- **Écart à la référence :** `CC=F` dépasse le contrôle de 30 % en août 2024 et de 33 % en septembre 2024, quand les volumes affichés sont quasi nuls.
- **Sauts surtout négatifs :** -7,8 %, -18,5 %, -6,7 % et -22,9 % sur quatre passages de 2024. Le saut moyen est de -6,8 % sur 2024-2025, contre -0,1 % sur 2005-2022.

Ces sauts négatifs sont cohérents avec un marché où le contrat proche vaut nettement plus que les suivants (déport). C'est une interprétation, à confirmer avec un article de référence ou des prix par échéance.

#### Décision proposée

1. Garder `CC=F` brut comme série de prix.
2. Ne neutraliser aucun passage automatiquement.
3. Marquer les semaines de passage et les exclure à titre de test de robustesse, en comparant les résultats avec et sans elles.
4. Considérer 2024-2026 comme un régime à part : un modèle entraîné avant 2024 n'a jamais vu ce niveau de volatilité.
5. Garder Bloomberg comme option pour obtenir les contrats ouverts, que Yahoo ne fournit pas.

---

### 2026-11-04 — Décision de fréquence et grille quotidienne

**Statut : grille de la thématique 1 construite et testée. Modèles non commencés.**

#### Décision

L'utilisatrice retient un dataset **quotidien**, sur les séances de `CC=F` depuis 2005, avec **deux horizons de prévision : 1 séance et 20 séances**. La série `CC=F` brute est conservée comme prix du cacao.

Arguments discutés :

- Un test à 1 séance est très bruité et favorise les variables rapides. L'importance des facteurs doit donc être comparée entre les horizons.
- Le niveau de prix n'est pas une bonne cible : « demain = aujourd'hui » donne déjà un R² très élevé sans aucune compétence réelle.
- La comparaison entre horizons pourra montrer si le facteur dominant dépend de l'horizon.

#### Méthode

- **Fichiers créés :** `src/cacao/grille.py`, `scripts/06_construire_grille_quotidienne.py`, `tests/test_grille.py`. `pytest` ajouté aux dépendances.
- **Axe temporel :** les 5 489 séances de `CC=F`, du 2005-01-03 au 2026-11-03.
- **Alignement :** pour chaque séance, chaque variable prend sa dernière valeur **strictement antérieure**. Cette règle couvre le cas des marchés fermant après le cacao, dont les horaires exacts restent à vérifier.
- **Prix des actions :** `Adj Close`, pour la continuité des rendements. Seuls les rendements devront être utilisés, car le niveau ajusté dépend de dividendes futurs.
- **Change :** erreurs de cotation retirées, `EURXOF=X` écarté.
- **Cibles :** hausse et rendement à 1 et 20 séances, volatilité réalisée sur 20 séances. Une égalité de prix compte comme « pas de hausse ».
- **Indicateurs conservés :** volume nul, volume faible, saut d'échéance, passage dans la fenêtre de prévision.

#### Écart à la règle d'imputation

L'interpolation temporelle a été écartée : combler un trou en interpolant utiliserait la valeur suivante, donc une information future. Les trous sont comblés par la **dernière valeur connue**, dans la limite de 10 jours. Au-delà, ou avant le début d'une série, la valeur reste manquante. Rien n'est inventé ni rempli à rebours.

#### Résultats

La grille compte 5 489 lignes et 29 colonnes (`data/processed/grille_quotidienne_t1.parquet`).

| Cible | Lignes | Part de hausses | Fenêtres avec passage d'échéance |
|-------|--------|-----------------|----------------------------------|
| 1 séance | 5 488 | 50,8 % | 1,9 % |
| 20 séances | 5 469 | 53,6 % | 38,6 % |

Ces proportions sont la barre à battre : prédire toujours « hausse » donnerait déjà ces scores sur l'historique complet.

- **Volatilité future à 20 séances :** médiane 27,5 %, maximum 130 %.
- **Valeurs manquantes :** `ghs_x` 11,51 % (absent avant juillet 2007) et `brl_x` 5,83 %. Depuis 2008, elles sont de 0,25 % ou moins partout.
- **Change :** 24 erreurs retirées, sur `EURUSD=X` (1), `GHS=X` (6), `IDR=X` (5), `NGN=X` (10) et `PEN=X` (2).
- **Tests :** 10 sur 10 réussis, dont la vérification que modifier le futur ne change pas le passé et que la grille correspond à la source brute.

#### Limites et points ouverts

1. **14 sauts de change restent à examiner :** `GHS=X` (1), `IDR=X` (4, entre le 29 novembre et le 10 décembre 2013) et `NGN=X` (9). Ils peuvent être de vraies dévaluations ou des erreurs, et ils sont encore dans la grille.
2. **Le filtre du change utilise le lendemain** pour reconnaître un aller-retour. Cette petite part d'information future est limitée par le décalage d'une séance, mais elle doit être déclarée.
3. **38,6 % des fenêtres à 20 séances contiennent un passage.** Toutes les exclure retirerait trop de données. Le test de robustesse devra plutôt viser les grands sauts.
4. **Cette grille ne contient que la thématique 1.** Les thématiques 2 à 6 et les variables explicatives transformées restent à construire.
5. **`requirements.txt` n'est pas encore figé par versions.**

---

### 2026-11-04 — Plan d'analyse des facteurs et configuration de Positron

**Statut : plan validé par l'utilisatrice, environnement déclaré.**

#### Plan validé

Les variables de chaque famille sont adaptées à l'horizon : changements et surprises récentes pour 1 séance, niveaux et cumuls pour 20 séances. La biodiversité n'est pas forcée à 1 séance, car les rendements annuels ne bougent pas d'un jour à l'autre.

**Les pondérations ne sont pas fixées à la main.** Cela imposerait la réponse à la problématique et introduirait un look-ahead si les poids étaient choisis en connaissant 2024. L'analyse suit quatre étapes :

1. Un modèle par horizon, qui apprend ses poids sur le passé.
2. SHAP agrégé par famille, pour comparer les sept familles à 1 et 20 séances.
3. Retrait d'une famille à la fois, pour mesurer sa contribution au score malgré les variables corrélées.
4. Réentraînement chronologique, pour observer l'évolution des poids avant et après 2024.

Ces poids mesurent une utilité prédictive et ne prouvent pas une causalité.

#### Environnement Positron

Positron signalait l'absence d'environnement dédié alors que `.venv` existait déjà. Aucun nouvel environnement n'a été créé, pour éviter un doublon.

- `.venv` vérifié : Python 3.14.10 et imports réussis.
- Fichier créé : `.vscode/settings.json`, qui désigne `.venv` comme interpréteur du projet.
- Paquet ajouté : `ipykernel`.

---

### 2026-11-04 — FAOSTAT et comparaison avec MapSPAM

**Statut : FAOSTAT collecté. Écart avec `Projet.docx` en grande partie expliqué, sauf l'Indonésie. Thématique 3 encore incomplète.**

L'utilisatrice a demandé si les chiffres de production de MapSPAM contredisaient les autres sources. La thématique 3 n'étant pas collectée, FAOSTAT a été téléchargé pour répondre sur pièces.

#### Démarche

- `scripts/07_collecter_faostat_cacao.py` : archive complète (33,9 Mo) et extrait `data/raw/t3_offre/faostat_cacao.csv`, soit 15 194 lignes de production, surface et rendement, de 1961 à 2024.
- `scripts/08_comparer_faostat_mapspam.py` : comparaison par pays, sortie dans `outputs/metriques/t3_comparaison_faostat_mapspam.csv`.
- Erreur corrigée : le fichier FAOSTAT était lu avec le mauvais encodage (« CÃ´te d'Ivoire »). Il est désormais lu en UTF-8.

#### Résultats

MapSPAM et FAOSTAT sont presque identiques une fois FAOSTAT moyenné sur trois ans autour de l'année du millésime :

| Monde | MapSPAM | FAOSTAT, moyenne 3 ans | Écart |
|-------|---------|------------------------|-------|
| 2005 | 4 137 459 t | 4 137 848 t | 0,0 % |
| 2010 | 4 384 349 t | 4 364 614 t | 0,5 % |
| 2020 | 5 615 585 t | 5 658 352 t | -0,8 % |

Les écarts par pays sont en général inférieurs à 0,5 %. Les exceptions sont l'Équateur en 2010 (+14,7 %), le Nigeria (-7,6 %), le Cameroun (-6,2 %) et l'Indonésie (+3,8 %) en 2020.

**Cette concordance n'est pas une confirmation indépendante.** Sa précision suggère que MapSPAM est calé sur les statistiques FAOSTAT, comme l'indique le ReadMe de SPAM 2000 (`source` toujours égal à « F » pour FAO). Les deux sources partagent donc leurs éventuelles erreurs.

#### Écart avec `Projet.docx`

L'écart relevé plus tôt venait surtout des années comparées : `Projet.docx` est proche des années récentes, pas de 2020. La production mondiale recule de 5,62 Mt en 2022 à 5,12 Mt en 2023.

| Pays | `Projet.docx` | FAOSTAT 2024 | MapSPAM 2020 |
|------|---------------|--------------|--------------|
| Côte d'Ivoire | ~1,8 Mt | 1,89 Mt | 2,22 Mt |
| Ghana | ~0,5 Mt | 0,53 Mt | 0,88 Mt |
| Équateur | ~0,43 Mt | 0,40 Mt | 0,30 Mt |
| Nigeria | ~0,315 Mt | 0,35 Mt | 0,27 Mt |
| Cameroun | ~0,30 Mt | 0,32 Mt | 0,28 Mt |
| Pérou | ~0,15 Mt | 0,16 Mt | 0,15 Mt |
| **Indonésie** | **~0,16 Mt** | **0,63 Mt** | **0,73 Mt** |

**L'Indonésie reste un vrai désaccord**, d'un facteur 4 environ, et ne s'explique pas par l'année. La cause est inconnue à ce stade. Un contrôle avec l'ICCO sera nécessaire avant de pondérer l'Indonésie face aux autres pays.

#### Conséquences

- La localisation **à l'intérieur d'un pays** reste utilisable avec MapSPAM.
- Pour la pondération **entre pays**, une carte figée serait insuffisante, car les parts changent nettement : la Côte d'Ivoire passe de 33 % en 2005 à 39 % en 2020, le Nigeria de 10,8 % à 4,9 %, l'Équateur de 2,2 % à 5,4 %.
- Les valeurs FAOSTAT sont des données révisées et sont publiées avec retard. Elles devront entrer dans le modèle avec un décalage prudent, à documenter.

#### Reste à collecter pour la thématique 3

USDA PS&D, bilans et stocks ICCO, engrais. Le Pink Sheet déjà téléchargé devrait contenir des prix d'engrais, ce qui reste à vérifier.

---

### 2026-11-04 — Comparaison avec l'ICCO

**Statut : tableaux ICCO collectés et comparés. Le désaccord sur l'Indonésie est confirmé comme un écart entre sources. Historique ICCO incomplet.**

#### Démarche

- `scripts/09_collecter_icco_production.py` : 23 tableaux de production publics des bulletins trimestriels (QBCS), dans `data/raw/t3_offre/icco/`.
- `scripts/10_comparer_icco.py` : extraction de 342 valeurs issues de 13 éditions lisibles, avec leur date de publication, dans `data/interim/icco_production_editions.csv`. Comparaison dans `outputs/metriques/t3_comparaison_icco.csv`.
- Paquet ajouté : `pypdf`.

Le script refuse toute ligne dont le nombre de valeurs ne correspond pas aux saisons. Ce contrôle a arrêté plusieurs lectures fautives (saisons écrites « 2022 / 23 », dates coupées, pourcentages, note de bas de page collée), toutes corrigées.

**Convention de comparaison.** La saison 2022/23 est comparée à l'année FAOSTAT 2023. Ce rapprochement est imparfait, et une partie des écarts annuels peut en venir.

#### Résultats

| Pays (kt, saison 2023/24 et FAOSTAT 2024) | ICCO | FAOSTAT | FAOSTAT / ICCO |
|-------------------------------------------|------|---------|----------------|
| Côte d'Ivoire | 1 674 | 1 890 | 1,13 |
| Ghana | 449 | 530 | 1,18 |
| Équateur | 419 | 404 | 0,96 |
| Nigeria | 350 | 350 | 1,00 |
| Cameroun | 320 | 320 | 1,00 |
| Brésil | 182 | 298 | 1,63 |
| **Indonésie** | **180** | **633** | **3,52** |
| **Monde** | **4 368** | **5 233** | **1,20** |

- **Indonésie :** le rapport FAOSTAT / ICCO reste entre 3,5 et 4 sur les quatre saisons comparées. L'écart est donc structurel. La valeur de 0,16 Mt de `Projet.docx` est le chiffre de l'ICCO pour 2022/23.
- **Monde :** FAOSTAT dépasse l'ICCO de 2 % à 20 %. En 2023/24, l'écart de 865 kt vient surtout de l'Indonésie (453), de la Côte d'Ivoire (216), du Brésil (116) et du Ghana (81).
- **Moyenne de 2020/21 et 2021/22 contre MapSPAM 2020 :** MapSPAM suit FAOSTAT et hérite de l'écart sur l'Indonésie (729 kt contre 175 kt à l'ICCO). 2019/20 n'est pas disponible.
- **Choc de l'offre :** l'ICCO montre 5 016 kt en 2022/23 puis 4 368 kt en 2023/24, soit -12,9 %. La part de la Côte d'Ivoire et du Ghana passe de 57,7 % à 48,6 %.

#### Explication possible pour l'Indonésie (non confirmée)

D'après une source de presse indonésienne (Bisnis), l'association de l'industrie du cacao préfère les chiffres de l'ICCO à ceux du gouvernement. L'article oppose 561 444 t selon l'institut statistique à 220 000 t selon l'ICCO pour 2018. Le chiffre ICCO concorde avec notre édition pour 2018/19. Le rapprochement n'a pas été vérifié dans une source primaire, et aucune réconciliation officielle ICCO-FAOSTAT n'a été trouvée.

Source : https://ekonomi.bisnis.com/read/20200210/257/1199701/asosiasi-industri-kakao-meragukan-data-bps-ini-alasannya

#### Révisions et look-ahead

Les éditions ICCO montrent ce qui était connu à leur date de publication :

| Saison | Première valeur | Dernière valeur |
|--------|-----------------|-----------------|
| Ghana 2023/24 | 580 (février 2024) | 449 (mai 2025) |
| Ghana 2022/23 | 750 (février 2023) | 654 (mai 2025) |
| Côte d'Ivoire 2023/24 | 1 800 (février 2024) | 1 674 (mai 2025) |

Utiliser les chiffres finaux de 2023/24 dans un backtest de début 2024 serait du look-ahead. Les éditions datées permettent de l'éviter.

#### Limites

- Éditions lisibles : mai à novembre 2019, puis février 2023 à mai 2025.
- Dix PDF sont des images, non exploités à ce stade. Ils pourraient couvrir une partie de 2020-2022.
- Aucun tableau public n'a été trouvé avant 2019 dans les URL testées, ni après mai 2025. Selon l'ICCO, les statistiques complètes récentes passent par un abonnement.
- La valeur 2024/25 du tableau est une prévision.

#### Décision proposée

| Besoin | Source proposée |
|--------|-----------------|
| Localisation dans un pays | MapSPAM |
| Pondération entre pays | ICCO quand disponible, à défaut FAOSTAT, avec test de sensibilité sur l'Indonésie |
| Chocs d'offre 2016-2025 | Éditions ICCO datées |
| Historique 2005-2016, rendements (thématique 6) | FAOSTAT |

Pages ICCO : https://www.icco.org/statistics/

---

### 2026-11-04 — Indonésie : FAOSTAT contre MapSPAM

`scripts/11_indonesie_faostat_mapspam.py` compare production, surface récoltée et rendement. Sortie : `outputs/metriques/t3_indonesie_faostat_mapspam.csv`. MapSPAM 2017 ne couvre pas l'Indonésie.

| Millésime | Production MapSPAM | FAOSTAT moy. 3 ans | Écart | Surface MapSPAM | FAOSTAT moy. 3 ans | Écart |
|-----------|-------------------|-------------------|-------|-----------------|-------------------|-------|
| 2005 | 736 704 t | 736 639 t | 0,0 % | 1 054 484 ha | 1 054 579 ha | 0,0 % |
| 2010 | 788 732 t | 788 803 t | 0,0 % | 1 657 072 ha | 1 657 092 ha | 0,0 % |
| 2020 | 728 816 t | 702 022 t | +3,8 % | 1 522 450 ha | 1 496 971 ha | +1,7 % |

Le rendement est identique en 2005 (699 kg/ha) et en 2010 (476 kg/ha), et proche en 2020 (479 contre 469 kg/ha). MapSPAM reprend donc FAOSTAT : ce sont deux présentations d'une même base, et les deux s'opposent à l'ICCO.

Points à contrôler :

- **Écart de 2020 :** l'hypothèse est une révision de FAOSTAT après le calage de MapSPAM. Une publication citant FAOSTAT donne environ 728 000 t en 2021, contre 650 612 t aujourd'hui. Non vérifié.
- **2021 et 2022 identiques dans FAOSTAT** (650 612 t et 1 421 014 ha), ce qui ressemble à une valeur reconduite.
- **Rupture en 2005-2006 :** la surface tombe de 1 167 046 à 905 730 ha alors que le rendement passe de 642 à 850 kg/ha. Cela pourrait être une rupture de série, à examiner avant d'utiliser ces rendements en proxy (thématique 6).

---

### 2026-11-04 — Arbitrage méthodologique : séparation des rôles des sources

**Statut : arbitrage décidé par l'utilisatrice.**

#### Décision

| Rôle | Source | Usage |
|------|--------|-------|
| **Temporel et inter-national** | FAOSTAT, ou USDA si le cacao y figure | Source unique des volumes nationaux depuis 2005, variables de production du modèle, poids de chaque pays dans l'indice météo mondial |
| **Spatial et intra-national** | MapSPAM | Localisation des grilles de culture et densité du cacao dans chaque pays, uniquement |

La météo (pluie, température, humidité des sols, via NASA POWER ou Open-Meteo) est extraite sur les coordonnées MapSPAM. Elle est agrégée au niveau national par une moyenne pondérée par la densité MapSPAM, puis au niveau mondial par les poids FAOSTAT. Une sécheresse en zone dense pèse donc plus qu'une sécheresse en zone marginale.

#### Précisions à conserver

- **Nature du désaccord.** L'arbitrage parle d'un décalage FAOSTAT / MapSPAM, mais ces deux sources coïncident presque pour l'Indonésie. Le désaccord réel oppose FAOSTAT à l'ICCO (633 kt contre 180 kt en 2023/24). L'arbitrage reste valable, mais il tranche ce désaccord en faveur de FAOSTAT.
- **Test de sensibilité à garder.** L'Indonésie pèse environ 12 % selon FAOSTAT 2024 et 4 % selon l'ICCO 2023/24. L'indice météo mondial devra être recalculé avec les poids ICCO, au moins sur les saisons disponibles, pour vérifier que les conclusions ne dépendent pas de ce choix.
- **Look-ahead sur les poids.** FAOSTAT est annuel, révisé et publié avec retard. Le poids d'une date doit venir d'une année déjà publiée à cette date, avec un décalage prudent à documenter.
- **USDA.** La présence du cacao dans PS&D n'est toujours pas vérifiée.
- **Données FAOSTAT.** Les anomalies de l'Indonésie (2021-2022 identiques, rupture de surface en 2005-2006) restent à surveiller.

---

### 2026-11-04 — Extraction spatiale du cacao et anomalie MapSPAM 2020 au Cameroun

**Statut : cellules extraites et contrôlées. Le millésime de référence reste à décider. Aucune météo téléchargée.**

#### Démarche

`scripts/12_extraire_cellules_cacao.py` extrait les cellules de cacao de 2005, 2010, 2017 (Afrique seulement) et 2020. Il calcule la densité dans chaque pays et les regroupe en mailles de 0,25 degré.

- `data/interim/mapspam_cacao.parquet` : cellules de 5 minutes d'arc (71 142 en 2020 pour le monde).
- `data/interim/points_meteo_cacao.parquet` : mailles de 0,25 degré.
- Contrôle : la densité somme à 1 dans chaque pays et millésime. Pour 2005, toutes les cellules ont retrouvé leurs coordonnées.

#### Problème majeur : le Cameroun en 2020

Le contrôle de stabilité a donné 0 % de zones communes entre 2020 et les millésimes antérieurs.

| Millésime | Centre de gravité du cacao au Cameroun |
|-----------|---------------------------------------|
| 2005 | 3,95° N, 12,12° E |
| 2010 | 4,28° N, 11,64° E |
| 2017 | 4,57° N, 11,07° E |
| **2020** | **9,38° N, 13,96° E** |

MapSPAM 2020 place 79,3 % du cacao camerounais dans le Nord et 20,7 % dans l'Extrême-Nord, et rien dans le sud forestier. Trois millésimes antérieurs concordent contre celui-ci. Il s'agit très probablement d'une erreur d'affectation dans le fichier 2020. **Le Cameroun 2020 ne doit pas être utilisé.** Sans ce contrôle, la météo du Cameroun aurait été lue dans la mauvaise zone climatique.

#### Autres résultats

- **Indonésie 2020 :** les provinces de Sulawesi concentrent **60,2 %** du cacao (Central 17,6 %, South 16,3 %, South-East 15,8 %, West 9,7 %). Sumatra pèse environ un quart : West Sumatera 7,3 %, Lampung 7,1 %, Aceh 5,2 %, North Sumatera 4,5 %. L'exemple de l'arbitrage est donc confirmé, sous réserve de la limite ci-dessous.
- **Brésil 2020 :** Pará 49,8 % et Bahia 43,6 %. Un centre de gravité n'a pas de sens géographique dans ce pays : il faut bien des points séparés.
- **Stabilité entre 2010 et 2020 :** elle varie de 27 % à 84 % selon le pays, y compris hors Cameroun. L'indicateur est strict, car il est mesuré maille par maille, et l'affectation MapSPAM est modélisée. Il ne faut donc pas surinterpréter le détail d'une maille.

**Limite.** Comme le fichier 2020 du Cameroun est faux, les autres pays de ce millésime méritent aussi un contrôle, même si leurs centres de gravité paraissent cohérents.

#### Charge de collecte météo

| Mailles de 0,25° retenues (2020) | Points |
|----------------------------------|--------|
| Toutes | 6 969 |
| 95 % de la production de chaque pays | 2 042 |
| 90 % | 1 535 |
| 80 % | 1 008 |

Ces chiffres couvrent neuf pays et incluent les mailles erronées du Cameroun. Interroger 2 000 points sur plus de 20 ans dépassera probablement ce qu'une API gratuite accepte facilement. Les limites réelles restent à vérifier, et une réduction du nombre de points ou une grille plus large sera sans doute nécessaire.

#### Décision à prendre

Quel millésime fixe la densité intra-nationale ? Proposition : **2010 comme référence**, le plus prudent contre le look-ahead puisqu'il précède la crise et la plus grande partie du test, et 2020 corrigé (Cameroun remplacé par 2017) comme test de sensibilité. Limite : 2010 reflète moins bien la montée récente du Pará, de l'Équateur et du Pérou.

---

### 2026-11-05 — Arbitrage : MapSPAM 2010 et réduction des points météo

**Statut : arbitrage décidé par l'utilisatrice.**

- **Référence :** MapSPAM 2010 est l'unique baseline de densité pour tout l'historique 2005-2026. Les évolutions récentes de volume passent par les séries annuelles FAOSTAT.
- **Sensibilité :** MapSPAM 2020 corrigé (Cameroun remplacé par 2017) sera utilisé en phase 4 sur la période récente.
- **Volume :** extraction limitée aux zones couvrant 80 % de la production. Si besoin, regroupement spatial (k-means) vers 300 à 400 points.

**Nuance sur l'étanchéité.** Une carte fixe supprime l'effet d'un changement de carte à l'approche de la crise, mais elle ne donne pas une garantie absolue contre le look-ahead. Le fichier 2010 a été publié après 2010 et il est appliqué à 2005-2009. Le risque est faible, car la localisation évolue lentement, et il sera déclaré comme hypothèse dans le rapport.

---

### 2026-11-05 — Thématique 2 : sélection des points météo et collecte NASA POWER

**Statut : collecte terminée, 349 points sur 349. Traitement de la pluie à arbitrer.**

**Sélection (`scripts/13_selectionner_points_meteo.py`).** Depuis MapSPAM 2010, on garde par pays les mailles de 0,25° les plus denses jusqu'à 80 % de la production, soit 877 mailles. Un k-means pondéré par pays (`random_state=42`) les réduit à 349 points : CIV 46, GHA 35, IDN 57, ECU 30, CMR 44, BRA 42, NGA 37, PER 34, DOM 24. Chaque point porte un poids qui somme à 1 par pays. La distance moyenne à un centre va de 0 à 21 km, le maximum est de 107,8 km en Indonésie.

**Limite de résolution.** Ces 349 points tombent dans seulement 235 cellules natives MERRA-2 (0,5 × 0,625°). 103 points ont une pluie strictement identique à celle d'un autre. Ce sont des doublons d'information, pas une erreur.

**Choix de la source.** Test sur un point : NASA POWER répond. Open-Meteo fonctionne aussi, mais coûte 341,8 unités par point pour 6 variables, avec une limite de 600 par minute. NASA POWER devient la source principale, Open-Meteo (ERA5) le contrôle.

**Collecte (`scripts/14_collecter_meteo_nasa.py`).** Sept variables quotidiennes de 2005 à novembre 2026 : `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `GWETROOT`, `GWETTOP`. Le premier passage a pris environ 2 h à cause de coupures répétées du serveur (erreur 10054). Il a donné 334 points. Trois relances ont récupéré les 15 autres. Le script reprend sans retélécharger, et le code -999 devient une valeur vide. Aucun manquant avant 2026 ; le dernier jour complet est le 2026-11-02, soit environ trois jours de retard.

### 2026-11-06 — Contrôle de la météo : anomalie sur la pluie NASA POWER

**Statut : anomalie mesurée, cause non établie.**

**Constat.** Toutes les pluies quotidiennes supérieures à 300 mm tombent entre 2020 et 2023.

| Période | Jours-point > 200 mm | Jours-point > 300 mm | Maximum |
|---|---:|---:|---:|
| 2005-2019 | 5 | 0 | 247 mm |
| 2020-2023 | 62 | 30 | 790 mm |
| 2024-2026 | 14 | 0 | 270 mm |

> **Correction du 2026-11-06.** Le contrôle ci-dessous n'est pas de l'ERA5 pur. Sans le paramètre `models=era5`, Open-Meteo renvoie un mélange de modèles. À IDN_013, la série par défaut est identique à ERA5 jusqu'en 2016, puis s'en écarte à partir de 2017 : 4,7 mm/jour contre 8,2 mm/jour en 2020-2023, corrélation 0,45. Les températures, l'humidité et les ratios de pluie par période de ce contrôle sont donc à refaire, et les changements de niveau cités plus bas ne sont pas établis. Le pic de 790 mm reste isolé : ERA5 pur donne 15,0 mm ce jour-là.

**Résultat partiel ERA5 pur (`scripts/18_collecter_pluie_era5.py`, `scripts/19_comparer_pluie_era5.py`), 83 points, surtout CIV et GHA.** Le ratio de pluie NASA/ERA5, en moyenne simple des points, change de niveau en 2020 : CIV 1,18 en 2017-2019 puis 1,57 en 2020-2023 et 1,43 en 2024-2026 ; GHA 1,12 puis 1,52 et 1,68. Il était stable entre 2005-2016 et 2017-2019. Le décalage persiste après 2023. Cela montre qu'une des deux séries a changé, sans dire laquelle. Sur les 7 jours-point NASA au-dessus de 300 mm de cet échantillon, ERA5 donne au plus 14,5 mm. ERA5 a aussi ses pics propres, jusqu'à 280,5 mm au Ghana.

**Résultat ERA5 pur à 254 points (CIV, GHA, IDN, ECU, CMR, BRA).** La collecte s'est arrêtée sur la limite quotidienne de l'API (« Daily API request limit exceeded ») ; il reste NGA, PER et DOM, soit 95 points. Le décalage de 2020 n'est pas général. Il touche surtout la Côte d'Ivoire et le Ghana. Le Brésil baisse (1,04 en 2017-2019, 0,91 puis 0,77). L'Indonésie (0,78 ; 0,86 ; 0,80), le Cameroun (0,94 ; 1,10 ; 0,91) et l'Équateur (0,40 ; 0,42 ; 0,43) ne montrent pas de rupture nette. L'Équateur a un écart structurel, avec une NASA à environ 40 % d'ERA5. La corrélation mensuelle reste élevée partout (0,70 à 0,95). Sur 29 jours-point NASA au-dessus de 300 mm, ERA5 donne une médiane de 10,9 mm et un maximum de 49,7 mm.

**Troisième source : CHIRPS v2.0 mensuel (`scripts/20_collecter_chirps.py`, `scripts/21_comparer_trois_pluies.py`).** Choisi pour départager NASA et ERA5, car il combine satellites et stations. IMERG via POWER a été écarté : la série revient vide. L'en-tête POWER indique `MERRA2` et `GEOSIT` comme sources de `PRECTOTCORR`. La collecte via l'IRI Data Library est lente : 40 points en 5 heures, avec des coupures, et le PC peut aussi avoir joué. Le script parcourt maintenant les pays à tour de rôle, du point le plus lourd au plus léger. Résultat provisoire sur 40 points de Côte d'Ivoire : NASA/CHIRPS 1,04 ; 1,11 ; 1,25 ; 0,98 et ERA5/CHIRPS 0,83 ; 0,92 ; 0,78 ; 0,68 sur 2005-2016, 2017-2019, 2020-2023, 2024-2026. Les deux bougent, donc le test ne tranche pas encore. CHIRPS est mensuel et ne juge pas les pics quotidiens.

Mise à jour à 44 points communs, soit un seul point pour BRA, CMR, ECU et GHA, donc résultat fragile. Corrélation mensuelle avec CHIRPS en 2020-2023 : NASA 0,79 (CIV), 0,69 (CMR), 0,60 (ECU), contre 0,91, 0,86 et 0,76 pour ERA5. NASA recule par rapport à 2017-2019, ERA5 non. Le ratio NASA/CHIRPS au Ghana monte de 1,02 à 1,41. Le ratio ERA5/CHIRPS baisse depuis 2017-2019 en CIV (0,92 à 0,68) et GHA (0,92 à 0,66), ce qui signale une dérive possible d'ERA5 ou de CHIRPS. En Équateur, ERA5 vaut 2,7 à 4,5 fois CHIRPS sur ce point : niveau non fiable, à traiter en anomalies. Le débit tombe à 5 points en 4 h 30 : la collecte CHIRPS complète n'est pas réaliste à ce rythme.

**Décision et extension du périmètre (2026-11-06).** L'utilisatrice préfère attendre CHIRPS avant de choisir la pluie. Elle rappelle que la météo ne se limite pas à la pluie et demande d'intégrer les incendies, ainsi que l'empoisonnement des sols pour la biodiversité.
- **Déjà collecté :** température moyenne, maximale et minimale, humidité de l'air et des sols. Leur contrôle reste à refaire avec de l'ERA5 pur.
- **À ajouter :** rayonnement solaire et vent, déficit de pression de vapeur calculé, et indice ENSO. Sources à confirmer au moment de la collecte.
- **Incendies :** NASA FIRMS, archives annuelles par pays depuis 2000 pour MODIS selon des documentations tierces, à vérifier sur le site officiel.
- **Sols :** aucune série quotidienne connue. Pistes : rendements FAOSTAT, pesticides et engrais annuels, événements datés et sourcés. Une étude du district de Fanteakwa (Ghana) mesure mercure et cadmium dans les sols de cacao, avec des fèves dans les limites : c'est une étude ponctuelle, pas une série. Le virus du swollen shoot et l'orpaillage illégal sont cités comme causes de la crise, à recouper avec des médias de référence.

**CHIRPS complet (2026-11-07, `scripts/25_telecharger_chirps_global.ps1`, `scripts/26_extraire_chirps_global.py`).** Le fichier mondial de 7,76 Go a été téléchargé en une vingtaine de minutes, à environ 8,5 Mo/s. L'extraction mois par mois prend 21 minutes, une première lecture point par point avait été arrêtée après 43 minutes. Résultat : 261 mois de janvier 2005 à septembre 2026. IDN_008 et IDN_013 n'ont aucune donnée, probablement des pixels hors terre, et sont retirés de la comparaison. Comparaison sur 252 points de 6 pays, poids MapSPAM ; NGA, PER et DOM attendent ERA5.

| Ratio à CHIRPS | 2005-2016 | 2017-2019 | 2020-2023 | 2024-2026 |
|---|---:|---:|---:|---:|
| NASA, CIV | 1,03 | 1,10 | 1,23 | 0,97 |
| NASA, GHA | 0,98 | 1,13 | 1,23 | 1,19 |
| ERA5, CIV | 0,82 | 0,92 | 0,77 | 0,68 |
| ERA5, GHA | 0,84 | 0,99 | 0,79 | 0,68 |
| ERA5, ECU | 2,31 | 1,87 | 1,60 | 1,56 |

Lecture corrigée : le décalage NASA/ERA5 en Afrique de l'Ouest vient au moins autant d'une baisse d'ERA5 par rapport à CHIRPS que d'une hausse de la NASA. L'hypothèse d'une NASA seule en cause ne tient donc pas sur le niveau. En 2020-2023, la corrélation mensuelle de la NASA avec CHIRPS recule (CIV 0,79, CMR 0,74, ECU 0,72, IDN 0,75), celle d'ERA5 tient mieux (0,91 ; 0,92 ; 0,85 ; 0,76). CHIRPS peut aussi avoir dérivé : rien ici ne le prouve ni ne l'exclut.

**Décision de l'utilisatrice (2026-11-07).** La pluie du modèle combine ERA5 quotidien en anomalies et CHIRPS mensuel. La pluie NASA reste un test de robustesse. La NASA reste la source de la température, de l'humidité, du rayonnement et du vent.

**Mise en œuvre (`src/cacao/meteo.py`, `tests/test_meteo.py`, `scripts/27_indices_pluie.py`).**
- **ERA5 :** cumuls sur 7 et 30 jours par point, écart à la normale du même mois en écarts-types, calculée sur les années strictement antérieures, avec trois années de passé au minimum. Les années 2005-2007 restent vides.
- **CHIRPS :** cumuls sur 1, 3 et 6 mois, écart à une normale fixe 1991-2004, antérieure à l'échantillon. CHIRPS est réextrait depuis 1991.
- **Délais :** 7 jours pour ERA5, retard observé sur l'API le 2026-11-06. Pour CHIRPS, le 25 du mois suivant, avec une marge sur la [FAQ du Climate Hazards Center](https://wiki.chc.ucsb.edu/CHIRPS_FAQ), qui annonce la troisième semaine.
- **Tests :** 4 tests réussis, dont un qui modifie le futur et vérifie que le passé ne change pas.
- **Risque :** un [document USGS](https://earlywarning.usgs.gov/fews/product/175) indique que CHIRPS 3.0 remplace la version 2.0 depuis décembre 2024. Notre fichier v2.0 a pourtant été mis à jour le 15 octobre 2026. Il faudra vérifier sa pérennité et les éventuelles différences de méthode.

**Indices de pluie construits (2026-11-07).** ERA5 atteint 349 points sur 349. Comparaison finale sur 347 points et 9 pays : en 2020-2023, la corrélation mensuelle avec CHIRPS est plus forte pour ERA5 que pour la NASA dans 7 pays sur 9 ; le Ghana et le Brésil vont légèrement dans l'autre sens. Le pire cas de la NASA est la République dominicaine (0,31 contre 0,74). Sur les 30 jours-point NASA au-dessus de 300 mm, ERA5 donne une médiane de 10,2 mm et un maximum de 49,7 mm.
- `data/processed/pluie_era5_pays.parquet` : 7 973 jours, 20 colonnes, du 2005-01-01 au 2026-10-30, complet à partir du 2008-01-01.
- `data/processed/pluie_chirps_pays.parquet` : 261 mois, 31 colonnes, de janvier 2005 à septembre 2026, 347 points, aucune valeur vide, avec la colonne `disponible_le`.

Ces fichiers ne sont pas encore intégrés à la grille quotidienne.

**Prévisions météo : non collectées à ce stade (2026-11-07).** L'utilisatrice demande de prendre en compte les prévisions, puis la météo réelle en comparaison. Les données collectées jusqu'ici sont toutes observées ou réanalysées. La météo réelle du futur ne peut pas être une variable du modèle sans look-ahead. Plan proposé : prévisions émises avant la date de décision ; écart entre prévision et réalité, utilisable une fois la réalité connue ; expérience « oracle » hors production pour mesurer la valeur maximale d'une météo parfaite. Archives repérées, non testées : [GEFSv12](https://psl.noaa.gov/news/2022/042122a.html) sur 2000-2019, gratuit sur AWS ; [TIGGE](https://www.ecmwf.int/node/27900) depuis octobre 2006, gratuit pour la recherche ; [Open-Meteo](https://openmeteo.substack.com/p/introducing-the-historical-forecast) depuis 2021 seulement, et échéances fixes depuis janvier 2024.

**Test d'accès GEFS (2026-11-07).** L'archive `noaa-gefs-retrospective` s'ouvre sans compte. Un fichier de pluie du 2015-04-11 (membre `c00`, 1 à 10 jours) pèse 31 Mo, se télécharge en 15 s, se décode et s'extrait sur les 349 points en 3,2 s, sans valeur vide. Lecture permise par `eccodes`, `ecmwflibs` et `cfgrib`, ajoutés à `requirements.txt`. Couverture observée : reprévisions complètes jusqu'en 2019, le dossier 2020 ne contient qu'une date isolée. L'archive opérationnelle `noaa-gefs-pds` existe depuis 2017, avec un format différent : `pgrb2a` et `pgrb2b` au 2020-03-01, `pgrb2sp25` au 2020-10-01. Il y a donc trois régimes à raccorder : 2005-2019, début 2020 à l'automne 2020, puis l'opérationnel. La date exacte de bascule reste à fixer. Reprévisions et opérationnel n'ont pas les mêmes conditions initiales, donc un test de rupture sera nécessaire.

**Collecte GEFS lancée (`scripts/28_collecter_previsions_gefs.py`).** Sur décision de l'utilisatrice, sans test préalable d'un mois : pluie à 1-10 jours, membre de contrôle, émission 00 UTC, 349 points, du plus récent au plus ancien. Fichiers `.npy` par date dans `data/raw/t2_climat/gefs/`, rien de global n'est gardé. Test sur 3 dates, une par régime : 49, 36 et 17 s par date, aucune valeur vide, cumuls médians à 10 jours de 61,0, 43,1 et 38,9 mm. Bascule retenue : le 2020-09-23 vers le format récent ; le dossier du 2020-09-23 contient les deux formats. Limite de fond : les années 2005-2019 sont des reprévisions produites après coup avec un modèle plus récent, pas les prévisions vues par le marché. Elles peuvent donc paraître plus justes que les prévisions d'époque.

**Nouvelles collectes (2026-11-06).**
- **ENSO (`scripts/24_collecter_enso_intrants.py`) :** `data/raw/t2_climat/oni.txt`, indice ONI de la NOAA, 921 lignes. Dernière valeur : ASO 2026, anomalie +2,46. C'est une moyenne sur trois mois, donc publiée avec retard.
- **Pesticides et engrais FAOSTAT :** `faostat_pesticides.csv` (1990-2024, 36 catégories) et `faostat_engrais.csv` (1961-2024, N, P2O5, K2O). Chiffres annuels nationaux, toutes cultures confondues. Ce n'est ni une mesure sur le cacao ni une mesure de pollution des sols. Le fichier engrais a été récupéré avec `curl`, après l'échec de Python, puis filtré sur les 9 pays.
- **Incendies (`scripts/23_collecter_incendies.py`) :** archives annuelles MODIS de NASA FIRMS, 2005-2025, filtrées sur les mailles de cacao MapSPAM 2010 à 0,25°. En Indonésie, le filtre garde encore l'essentiel des détections. L'année 2026 n'est pas dans ces archives. Le nom de la Côte d'Ivoire est `Cote_d_Ivoire`. Collecte terminée : 189 fichiers, 4 838 892 détections, du 2005-01-01 au 2025-12-31, sans coordonnée ni date manquante. En Côte d'Ivoire, les détections baissent de 28 940 en 2005 à 8 260 en 2025, et se concentrent de décembre à février. Attention : le champ `version` change (6.20 sur 2005-2017, 6.03 sur 2018-2022, 61.03 sur 2023-2025). Ces changements peuvent créer des ruptures et devront être testés. 97 % des détections sont de type 0 ; les types 1 à 3 devront être écartés ou examinés.
- **Rayonnement et vent (`scripts/22_collecter_rayonnement_vent.py`) :** `ALLSKY_SFC_SW_DWN` et `WS2M`, en cours sur les 349 points.

**Diagnostic réseau.** Les coupures 10054 touchent NASA, IRI et FAO, y compris via `curl` : trois requêtes vers FAO en suivant ont donné un succès puis deux coupures en 0,04 s. La poignée de main TLS prend 7 à 10 s. Tout cela pointe plutôt vers le réseau local (Wi-Fi, box ou opérateur) que vers les serveurs, sans le prouver. Mon explication précédente par le seul serveur IRI est donc à revoir.

**Contrôle ERA5 (`scripts/15_collecter_controle_openmeteo.py`, `scripts/16_controler_meteo.py`).** 14 points : le plus lourd de chaque pays et les 5 points aux extrêmes les plus marqués. Résultats dans `outputs/metriques/t2_controle_openmeteo.csv` et `t2_pluies_extremes.csv`.

| Point | Date | NASA (mm) | ERA5 (mm) |
|---|---|---:|---:|
| IDN_013 | 2020-10-17 | 790,0 | 6,2 |
| CIV_020 | 2022-09-16 | 726,7 | 5,9 |
| CIV_012 | 2022-09-16 | 710,8 | 1,9 |
| IDN_028 | 2023-12-04 | 508,6 | 0,1 |

| Médiane sur 14 points | 2005-2019 | 2020-2023 | 2024-2026 |
|---|---:|---:|---:|
| Corrélation mensuelle de la pluie | 0,68 | 0,52 | 0,69 |
| Corrélation quotidienne de la pluie | 0,36 | 0,25 | 0,33 |
| Écart NASA − ERA5 sur `T2M` (°C) | −0,19 | −0,45 | −0,09 |
| Écart NASA − ERA5 sur `T2M_MAX` (°C) | −0,55 | −1,72 | −1,27 |

**Ce qui va dans le sens d'une rupture.** Le ratio de pluie NASA/ERA5 change aussi de niveau selon le pays : Nigéria 0,96 puis 1,78, Pérou 1,17 puis 0,61, Équateur 0,17 puis 0,52. L'humidité des sols `GWETROOT` se distingue également en 2020-2023.

**Ce qui nuance.**
- ERA5 est aussi un modèle, et un seul point par pays ne représente pas tout le pays. Un écart ne dit pas à lui seul quelle source a raison.
- Les extrêmes ne sont pas isolés : le jour du pic, les voisins à moins de 150 km sont souvent très élevés (médiane de 142 à 640 mm) et l'humidité de surface monte.
- 2020-2022 est aussi une période réellement humide possible : je ne l'ai pas vérifié, et cela n'expliquerait pas des valeurs de 700 mm absentes d'ERA5.

**Cause non confirmée.** Aucun changement de méthode daté n'a été trouvé. Une recherche web indique que POWER ajoute GEOS-IT à la fin de la série MERRA-2. Les deux pages de méthodologie de POWER renvoient une erreur 404, il faudra les retrouver avant de conclure.

**Recherche d'articles (2026-11-06).**
- **Bug ×24 de POWER, écarté pour nos données.** Deux dépôts GitHub ([Holos #499](https://github.com/holos-aafc/Holos/issues/499), [prismpy #126](https://github.com/izuku-franck1555/prismpy/pull/126)) signalent en octobre 2026 un `PRECTOTCORR` multiplié par 24 quand la requête atteint la période récente, sans confirmation de la NASA. Test direct : les valeurs restent identiques quelle que soit la fenêtre demandée (IDN_013 : 790,0 mm pour octobre 2020, 2020-2021 et 2005-2025 ; CIV_020 : 726,74 mm ; IDN_028 : 508,65 mm sur un mois). La moyenne par fichier va de 0,82 à 11,84 mm/jour, donc aucun fichier n'est gonflé en entier. Le bug signalé ne produit pas notre anomalie.
- **Fragilité documentée.** Le [guide climatique du NCAR](https://climatedataguide.ucar.edu/climate-data/nasas-merra2-reanalysis) signale des discontinuités liées aux changements du système d'observation. Une autre source indique que la pluie corrigée de MERRA-2 dépend d'un réseau de pluviomètres qui évolue, surtout là où il est peu dense. Cela rend une rupture plausible, sans en prouver une en 2020.
- **Validation.** Aucune évaluation des extrêmes quotidiens de POWER sous les tropiques n'a été trouvée. Une [étude à Oman](https://arxiv.org/pdf/2210.16111), en zone aride, juge la pluie POWER non acceptable. Elle n'est pas transposable directement.
- **Presse.** Une crue est rapportée à Donggala (Sulawesi central) vers le 15 octobre 2020 ([Antara](https://sulteng.antaranews.com/berita/159453/flash-flood-hits-two-sub-districts-of-central-sulawesi)), ce qui ne confirme pas 790 mm. Rien n'a été trouvé pour le 16 septembre 2022 en Côte d'Ivoire, ce qui ne prouve pas l'absence d'événement.
- **Précaution.** Toute nouvelle collecte POWER devra contrôler le rapport à la série déjà stockée, à cause du bug ×24.

**Test d'écrêtage (seuil : quantile 99,9 % par point sur 2005-2019, médiane 48,6 mm).** Il retire les pics, mais pas le changement de niveau. L'Indonésie reste à 2 990 mm en 2020 contre 3 086 mm bruts et 2 039 mm en 2019. Pour le modèle, le seuil devra être calculé uniquement sur le passé de chaque fenêtre.

**Indices (`scripts/17_indices_meteo.py`).** `data/processed/meteo_pays.parquet` contient 7 976 jours, 70 colonnes et aucun manquant, du 2005-01-01 au 2026-11-02. L'indice pays utilise les poids MapSPAM 2010. L'indice mondial utilise les parts FAOSTAT de l'année N-2 parmi les 9 pays (`outputs/metriques/t2_poids_pays.csv`). Ces parts sont des chiffres révisés, pas ceux connus à l'époque. Les valeurs sont brutes : aucune correction de la pluie n'est appliquée à ce stade.

**Reste à faire.** Arbitrer le traitement de la pluie, puis intégrer la météo à la grille avec un délai de disponibilité.

---

### 2026-11-07 — Dataset quotidien et benchmark

**Statut : dataset météo assemblé, GEFS et autres familles non intégrés. Benchmark terminé.**

**Contrôles.** Rayonnement et vent : 349 points, moyennes annuelles stables (rayonnement 16,9 à 17,5, vent 1,16 à 1,28), pas de rupture visible au niveau annuel. Trous récents du rayonnement : 6 % des points le 2026-09-18, moins ensuite, poids renormalisés.

**Dataset (`scripts/29_construire_dataset_meteo.py`, `data/processed/dataset_quotidien.parquet`).** 5 489 séances, 179 colonnes. Une valeur n'entre qu'une fois disponible, strictement avant la séance (`aligner_disponible`, 16 tests réussis sur l'ensemble du projet). Délais : NASA 3 jours, rayonnement 6 jours, ERA5 7 jours, observés sur les API ; incendies 1 jour et ONI autour du 15-18 du mois suivant la fin de la saison, hypothèses prudentes à confirmer ; CHIRPS le 25 du mois suivant. Pluie NASA gardée sous le préfixe `ROBUSTESSE_`, à exclure du modèle principal. Vides : ERA5 13,8 % (2005-2007), incendies 3,7 % (2026 absent des archives). Les incendies sont filtrés sur le type 0 et une confiance d'au moins 30 %. Ce filtre et les changements de version n'ont pas encore été testés.

**Bug corrigé.** Une première version du script ONI décalait d'un an la saison NDJ. Corrigé avant toute utilisation.

**Benchmark (`scripts/30_benchmark.py`, `outputs/metriques/benchmark.csv`).** Validation par année de 2010 à 2026, entraînement arrêté h séances avant l'année testée, `random_state=42`. Modèles sans aucun facteur.

| Sens, exactitude équilibrée | 2010-2023 | 2024-2026 |
|---|---:|---:|
| h=1, logistique | 0,496 | 0,520 |
| h=1, persistance | 0,506 | 0,477 |
| h=20, logistique | 0,550 | 0,491 |
| h=20, logistique, sans passage d'échéance | 0,496 | 0,520 |
| h=20, momentum | 0,439 | 0,542 |
| h=20, momentum, sans passage d'échéance | 0,507 | 0,554 |

| Volatilité à 20 séances, RMSE | 2010-2023 | 2024-2026 |
|---|---:|---:|
| Moyenne passée | 0,081 | 0,374 |
| Persistance | 0,071 | 0,236 |

**Lecture.**
- À 1 séance, le sens n'est pas prévisible par le passé du prix.
- À 20 séances, l'AUC de 0,573 sur 2010-2023 tombe à 0,498 sans les fenêtres contenant un passage d'échéance. Ce gain vient au moins en partie de l'artefact des passages, pas d'un vrai signal. Un modèle à facteurs devra être jugé aussi sans ces fenêtres. Ce filtre retire environ 39 % des dates et repose sur des sauts repérés après coup.
- La volatilité se prévoit bien mieux que le sens : la persistance bat la moyenne passée, surtout en 2024-2026.
- Le momentum et la persistance sont identiques à h=20, puisqu'ils utilisent le même calcul.

---

### 2026-11-07 — Thématiques 4 et 5 : investisseurs et géopolitique

**Statut : CFTC, GPR et Google Trends intégrés. GDELT en cours. Base d'événements non commencée.**

**Collecte (`scripts/31_collecter_investisseurs_geopolitique.py`).**
- **CFTC :** cacao, code 073732. Classement historique : 1 140 rapports depuis 2005, tous à 6-8 jours d'écart, aucun doublon. Le nom du marché change (New York Board of Trade, puis ICE Futures U.S.), le code reste le même. Classement désagrégé depuis 2006-06-13.
- **Google Trends :** cocoa, chocolate, cocoa price, mensuel de janvier 2004 à octobre 2026, via `pytrends`, bibliothèque non officielle. `cocoa price` a 22 mois à zéro. L'échelle 0-100 dépend de toute la période, donc seules les variations sur 1 et 12 mois sont gardées.
- **GPR (Caldara et Iacoviello) :** quotidien mondial, et mensuel. Par pays, seuls le Brésil, l'Indonésie et le Pérou sont couverts : **aucune mesure pour la Côte d'Ivoire ni le Ghana**.
- **GDELT :** volume et ton de presse, depuis 2017 seulement. L'API a renvoyé des refus de débit (erreur 429) : collecte relancée lentement, 2 minutes entre deux séries. Les requêtes par mots-clés sont un choix de ma part, à discuter.

**Dataset.** 5 489 séances, 197 colonnes. Délais : CFTC le vendredi de publication, donc utilisable à la séance suivante ; GPR quotidien 7 jours, retard observé ; GPR mensuel 10 jours après la fin du mois et Trends 5 jours, hypothèses. Les décalages de publication liés aux jours fériés ne sont pas modélisés pour la CFTC.

**Reste à faire pour la géopolitique.** Une base d'événements datés, chacun recoupé avec une source de référence. Rien n'a été écrit ici : conformément à la règle, aucune date n'est donnée de mémoire.

---

### 2026-11-07 — Offre, intrants et base d'événements

**Statut : dataset à 240 colonnes. GEFS en cours, GDELT bloqué par l'API.**

- **USDA PS&D : écarté.** Le fichier complet téléchargé contient 63 produits, aucun n'est le cacao.
- **Prix mensuels Banque mondiale (Pink Sheet) :** urée, DAP, TSP, potasse, sucre, huile de palme, café robusta, en logarithme, disponibles 5 jours après la fin du mois. Le fichier du 3 novembre contient octobre, ce qui soutient ce délai.
- **FAOSTAT annuel par pays :** rendement, production, pesticides et azote par hectare cultivé. Une année N n'est utilisée qu'à partir du 1er janvier N+2. Contrôle : en janvier 2007, le dataset donne bien le rendement ivoirien de 2005 (586,4 kg/ha) ; en janvier 2025, celui de 2023 (499,5 kg/ha). Ce sont des chiffres révisés.
- **ICCO :** non intégré. Les éditions lisibles couvrent 2019 et 2023-2025, ce qui est trop discontinu pour le modèle. Gardé pour le test de sensibilité des poids.
- **Base d'événements (`config/evenements.csv`) :** 6 événements. 3 ont une date confirmée par l'adresse d'un article Bloomberg, 3 restent à recouper avec un média de référence. Seuls les extraits de recherche ont été lus, pas les articles complets. Le fichier sert aux annotations du site, pas de variable du modèle à ce stade.
- **Indice composite absent :** aucune mesure directe de l'empoisonnement des sols, de la maladie du swollen shoot ou de l'orpaillage en série temporelle. Ils restent couverts indirectement par les rendements et les événements.

**GDELT.** L'API DOC échoue : erreur 429 répétée, y compris sur une seule requête courte depuis ce poste. Aucun fichier de l'API n'est conservé. Les fichiers bruts d'événements restent accessibles et couvrent 2005 (annuel), 2006 à mars 2013 (mensuel), puis chaque jour. `scripts/32_collecter_gdelt_evenements.py` les agrège par pays et par jour : nombre d'événements, conflits, protestations, ton, score de Goldstein, et `n_monde` pour normaliser. Test réussi sur 2 fichiers, collecte complète lancée. Avantage : c'est la seule mesure de tension couvrant la Côte d'Ivoire et le Ghana depuis 2005, ce que le GPR ne fait pas. Limites : pas de mot-clé cacao ; le volume de presse augmente fortement et le ton change d'échelle entre les deux formats (4,67 en janvier 2006 contre 0,12 en janvier 2017 pour la Côte d'Ivoire), donc une rupture à la jonction de 2013 est probable. Résultat : 5 032 fichiers, 70 284 lignes pays-jour, du 2005-01-01 au 2026-11-06, sans doublon. Le signal est crédible : en Côte d'Ivoire, le nombre moyen d'événements par jour passe de 77 en 2010 à 181 en 2011, année de crise post-électorale. Le ton casse nettement (5,4 en 2011, 2,4 en 2013, −1,6 en 2015) : il est écarté. Le nombre brut dépend du volume mondial : variables gardées en part du total, part de conflits et de protestations, sur 30 jours. Seule l'API DOC donne le volume spécifique au cacao. Sur le réseau du téléphone de l'utilisatrice, elle a répondu : le blocage dépendait donc de l'adresse réseau. 3 séries sur 6 ont été récupérées depuis 2017 (`cacao` volume et ton, `cacao_afrique` volume) avant un nouveau blocage, et sont intégrées au dataset. Les 3 autres ne sont pas essentielles, les tensions étant couvertes par les fichiers bruts.

**Contrôle ERA5 pur refait sur 14 points (`scripts/15`, `scripts/16`, `data/raw/t2_climat/era5_controle/`).** Corrélation mensuelle : température 0,85 à 0,87, stable sur les trois périodes. Écart moyen NASA − ERA5 sur 2005-2019, 2020-2023, 2024-2026 : `T2M` −0,72 ; −1,13 ; −0,62 °C. `T2M_MAX` −1,85 ; −2,42 ; −1,75 °C. `T2M_MIN` −0,39 ; −0,37 ; −0,34 °C. `RH2M` −1,9 ; +1,0 ; −1,3 point. `GWETROOT` : la NASA monte à 0,74 en 2020-2023 contre 0,69 et 0,65, ERA5 reste entre 0,37 et 0,39, sur une échelle différente. Le décalage de 2020-2023 touche donc aussi l'humidité et la température maximale, côté NASA, de façon cohérente avec une période plus humide. C'est moins marqué que pour la pluie. La température minimale est stable. Ces variables seront utilisées en anomalies, et ce biais devra être testé sur le modèle.

**GEFS.** 1 483 dates sur 7 980, aucun échec. Le compteur du script indique 580 minutes, mais le PC a manifestement cessé de travailler une partie de la nuit : le rythme réel reste à confirmer.

---

### 2026-11-07 — Protocole et pipeline, avant tout résultat de modèle

**Statut : protocole proposé, en attente de validation. Pipeline écrit et testé. Aucun modèle à facteurs entraîné sur la vraie cible.**

Décision de l'utilisatrice : collecter d'abord toutes les données, avec date limite proposée au 2026-11-10, et se mettre d'accord sur les règles avant de voir les résultats.

- **`protocole.md` :** cibles, variables, validation, benchmarks, critères de réussite, mesure des familles, robustesse. Le benchmark sans facteurs était déjà connu, ce qui est écrit dans le protocole.
- **`config/familles.yaml`, `src/cacao/variables.py` :** 141 variables à 20 séances, réparties en 7 familles : climat 42, couts_production 23, géopolitique 19, demande 18, investisseurs_biais 16, biodiversité 12, marché_finance 11.
- **`src/cacao/evaluation.py` :** plis chronologiques avec purge, Gradient Boosting et Random Forest, retrait de famille, SHAP par famille et par année, bootstrap par blocs.
- **Tests :** 28 tests réussis. Données factices : la purge est exacte, le bruit donne 0,5, la bonne famille est retrouvée par le retrait et par SHAP, et une fuite volontaire est détectée. Sur les vraies variables : un test tronque les données en 2018 et vérifie que le passé ne change pas.
- **Essai complet (`scripts/33_modele_factice.py`) :** vraies variables et cible tirée au hasard, donc aucun résultat sur le cacao. Score 0,474 sur deux ans, comme attendu pour du hasard. Deux ans en 2 s, SHAP en moins de 1 s.

**Point relevé.** La somme SHAP par famille favorise les familles nombreuses. Le protocole le signale et prévoit une lecture par variable.

---

### 2026-11-07 — Matrice d'horizons 1, 5, 20, 60 et 120 séances

**Statut : consigne de l'utilisatrice appliquée. Benchmark refait, modèle à facteurs non lancé.**

| Horizon | Séances | Sens | Volatilité | Purge |
|---|---:|---|---|---:|
| Très court terme | 1 | Oui | Non : une seule séance ne donne pas de volatilité | 1 |
| Très court terme, une semaine | 5 | Oui | Oui | 5 |
| Moyen terme, un mois | 20 | Oui | Oui | 20 |
| Long terme, agronomique, trois mois | 60 | Oui | Oui | 60 |
| Long terme, agronomique, six mois | 120 | Oui | Oui | 120 |

**Purge.** La fenêtre de purge est strictement égale à l'horizon. Un test le vérifie pour chaque valeur. 34 tests réussis au total.

**Fenêtres avec passage d'échéance.** 1,9 % à 1 séance, 9,7 % à 5, 38,6 % à 20, 94,9 % à 60, 97,8 % à 120. Le filtre « sans passage » ne fonctionne donc plus à long terme : il reste 138 lignes à 60 séances et aucune à 120. **Ajout :** une cible où les jours de saut sont mis à zéro (`cible_hausse_neutre_h`). Elle sert de lecture de contrôle à 60 et 120 séances. Les sauts étant repérés après coup, c'est un test de robustesse et pas une vraie cible.

**Benchmark 2010-2026 (`scripts/30_benchmark.py`).**

| Horizon | Sens brut | Sans passage | Sans sauts | RMSE volatilité |
|---:|---:|---:|---:|---:|
| 1 | 0,501 | 0,502 | 0,502 | Sans objet |
| 5 | 0,503 | 0,500 | 0,500 | 0,201 |
| 20 | 0,542 | 0,514 | 0,514 | 0,116 |
| 60 | 0,514 | Inutilisable | 0,500 | 0,093 |
| 120 | 0,500 | Inutilisable | 0,513 | 0,106 |

**Lecture.**
- Le passé du prix ne prédit pas le sens, à aucun horizon, une fois les passages d'échéance traités. Le meilleur score de contrôle est 0,514.
- L'AUC de la logistique tombe à 0,412 à 60 séances et 0,322 à 120 séances, sous le hasard. Avec environ 70 et 35 fenêtres indépendantes, ces chiffres sont fragiles : ils traduisent surtout des changements de régime, à ne pas exploiter comme un signal inversé.
- La volatilité reste prévisible. La persistance bat la moyenne passée à 20, 60 et 120 séances, mais pas à 5, où l'écart est faible (0,205 contre 0,201).

**Protocole.** `protocole.md` intègre la matrice. Ajout de ma part à valider : 9 comparaisons exigent une correction des tests multiples, l'intervalle passe donc à 99,4 %, avec un bootstrap par blocs de `max(20, h)` séances.

**Quarto.** `site/horizons.qmd` compare les horizons avec Plotly. Rendu réussi avec le Quarto de Positron, avec les seuls modèles sans facteurs pour l'instant. Les modèles à facteurs s'ajouteront depuis `outputs/metriques/modele_horizons.csv`. La page n'est pas publiée, Git n'étant pas installé.

---

### 2026-11-07 — Validation du protocole et fin de la phase 1

**Statut : protocole validé. Phase 1 à 23 jeux complets sur 27. Modèle non lancé, sur instruction de l'utilisatrice.**

**Validé par l'utilisatrice :** retrait de la volatilité à 1 séance, cible sans sauts à 60 et 120 séances, intervalle à 99,4 %, pas de classement si le benchmark n'est pas battu, retrait d'une famille en mesure principale. Pétrole, gaz et change en coûts de production ; production FAOSTAT dans une famille `production_offre` ; Trends et presse en investisseurs et biais ; sucre, huile de palme et café en demande et substituts.

**Point signalé.** La famille `production_offre` porte le total à 8 familles, alors que le projet en comptait 7. Confirmé par l'utilisatrice : on garde 8 familles.

**Revue des sauts de change (`scripts/06`).** 9 cotations retirées : IDR figé à 9 612 entre des cotations à 11 800 (novembre-décembre 2013, 5 retirées en plus du filtre), NGN divisé par 100 (janvier 2011), NGN à 232 au lieu de 322 (juin 2017). Restent 6 sauts, conservés car le niveau ne revient pas : GHS 2022-12-16 ; NGN 2016-06-22, 2019-06-12, 2023-06-16, 2024-02-01, 2024-02-06. Ils ressemblent à de vrais mouvements ou à un changement de cours de référence, sans vérification par une source.

**GEFS.** `scripts/28` accepte `--tmax` pour la température maximale. Test sur les 3 formats : aucune valeur vide, maximum de 312 à 318 K. Lancement programmé à la fin de la collecte de pluie.

**Événements.** 4 sur 6 ont une date confirmée, dont le report européen par le Conseil de l'UE. Pour le différentiel de 2019, le mois est confirmé par Bloomberg, le jour reste à vérifier. Pour février 2026, Bloomberg confirme la date et la refonte. Le niveau de 2 587 cedis vient de MyJoyOnline et il est cité comme niveau en vigueur par Bloomberg en septembre 2026. Reuters, Le Monde et d'autres sources ne sont pas accessibles à l'outil de recherche.

**Inventaire (`scripts/34_inventaire_donnees.py`, `outputs/metriques/inventaire_donnees.csv`).** 23 jeux complets sur 27. Incomplets : GEFS pluie (2 681 sur 7 980), GEFS température (0), incendies 2026 (0 sur 9, clé FIRMS nécessaire), GDELT presse cacao (3 sur 6, relance en cours). Dataset : 5 489 séances, 287 colonnes, aucune date en double.

Mise à jour : la relance a donné la 4e série GDELT, le ton du cacao en Afrique de l'Ouest, avant un nouveau blocage. Les 4 séries sur le cacao sont donc complètes. Les 2 séries de tensions par mots-clés sont abandonnées, car les fichiers bruts couvrent déjà ces tensions depuis 2005.

---

### 2026-11-07 — Pluie GEFS terminée : 7 980 dates sur 7 980

**Résultat.** La collecte de pluie GEFS a fini avec 4 échecs sur 7 980 dates. Ces échecs ne venaient pas du réseau : une relance donnait les mêmes erreurs. Les 4 dates sont récupérées après correction de `scripts/28_collecter_previsions_gefs.py`.

| Date | Problème constaté | Traitement |
|---|---|---|
| 2013-11-09, 2007-06-02, 2007-06-04 | Fichier de reprévision contenant des messages en double (35, 21 et 25) | Doublons octet pour octet identiques, pluie et Tmax vérifiées : un seul exemplaire est gardé |
| 2020-08-28 | Échéance 168 h absente de l'archive NOAA (404 sur le GRIB et son index) | Jour d'échéance 7 laissé vide (`NaN`) sur les 349 points, les 9 autres jours gardés |

**Pourquoi c'est important.** Le contrôle du nombre de cumuls a bloqué ces dates. Sans lui, la pluie de ces 3 fichiers aurait été comptée deux fois. Le jour 7 du 2020-08-28 n'est pas reconstitué. Le script s'arrête désormais si deux doublons diffèrent.

**Contrôle.** Maximum et médiane du cumul sur 10 jours comparés à une date voisine : pas d'écart anormal. Ce n'est qu'un contrôle sommaire. La comparaison à ERA5 et CHIRPS reste à faire.

**À faire.** La collecte Tmax en cours a démarré avant cette correction : elle échouera sur les mêmes dates, à relancer à la fin. L'agrégation devra gérer le `NaN` du 2020-08-28.

---

### 2026-11-08 — Température GEFS terminée et contrôle de qualité GEFS

**Collecte.** La Tmax GEFS est complète : 7 981 dates, jusqu'au 2026-11-07. Les 4 échecs attendus (2020-08-28, 2013-11-09, 2007-06-02, 2007-06-04) sont récupérés avec le script corrigé. J'ai aussi ajouté le 2026-11-07 à la pluie : 7 981 dates. La collecte a ralenti pendant la nuit, sans doute à cause de la mise en veille du PC (cause non vérifiée).

**Démarche.** Le nouveau script `scripts/35_controler_gefs.py` mesure seulement, sans rien corriger. Il calcule une moyenne par pays avec les poids MapSPAM, sur chacun des 3 régimes de données. Il compare la pluie du jour 1 à ERA5 du même jour et sa somme mensuelle à CHIRPS. Il compare aussi la Tmax du jour 1 à T2M_MAX de la NASA. Sorties : `outputs/metriques/gefs_controle.csv` et `gefs_echeances.csv`.

**Résultats.**
- Aucune valeur aberrante : pas de pluie négative ni de Tmax infinie. Les seuls vides sont les 349 points du jour 7 du 2020-08-28. Les 2 fichiers suivent le même ordre de points.
- La corrélation est stable d'un régime à l'autre : 0,65 à 0,82 au jour près face à ERA5, 0,58 à 0,95 au mois face à CHIRPS. Le signal est donc cohérent entre les 3 formats.
- **Le niveau de pluie change d'un régime à l'autre.** Rapport à CHIRPS en Côte d'Ivoire : 1,40 en reprévision, 0,67 dans l'ancien GEFS, 1,06 dans le nouveau. Au Ghana : 1,44, puis 0,78, puis 1,03. Une anomalie calculée sans précaution prendrait ces ruptures pour de vrais écarts.
- Le jour 1 est plus humide que les suivants dans la reprévision : 6,65 mm contre environ 5,3 mm. Cela suggère un effet de démarrage du modèle.
- Biais de Tmax face à la NASA : de −2 à +3,5 °C selon le pays, assez stables entre régimes. Il y a des exceptions, notamment +1,4 °C au Ghana dans le nouveau régime. La NASA a elle-même un biais frais en 2020-2023, donc la part de chaque source reste inconnue.

**Décision en attente de l'utilisatrice.** Il faut choisir le traitement de ces ruptures avant d'intégrer GEFS, qui sert au test de robustesse n° 5 du protocole.

---

### 2026-11-08 — Correction GEFS validée et intégrée, règle d'imputation

**Arbitrage de l'utilisatrice (option 1).**
- Écarter la période du 2020-01-01 au 2020-09-22, celle de l'ancien GEFS.
- Corriger le niveau par pays face à CHIRPS, avec le passé seulement.
- Utiliser les jours de prévision 2 à 10.

**Règle d'imputation, demandée par l'utilisatrice.** Pas de médiane globale. Deux cas :
- **Échéance vide dans une prévision :** interpolation linéaire entre les jours d'échéance voisins de la même émission. Ces valeurs sont publiées en même temps, donc il n'y a pas de look-ahead.
- **Date d'émission manquante :** report de la dernière prévision connue (ffill), 3 jours au plus.

J'ai écarté l'interpolation entre t−1 et t+1 pour une date manquante : la valeur de t+1 n'est pas connue à la date t, ce serait un look-ahead. L'utilisatrice proposait l'interpolation ou le ffill : le ffill respecte la règle. Le seul trou connu, le 2020-08-28, tombe de toute façon dans la période écartée.

**Code.** Nouveau script `scripts/36_indices_gefs.py`, qui produit `data/processed/gefs_pays.parquet`. Il calcule le cumul de pluie et la moyenne de Tmax sur les jours 2 à 6 et 2 à 10. Le niveau de chaque pays et de chaque régime est corrigé, puis l'écart à la normale passée du même mois est calculé comme pour ERA5. Enfin, l'agrégat monde utilise les parts FAOSTAT de N-2.
- **Pluie :** rapport CHIRPS / GEFS cumulé sur les mois déjà publiés (le 25 du mois suivant).
- **Tmax :** pas de CHIRPS pour la température. J'ai appliqué la même méthode, en écart additif face à T2M_MAX de la NASA, publiée en fin de mois plus 3 jours. Ce choix est le mien, par analogie : il reste à valider par l'utilisatrice.
- **Fenêtre de calcul :** 3 mois au moins du même régime, et le rapport ne passe jamais d'un régime à l'autre.

Dans `scripts/29_construire_dataset_meteo.py`, une prévision émise le jour E n'entre qu'à la séance E+1, par alignement strict. `scripts/34_inventaire_donnees.py` vérifie aussi le fichier d'indices.

**Contrôles.**
- **Troncature au 2022-06-15 :** 192 360 valeurs identiques, écart maximal 3e-12. Les données postérieures ne changent donc pas le passé.
- **Raccord de la pluie :** l'anomalie moyenne vaut +0,04 en 2015-2019 et +0,05 en 2021-2026 en Côte d'Ivoire, −0,02 et −0,03 au Ghana. Il n'y a pas de saut, la correction fonctionne.
- **Raccord de la Tmax : défaut.** L'anomalie moyenne passe de +0,11 à −0,69 en Côte d'Ivoire, et de +0,43 à −0,76 au Ghana. L'écart corrigé vaut −3,1 °C mi-2022 et −2,0 °C fin 2026 : il suit le biais frais de la NASA en 2020-2023. La correction de la Tmax transmet donc ce défaut de la NASA. C'est une limite à signaler, ou une correction à revoir.
- **Facteurs de pluie en fin de régime :** 1,03 (CIV) et 0,95 (GHA) en reprévision, 1,13 et 1,16 dans le nouveau régime. Sur les jours 2 à 10, la reprévision est donc proche de CHIRPS. Le fort excès vu au jour 1 venait du démarrage du modèle.

**Résultats.** 40 colonnes GEFS ajoutées. Le dataset passe à 5 489 séances et 328 colonnes, sans doublon. GEFS est vide sur 19,7 % des séances : avant avril 2008 (3 ans de passé requis) et de janvier 2020 à fin janvier 2021 (période écartée, puis 3 mois de correction). Inventaire : 27 jeux complets sur 28, seul FIRMS 2026 manque, faute de clé. 34 tests passés.

**Phase 1 terminée, sauf FIRMS 2026.** Le modèle à facteurs attend le feu vert de l'utilisatrice. Selon le protocole, GEFS n'entre que dans le test de robustesse n° 5.

---

### 2026-11-08 — Lancement du modèle à facteurs (phases 3 et 4)

**Feu vert de l'utilisatrice** reçu le 2026-11-08. Le modèle est lancé sur la vraie cible.

**Code.** `scripts/37_modele_facteurs.py` applique `protocole.md` sans changer les réglages. Il calcule les 9 comparaisons en validation annuelle de 2010 à 2026, avec une purge égale à l'horizon. Le Gradient Boosting est le modèle principal, et la Random Forest sert de contrôle.
- **Benchmark :** chaque modèle est comparé au meilleur modèle sans facteurs de `scripts/30_benchmark.py`, choisi sur 2010-2026 comme dans le tableau du protocole.
- **Intervalle :** bootstrap à 99,4 %, par blocs de max(20, h) séances, 1 000 tirages.
- **Lecture de contrôle :** sans passage d'échéance jusqu'à 20 séances. À 60 et 120 séances, la cible sans sauts sert de contrôle pour le sens. La volatilité à 60 et 120 séances n'a pas de lecture de contrôle définie dans le protocole : elle est donc jugée sur la lecture brute seule, et je le signale.
- **Impact des familles :** retrait d'une famille à la fois, avec un intervalle à 99,4 %. SHAP est calculé par variable et par famille, sur 500 lignes tirées par année de test, avant et depuis 2024.
- **Contrôle :** le script s'arrête si une colonne `cible_`, `passage_dans`, `saut_echeance`, `ROBUSTESSE_` ou `GEFS_` entre dans les variables.

**Problème et solution.** Premier lancement arrêté par `HistGradientBoosting` (« window shape cannot be larger than input array shape »). Une colonne était entièrement vide sur l'entraînement d'un pli : c'est une série qui commence plus tard, comme la presse GDELT. Dans `src/cacao/evaluation.py`, `predire` ignore désormais, pour un pli donné, une colonne vide sur tout son passé. Cette colonne ne contient encore aucune information. SHAP lui donne alors 0 cette année-là. Aucun réglage du modèle n'a changé. 34 tests passés. Durée : 29 minutes.

**Résultats (outputs/metriques/modele_horizons.csv).** **Le modèle principal (Gradient Boosting) ne bat le benchmark sur aucune des 9 cibles**, ni en lecture brute, ni en lecture de contrôle.

| Cible | GB 2010-2026 | Benchmark | IC 99,4 % de l'écart |
|---|---:|---:|---|
| Sens 1 séance | 0,492 | 0,501 | −0,042 à +0,025 |
| Sens 5 | 0,502 | 0,503 | −0,033 à +0,037 |
| Sens 20 | 0,508 | 0,542 | −0,092 à +0,015 |
| Sens 60 | 0,442 | 0,514 | −0,144 à +0,010 |
| Sens 120 | 0,442 | 0,500 | −0,169 à +0,071 |
| Vol 5 (RMSE) | 0,199 | 0,201 | −0,008 à +0,013 |
| Vol 20 | 0,144 | 0,116 | −0,050 à +0,002 |
| Vol 60 | 0,139 | 0,093 | −0,076 à −0,013 (pire que le benchmark) |
| Vol 120 | 0,147 | 0,106 | −0,080 à −0,005 (pire que le benchmark) |

- Le sens reste au niveau du hasard jusqu'à 5 séances. Il tombe sous 0,5 à 60 et 120 séances, et encore plus bas en 2024-2026 (0,18 à 120 séances, cible sans sauts). Le modèle apprend des régimes passés qui ne se répètent pas.
- La volatilité future est mieux prévue par la volatilité récente seule (persistance) que par le modèle à facteurs, de 20 à 120 séances.
- **Random Forest (contrôle) :** elle bat le benchmark sur la volatilité à 5 séances, dans les deux lectures (écart de RMSE de +0,005 à +0,019). Le protocole interdit de choisir le meilleur modèle sur le test : ce résultat reste exploratoire, sur 1 cible parmi 18 essais.

**Application de la règle du protocole.** Aucun signal démontré. **Aucune hiérarchie de familles n'est présentée comme un résultat.** Le retrait de familles et SHAP sont calculés et sauvegardés (`retrait_familles.csv`, `shap_variables.csv`, `shap_familles.csv`), mais ils ne décrivent qu'un modèle qui ne bat pas le benchmark. Lecture exploratoire seulement :
- Pour la volatilité, retirer le marché dégrade le modèle de façon nette, de 5 à 120 séances. L'information utile est dans les prix passés, que la persistance capte déjà.
- Pour le sens à 60 séances, retirer le climat améliore le modèle de 6 points (IC de −0,120 à −0,020). Les variables climatiques ajoutent du bruit sur cette cible.
- SHAP donne au climat 18 à 27 % des contributions pour le sens. Mais le retrait montre que ces contributions n'aident pas hors échantillon : c'est le désaccord entre les deux mesures annoncé au point 7 du protocole.

**Suite prévue par le protocole.** Tests de robustesse du point 8 : pluie NASA, sans 2024-2026, exclusion des passages, GEFS. Puis le site Quarto, la présentation et le rapport.

---

### 2026-11-08 — Tests de robustesse (point 8 du protocole)

**Démarche.** `scripts/38_robustesse.py` relance le Gradient Boosting en 4 variantes, face au même benchmark et avec le même intervalle à 99,4 %. La sortie est `outputs/metriques/robustesse.csv`, et le calcul a duré 16 minutes.
- **Base :** refaite à l'identique. Elle redonne les écarts du script 37 (−0,009 à 1 séance), donc le calcul est reproductible.
- **Pluie NASA (test 1) :** cumuls sur 7 et 30 jours, anomalie passée et délai de 3 jours, comme pour l'ERA5. Ces variables remplacent ERA5 et CHIRPS.
- **GEFS (test 5) :** la base, plus les 16 colonnes GEFS corrigées pour la Côte d'Ivoire, le Ghana, l'Indonésie et le monde.
- **Oracle (test 5, météo parfaite) :** la base, plus la pluie ERA5 et la Tmax NASA réellement observées de la séance t à t+6. **Cette variante utilise volontairement le futur** pour mesurer le gain maximal d'une prévision parfaite.
- **Sans 2024-2026 (test 2) :** lu sur 2010-2023. La validation chronologique n'entraîne jamais sur une année postérieure au test.
- **Tests 3 et 4 :** la Random Forest et l'exclusion des passages sont déjà dans `modele_horizons.csv`.
- **Test 6 :** MapSPAM 2020 et poids ICCO ne sont pas faits. Ils passent en extension, faute de temps.

**Résultats.** **Aucune variante ne bat le benchmark, sur aucune cible, ni sur 2010-2026 ni sur 2010-2023.** Le résultat négatif est robuste.
- **Oracle :** même la météo réellement observée sur la semaine suivante n'améliore rien. Écarts de −0,003 à 1 séance et de −0,036 à 20 séances, contre −0,009 et −0,034 pour la base. La météo à une semaine n'apporte pas d'information exploitable sur le prix dans ce cadre. Une limite possible : avec plus de 100 variables, le modèle peut ne pas isoler 8 colonnes.
- **GEFS :** les écarts sont identiques à la base, à ±0,01 près.
- **Pluie NASA :** elle est un peu moins mauvaise à 60 séances (−0,002 contre −0,072), sans être significative. Cela rejoint le retrait de famille : à 60 séances, les pluies ERA5 et CHIRPS ajoutent du bruit.
- **Sans 2024-2026 :** le modèle reste sous le benchmark. Pour la volatilité à 5 séances, il est même nettement pire sur 2010-2023 (−0,017, IC jusqu'à −0,026). L'égalité sur 2010-2026 vient donc de 2024-2026.

**Conclusion de la phase de modélisation.** Aucune famille de facteurs n'apporte d'information démontrée au-delà du prix passé, quel que soit l'horizon, la source de pluie, la période ou le modèle. Même une météo parfaite à une semaine ne change rien. Ce résultat négatif est la réponse à présenter. Il est cohérent avec un marché qui intègre vite l'information publique.

---

### 2026-11-08 — Feuille de route : trois pistes complémentaires (proposées, non lancées)

**Demande de l'utilisatrice.** Elle veut tester 3 pistes après la robustesse : une cible d'écart à la tendance à 60 et 120 séances, l'exploitation de la volatilité, et une analyse selon le régime (crise 2024-2026 contre période calme) pour l'attention et la presse.

**Précaution de méthode.** Ces pistes sont choisies **après** avoir vu les résultats. Le point 8 du protocole impose de les présenter comme **exploratoires**. Pour limiter le risque de chercher jusqu'à trouver un signal par hasard :
- les règles de chaque piste sont fixées dans un amendement daté de `protocole.md`, avant tout calcul ;
- l'intervalle de chaque piste est corrigé pour ses propres comparaisons (Bonferroni) ;
- tous les résultats sont publiés, y compris les négatifs ;
- le résultat principal reste celui du protocole initial : pas de signal démontré.

**Piste 1. Cible d'écart à la tendance (60 et 120 séances).**
- Écart du jour : D_t = log(P_t) − log(MA120_t), connu à la séance t. La cible porte sur sa variation future, D_{t+h} − D_t (son signe, et sa valeur en RMSE).
- Prédire directement le niveau D_{t+h} serait trompeur : il dépend surtout de D_t, déjà connu. Un « signal » apparaîtrait sans rien apporter.
- Benchmark à battre : le retour à la moyenne prévu par le seul écart actuel, avec une régression sur D_t estimée sur le passé. Les facteurs doivent faire mieux que ce benchmark.
- Les résidus face aux fondamentaux de **stocks** ne sont pas faisables : aucune série de stocks n'est collectée (ICCO stocks absents, et USDA sans cacao). Rien ne sera inventé. Pistes possibles en extension : la production FAOSTAT annuelle, disponible à N+2, trop grossière, ou une source de stocks à fournir par l'utilisatrice.
- Intégration : nouvelle fonction de cible dans `src/cacao/grille.py` (avec test de troncature), puis nouveau script `scripts/39_pistes_complementaires.py` qui réutilise `construire`, `predire` et `ecart_bootstrap`.

**Piste 2. Volatilité.**
- **Correction de la prémisse.** La volatilité est bien prévisible, mais par son propre passé : la persistance a une RMSE de 0,093 à 60 séances. Le modèle à facteurs fait **moins bien** que la persistance (0,139), avec un intervalle qui exclut zéro. On ne peut donc pas présenter les facteurs comme source de ce signal.
- Ce qu'on peut documenter :
  - La volatilité se regroupe dans le temps, ce qui est utile pour la gestion du risque.
  - Benchmark plus exigeant : un modèle HAR, régression de la volatilité future sur les volatilités passées à 5, 20 et 60 séances, estimée sur le passé seulement.
  - Test des facteurs **en plus** du HAR, en prévoyant l'écart à la prévision HAR. On répond ainsi à la question : les facteurs ajoutent-ils quelque chose à la volatilité passée ?
  - Mesure complémentaire : QLIKE, courante pour la volatilité, en plus de la RMSE.
- Limite : les sauts de CC=F aux passages d'échéance gonflent la volatilité réalisée, donc on garde aussi la lecture sans passage jusqu'à 20 séances.

**Piste 3. Analyse selon le régime.**
- Le régime est défini avec le passé seul. Haute volatilité : volatilité à 60 séances au-dessus du 80e centile de toutes les valeurs passées, connu à la séance t. Découper par année calendaire (2024-2026) suppose de savoir après coup que la crise a eu lieu. Ce découpage sera montré aussi, mais à titre descriptif.
- Mesure : perte de score quand on retire la famille `investisseurs_biais` (Trends, presse GDELT, CFTC), calculée séparément sur les séances de haute et de basse volatilité, avec intervalle bootstrap. On peut ajouter un test de variante : la base, plus une interaction entre le régime et la famille.
- Puissance faible : 2024-2026 ne contient qu'environ 12 fenêtres indépendantes à 60 séances et 6 à 120 séances. Un écart non significatif ne prouvera pas l'absence d'effet.
- Les séries de presse GDELT sur le cacao commencent tard, elles sont donc peu présentes dans les premiers plis.

**Calendrier proposé.** Validation de l'amendement par l'utilisatrice, puis calcul (environ 1 heure en tout), puis site Quarto. L'oral est le 18 novembre.

**Statut.** Amendement écrit dans `protocole.md` (point 11), **non validé**. Aucun calcul lancé.

**Sources de stocks examinées le même jour.**
- **CFTC :** les positions sont déjà intégrées, mais ce ne sont pas des stocks.
- **USDA PS&D :** pas de cacao.
- **Stocks certifiés ICE :** aucun historique gratuit trouvé. ICE les vend dans son offre ICE Fundamentals, et StoneX et Barchart sur abonnement. L'utilisatrice dispose de Bloomberg à l'école : export prévu plus tard, en extension.

---

### 2026-11-08 — Résultats des analyses exploratoires (point 11 du protocole)

**Validation.** Amendement validé par l'utilisatrice le 2026-11-08 (« vas y »), puis calcul lancé.

**Code.**
- `src/cacao/grille.py` : ajout de `ecart_tendance` et `cibles_ecart`, avec un test de troncature dans `tests/test_grille.py`. 35 tests passés.
- `scripts/39_pistes_complementaires.py` : sorties `outputs/metriques/pistes_ecart.csv`, `pistes_har.csv` et `pistes_regime.csv`, en 7 minutes.
- Premier lancement arrêté : une période vide dans le découpage par années (2024-2026 n'a pas de séance en 2010-2023). J'ai ajouté un contrôle, puis relancé.
- Ajout non écrit dans l'amendement : en A, le modèle reçoit aussi l'écart actuel D_t, pour que le benchmark soit un sous-ensemble de son information.

**A. Écart à la tendance : les facteurs ne battent pas le benchmark.**
- Le retour à la moyenne prévu par l'écart actuel seul atteint 0,68 à 60 séances et 0,71 à 120 séances en exactitude équilibrée. Le modèle à facteurs fait moins bien : 0,65 et 0,67, et sa RMSE est significativement pire en lecture brute.
- **Attention à l'oral :** ce 0,68 est en grande partie **mécanique**. La moyenne mobile rattrape le prix avec retard, donc un écart fort se réduit même si le prix ne bouge pas. Ce n'est pas une prévision du prix.

**B. Volatilité au-delà du HAR : les facteurs dégradent la prévision.**
- Le HAR bat nettement la persistance simple à 5 séances (RMSE 0,156 contre 0,205) et à 20 séances (0,102 contre 0,116). Il en est proche à 60 et 120 séances.
- Ajouter les facteurs au HAR est pire sur les 4 horizons, avec un intervalle entièrement négatif. Le QLIKE confirme.
- Le meilleur prédicteur de la volatilité est donc la volatilité passée, à plusieurs horizons : c'est utile pour la gestion du risque. Les facteurs n'y ajoutent rien.

**C. Régime de volatilité et famille attention et biais.**
- Les séances en régime haut représentent 12,5 % de 2010-2023 et 95 % de 2024-2026. Le régime haut et les années 2024-2026 sont donc presque les mêmes séances : ces deux découpes ne se confirment pas l'une l'autre.
- 2 tests sur 36 sont positifs, tous deux sur la volatilité à 60 séances. Retirer la famille dégrade le modèle en régime haut (+0,0071 de RMSE, IC 99,72 % de +0,0004 à +0,0225) et sur 2024-2026 (+0,0087). En régime bas, l'effet est nul.
- SHAP désigne la presse GDELT : son volume d'articles sur le cacao, moyenné sur 120 séances, a une contribution de 0,0124 en 2024-2026, contre 0,0002 avant.
- Lecture prudente :
  - L'effet est mesuré face au modèle sans cette famille, pas face au benchmark. Le modèle complet reste moins bon que la persistance.
  - L'attention médiatique suit sans doute la crise elle-même, au lieu de l'annoncer.
  - Il repose sur environ 11 fenêtres indépendantes, et l'analyse est décidée après coup.
- Aucun effet sur le sens du prix, à aucun horizon.

**Conclusion des analyses exploratoires (2026-11-08).** Elles confirment la conclusion principale. La seule trace d'apport des facteurs est la presse GDELT, utile au modèle pour la volatilité à 60 séances en période de crise. Cette trace est exploratoire, sans battre le benchmark, et à présenter comme une piste.

---

### 2026-11-08 — Site Quarto (phase 5)

**Démarche.** Le site du dossier `site/` passe d'une page unique à un site Quarto de 6 pages, défini par `site/_quarto.yml`, en français, thème cosmo, code repliable. Il ne lit que les sorties déjà calculées : `outputs/metriques/*.csv`, `modele_predictions.parquet`, le dataset et `config/evenements.csv`. Aucun chiffre n'est saisi à la main dans les graphiques.
- `index.qmd` : question, réponse courte (aucune famille ne bat le benchmark), tableau des 9 cibles, 4 enseignements.
- `donnees.qmd` : prix CC=F avec les 6 événements vérifiés au survol (source et statut), pluie CHIRPS en Côte d'Ivoire et au Ghana, ONI, inventaire.
- `resultats.qmd` : écart au benchmark avec intervalle à 99,4 % par horizon, exactitude année par année à 20 séances, tableau complet, robustesse.
- `familles.qmd` : retrait de familles et parts SHAP en cartes de chaleur, désaccord entre les deux mesures expliqué, encadré « exploratoire » imposé par le protocole.
- `exploratoire.qmd` : pistes A, B et C du point 11.
- `methode.qmd` : protocole, sources et délais, limites, extensions, usage de l'IA.

**Code.**
- `site/_commun.py` : palette de couleurs validée (ordre fixe), gabarit Plotly, fonction de tableau. `tabulate` n'est pas installé, donc les tableaux passent par `to_html`.
- L'ancienne page `site/horizons.qmd` est remplacée par `resultats.qmd`. Elle est rangée dans `site/_archive/`, que Quarto ignore.
- `.claude/launch.json` ajouté pour prévisualiser le site avec un serveur local (port 8765).

**Rendu.** Rendu avec le Quarto de Positron et `QUARTO_PYTHON` sur le `.venv` : 6 pages produites dans `site/_site/`.

**Vérification dans le navigateur.**
- Graphiques présents.
- Signes moins des axes vérifiés.
- Étiquettes de familles d'abord coupées dans les cartes de chaleur : marge gauche élargie, puis page rendue à nouveau.
- La console montre une ressource externe refusée (403) et une erreur `Package` : c'est probablement le conflit connu entre require.js et MathJax dans Quarto. Les graphiques s'affichent malgré tout. Non vérifié une fois en ligne.

**Reste à faire.** La publication sur GitHub Pages demande Git, qui n'est pas installé, et un compte GitHub : ce sont des actions de l'utilisatrice. Ensuite viendront l'oral (3 slides) et le rapport.

**Préparation de la mise en ligne (2026-11-08).**
- `site/_site/` : 25 fichiers, 2,3 Mo. Ajout d'un fichier `.nojekyll` pour que GitHub Pages serve les fichiers tels quels.
- Aucun chemin local ni identifiant personnel trouvé dans les pages HTML.
- La page Méthode attribuait la validation à « l'autrice » : formulation neutre adoptée, puis page rendue à nouveau.
- Voie retenue : Git n'est pas installé, donc on publie sans Git. L'utilisatrice crée un dépôt public sur github.com, y dépose le contenu de `site/_site/` par l'interface web, puis active Pages (branche `main`, dossier racine).
- La création du compte et le dépôt des fichiers sont faits par l'utilisatrice. Je ne crée pas de compte et je ne publie rien à sa place.
- Mise en ligne reportée par l'utilisatrice le 2026-11-08 : le site n'est pas encore publié.

---

### 2026-11-08 — Feuille de route : tableau de bord de suivi du marché (proposée, non lancée)

**Demande de l'utilisatrice.** Elle trouve le site insuffisant et veut un tableau de bord actualisé chaque jour, dans l'esprit des pages de cours des sites boursiers, avec 4 éléments :
- les prix (dernier cours, variation, OHLC) ;
- des prévisions quotidiennes : volatilité à 5 et 20 séances, écart aux moyennes mobiles MM60 et MM120, régime de marché ;
- les actualités ;
- le choix entre Quarto mis à jour automatiquement et Streamlit ou Dash.

**Points de vigilance, issus des résultats du projet.**
- **Prévision de volatilité.** Le modèle à facteurs ne bat pas le HAR : il le dégrade sur les 4 horizons. Le tableau de bord utilisera donc le **HAR**, réestimé chaque jour sur le passé seul. C'est le meilleur prévisionniste mesuré. Afficher le modèle à facteurs comme prévision contredirait nos propres résultats.
- **Écart aux MM60 et MM120.** C'est un **indicateur descriptif**, pas une prévision. Son retour vers zéro est en grande partie mécanique (piste A).
- **Régime.** Même règle que la piste C : volatilité des 60 dernières séances au-dessus du 80e centile de son passé. C'est un état observé, pas une prévision de crise.
- **« Temps réel ».** Yahoo Finance via yfinance donne des cours retardés et une fin de séance fiable. `yfinance` n'est pas une API officielle et peut casser. L'actualisation se fera une fois par jour, après la clôture, et la date de la donnée sera affichée.
- **Actualités.** Reuters a fermé ses flux RSS publics. On prévoit Google News RSS, avec une requête sur le cacao en français et en anglais : il reste à tester. Pour Boursorama, l'existence d'un flux RSS n'est pas vérifiée. On n'affiche que le titre, la source, la date et le lien, jamais le texte des articles (droit d'auteur).
- **Mention obligatoire :** « Outil pédagogique, pas un conseil en investissement. »

**Choix technique recommandé : Quarto, avec une page au format `dashboard`.**
- Le cours demande un site Quarto avec Plotly, accessible par URL publique. Une page `format: dashboard` (Quarto 1.4 et plus, on a la 1.10) donne des tuiles de chiffres, des graphiques et une liste d'actualités, sans serveur.
- Un site statique s'héberge gratuitement sur GitHub Pages. Une tâche planifiée peut le reconstruire chaque jour : GitHub Actions en ligne, ou le Planificateur de tâches Windows en local.
- Streamlit et Dash demandent un serveur qui tourne en permanence. Sur le port local, l'outil n'a pas d'URL publique. En ligne, il faut Streamlit Community Cloud ou un hébergeur, avec un compte et un dépôt GitHub. C'est plus interactif, mais plus fragile, et ce n'est pas l'outil demandé par le cours. À garder en extension.

**Architecture proposée.**

| Élément | Fichier | Rôle |
|---|---|---|
| Prix | `src/cacao/marche.py` | Télécharge CC=F en OHLC et volume par yfinance, ajoute seulement les nouvelles séances à `data/live/cc_f.parquet`, contrôle les doublons et les sauts |
| Indicateurs | `src/cacao/indicateurs.py` | HAR réestimé sur le passé (prévisions à 5 et 20 séances) ; écarts aux MM60 et MM120 ; régime de volatilité |
| Actualités | `src/cacao/actualites.py` | Lit le flux RSS avec la bibliothèque standard, garde titre, source, date et lien, met en cache dans `data/live/actualites.json` |
| Orchestration | `scripts/40_actualiser_marche.py` | Enchaîne prix, indicateurs, actualités et rendu du site, avec un journal d'exécution |
| Page | `site/marche.qmd` (`format: dashboard`) | Tuiles (dernier cours, variation, volatilité prévue, régime), chandeliers sur 6 mois avec MM60 et MM120, écart, actualités |
| Tests | `tests/test_indicateurs.py` | Aucun regard vers le futur : HAR et régime inchangés si on modifie les séances futures |
| Automatisation | GitHub Actions ou Planificateur Windows | Lancement quotidien après la clôture du cacao à New York |

**Étapes de mise en place.**
1. Module des prix et ses tests.
2. Indicateurs (HAR, écarts, régime) et leurs tests de non-regard vers le futur.
3. Module d'actualités, avec un test réel du flux Google News.
4. Page `marche.qmd` en format dashboard, vérifiée dans le navigateur.
5. Script d'actualisation de bout en bout.
6. Automatisation. Le Planificateur Windows est une configuration persistante, à faire avec l'accord explicite de l'utilisatrice. GitHub Actions demande un dépôt GitHub.
7. Mise en ligne avec le reste du site.

Durée estimée pour les étapes 1 à 5 : une demi-journée. L'oral est le 18 novembre, il faudra garder du temps pour les slides et le rapport.

**Statut.** Proposition en attente de validation par l'utilisatrice.

---

### 2026-11-08 — Construction du tableau de bord « Marché du jour »

**Validation.** L'utilisatrice valide toute la feuille de route : Quarto en format dashboard, automatisation quotidienne, volatilité uniquement par le HAR, MM60/MM120 et régime présentés comme indicateurs d'état, yfinance pour CC=F, Google News RSS (titre, source, date et lien seulement), mention « Outil pédagogique, pas un conseil en investissement ».

**Code.**
- `src/cacao/marche.py` : téléchargement de CC=F, mise à jour incrémentale de `data/live/cc_f.parquet` (les 10 derniers jours sont retéléchargés, et la dernière version gagne), contrôles et chiffres clés.
- `src/cacao/indicateurs.py` : HAR réestimé chaque jour sur les seules dates dont la cible est connue ; écarts aux MM60 et MM120 ; régime de volatilité.
- `src/cacao/actualites.py` : deux flux Google News (français et anglais, 14 derniers jours). On garde les titres qui parlent du cacao, sans doublons, avec un cache. Si le flux échoue, le dernier cache est réutilisé.
- `scripts/40_actualiser_marche.py` : enchaîne cours, indicateurs, actualités et rendu du site, et note chaque exécution dans `data/live/journal.csv`.
- `scripts/40_actualiser_marche.ps1` : lanceur pour la tâche planifiée.
- `site/marche.qmd` (nouvel onglet « Marché du jour ») : 5 tuiles, résumé de la séance, chandeliers sur 6 mois avec MM60 et MM120, actualités, écart aux moyennes sur 2 ans, régime avec son seuil, note de lecture. `freeze: false` pour que la page soit recalculée à chaque rendu.
- `tests/test_indicateurs.py` : HAR, régime et écarts inchangés quand on modifie les séances futures ; seuil égal au centile du passé strict ; fusion et contrôle des cours. 39 tests passés.

**Problèmes et solutions.**
1. **Données Yahoo rejetées au premier lancement.** 606 séances sur 5 492 (11 %) ont une clôture hors de la fourchette plus haut / plus bas. La clôture Yahoo de CC=F est le prix de règlement, qui peut sortir de la fourchette des échanges. Certaines séances proches d'un passage d'échéance ont aussi un volume de 1 ou 2 contrats. Solution : seules les vraies erreurs bloquent (doublons, ordre, clôture manquante, plus haut sous le plus bas). Les deux particularités sont signalées dans `indicateurs.json`, jamais corrigées.
2. **Actualités hors sujet** (élections, biomasse) à cause des mots « Côte d'Ivoire » et « Ghana » dans la requête. Solution : filtre sur le titre (cacao, cocoa, chocolat, fèves).
3. **Graphiques en 4 ou 5 exemplaires.** En format dashboard, Quarto affiche chaque instruction d'une cellule. Solution : résultats intermédiaires assignés à `_`.
4. **Tuiles géantes, puis graphiques qui débordent et légendes tronquées.** Solution : hauteurs de lignes en pixels, figures en HTML à largeur 100 % et hauteur fixe, nom de chaque courbe en étiquette au bout de la ligne au lieu de la légende. La dernière version a été vérifiée par les dimensions dans la page (figures plus étroites que leur carte). La dernière capture d'écran n'a pas pu être prise : fenêtre masquée.

**Résultats du jour (séance du 06/11/2026).** 5 119 $/t (−1,20 %). Volatilité prévue par le HAR : 37 % à 5 séances et 39 % à 20 séances. Écart à la MM120 : −3,7 %. Régime agité : volatilité 60 séances de 42 %, au-dessus du seuil de 38 %. 25 titres d'actualité.

**Automatisation (étape 6).** Tâche planifiée Windows « Cacao - actualisation du tableau de bord », créée avec l'accord de l'utilisatrice (validation de l'automatisation locale). Elle tourne chaque jour à 23 h, pour l'utilisatrice connectée, sans droits administrateur, et rattrape une exécution manquée. Essai immédiat : code 0, site rendu. Pour la supprimer : `Unregister-ScheduledTask -TaskName "Cacao - actualisation du tableau de bord"`.

**Mise en ligne (étape 7).** `site/_site` est prêt : 36 fichiers, 5,5 Mo, `.nojekyll`, aucun chemin personnel. Le dépôt sur GitHub reste à faire par l'utilisatrice, comme décrit plus haut. Limite : en ligne, la page ne se met à jour que si l'on dépose à nouveau `_site`. Une mise à jour en ligne automatique demanderait GitHub Actions, donc un dépôt contenant aussi le code et une partie des données.

**Limites déclarées sur la page.** Cours retardés et API non officielle. Le HAR prévoit l'amplitude, pas le sens. Le régime décrit l'état du marché.

---

### 2026-11-08 — Retours de l'utilisatrice sur le site : plus de contexte

**Retours.**
- Les icônes des tuiles sont jugées laides.
- Le cours n'est montré que sur 6 mois.
- MM60 et MM120 ne sont pas expliquées.
- Sur la page Données, on ne comprend pas pourquoi deux graphiques se superposent : c'était le curseur de zoom de Plotly.
- La pluie et El Niño manquent de contexte.
- Plus généralement, le site manque d'explications.

**Modifications.**
- **Tableau de bord** (`site/marche.qmd`) :
  - icônes retirées ;
  - encadré « À quoi sert cette page ? » ;
  - tuiles en vocabulaire simple (« agitation prévue », « état du marché ») et nombres au format français (virgule, espace, vrai signe moins) ;
  - phrase qui traduit la volatilité annualisée en variation moyenne par jour (39 % par an, soit environ 2,4 % par jour, calculé comme 39 / √252) ;
  - cours **depuis 2005**, avec des boutons 6 mois / 1 an / 5 ans / Depuis 2005. Chaque bouton fixe aussi l'échelle verticale, sinon le pic de 2024 écrase l'affichage. Vue par défaut : 1 an ;
  - explication sous chaque graphique : lecture des bougies, définition de MM60 (moyenne des 60 dernières clôtures, environ 3 mois) et de MM120 (environ 6 mois), lecture de l'écart et du régime.
- **Page Données** :
  - introduction sur la règle de publication ;
  - le prix : ce qu'est un contrat à terme, pourquoi il est intéressant. Curseur de zoom remplacé par des boutons, événements numérotés et tableau des 6 événements avec leur statut de vérification ;
  - la pluie : pourquoi elle compte (sécheresse et floraison, humidité et maladies, formulé sans chiffre), poids de la Côte d'Ivoire et du Ghana parmi les 9 pays suivis (environ la moitié en 2026, d'après nos poids FAOSTAT), lecture des écarts-types, prudence sur la saison sèche (+3 à +4,7 début 2026, sur des normales faibles) ;
  - El Niño : explication courte et lecture de l'ONI. Épisodes 2015-2016 (+2,6) et 2023-2024 (environ +2,0) tirés de nos données ;
  - pour chaque série, ce que le projet en conclut.
- **Résultats** : section « En bref » et glossaire (séance, exactitude équilibrée et seuil de 0,5, volatilité et RMSE, benchmark, hors échantillon).
- **Accueil** : paragraphe de contexte sur le marché et lien vers « Marché du jour ».
- **Tous les graphiques** : séparateurs français (`separators=", "` dans `site/_commun.py`).

**Vérification.** Site rendu sans erreur. Dimensions contrôlées dans la page : aucune figure ne dépasse sa carte. Captures prises du tableau de bord et de la page Données.

**Précaution sur les faits (2026-11-08).** Les phrases agronomiques et la description d'El Niño restent générales et prudentes (« souvent associé à »). Elles ne contiennent ni chiffre ni événement daté qui ne viennent pas de nos données ou de `config/evenements.csv`.

---

### 2026-11-08 — Deux propositions de l'utilisatrice (réponse donnée, rien de lancé)

**1. Effet de la météo sur la production (module d'impact agronomique).**
- **Idée :** expliquer la production et les rendements par pays avec nos anomalies météo pondérées par MapSPAM.
- **Structure proposée :**
  - `scripts/41_meteo_annuelle.py` construit des indices météo par pays et par campagne : pluie et température par saison, alignées sur le calendrier du cacao.
  - `scripts/42_impact_agronomique.py` estime un panel de 9 pays, avec effets fixes pays et année, et regroupe les erreurs par pays. Avec seulement 9 groupes, l'intervalle viendra d'un bootstrap sauvage.
  - Une page Quarto `impact.qmd` présentera les résultats.
- **Lecture causale :** la météo est exogène, ce qui rend une lecture causale défendable, sous réserve des tests placebo (météo de l'année suivante, permutations).
- **Limites à déclarer :**
  - la production FAOSTAT du cacao est souvent estimée par la FAO elle-même ;
  - les poids MapSPAM sont fixes (2010) ;
  - l'échantillon est petit : environ 20 ans × 9 pays avec ERA5 et NASA depuis 2005, environ 34 ans avec CHIRPS depuis 1991, mais pour la pluie seulement ;
  - les éditions ICCO sont trop peu nombreuses pour servir de cible.
- **Statut :** c'est une extension hors protocole, donc exploratoire. Elle est à valider par l'utilisatrice.

**2. Graphique historique sur 21 ans avec les prévisions.**
- **Problème :** aucun de nos modèles ne prévoit un **niveau de prix**. Ils prévoient le sens (une probabilité) et la volatilité. Tracer une « courbe de prix prévu » reviendrait à inventer une prévision.
- **Proposition honnête :** le cours de 2005 à 2026, plus un **tunnel de volatilité hors échantillon**. Chaque jour, la fourchette attendue à 20 séances vaut P_t × exp(±σ̂ × √(20/252)), avec σ̂ la prévision HAR réestimée chaque année sur le passé. On compare ensuite au cours réalisé 20 séances plus tard. On publie le **taux de couverture**, c'est-à-dire la part des cas où le cours tombe dans le tunnel, environ 68 % attendus pour ±1 écart-type, avant et depuis 2024.
- Ajouts possibles : la zone de la crise de 2024-2026, les marqueurs des 6 événements vérifiés, et éventuellement la probabilité de hausse du modèle en bas du graphique, qui montrera qu'elle reste proche de 0,5.
- **Statut :** en attente du feu vert de l'utilisatrice.

---

### 2026-11-08 — Module d'impact de la météo sur la production (réalisé)

**Validation.** L'utilisatrice choisit le module production. Les règles sont écrites au point 12 de `protocole.md` **avant** le calcul : cible, variables, modèle, inférence, contrôles.

**Constat sur les données, qui a changé la cible.** De 1991 à 2024, le rendement FAOSTAT est estimé par la FAO (code E) 29 années sur 34 en Côte d'Ivoire et au Cameroun, 17 au Ghana, 15 au Nigeria. En Côte d'Ivoire, il reste figé vers 500 kg/ha. La production est officielle (code A) dans 273 cas sur 306. La cible devient donc le log de la production, pas le rendement.

**Code.**
- `scripts/41_meteo_annuelle.py` : construit `data/processed/impact_panel.parquet`, soit 9 pays de 1991 à 2025, avec la pluie annuelle CHIRPS et la Tmax annuelle NASA (depuis 2005), pondérées par MapSPAM, plus la production FAOSTAT et son code de qualité.
- `scripts/42_impact_agronomique.py` : moindres carrés avec effets fixes pays et année, et tendance par pays.
  - Variables : pluie centrée-réduite par pays de l'année N et N−1, avec leurs carrés.
  - Erreurs regroupées par pays (CR1), avec une p-value par bootstrap sauvage sous l'hypothèse nulle (Rademacher, 512 combinaisons).
  - Permutation des années de météo à l'intérieur de chaque pays (2 000 tirages, graine 42).
  - Contrôles : placebo sur la pluie de N+1, données officielles seulement, sans l'Indonésie, sans tendances, et un modèle avec température sur 2006-2024.
  - Sorties : `outputs/metriques/impact_coefficients.csv`, `impact_permutation.csv` et `impact_courbe.csv`.
- `site/impact.qmd` : nouvel onglet « Météo et production ».

**Résultats : aucun effet démontré.**
- Permutation, modèle principal : la pluie explique 2,6 % des variations propres à chaque pays (p = 0,164). Sans tendances : 1,5 % (p = 0,455). Température en plus de la pluie : 2,7 % (p = 0,174).
- Aucun coefficient n'est significatif à 5 % par le bootstrap. Le plus proche est la pluie de N−1 au carré, avec p = 0,074 dans le modèle principal et entre 0,053 et 0,074 dans les variantes. Son signe n'a pas d'explication agronomique simple, donc il n'est pas interprété.
- Placebo de N+1 : p = 0,74 et 0,36, aucun lien. C'est attendu.
- Effets estimés, non significatifs : environ −4 % de production pour une année nettement humide (+1,5 écart-type).

**Choix de présentation.** La bande à 95 % issue du bootstrap sauvage sans hypothèse nulle était plus étroite que ne le laisse le test formel (p ≈ 0,07). Avec 9 pays, elle sous-estime l'incertitude. Elle n'est donc pas affichée : la page montre l'effet estimé seul, avec la mention « non significatif ».

**Lecture et limites, affichées sur la page.**
- Un résultat nul ne prouve pas l'absence d'effet.
- La pluie annuelle et nationale est trop grossière, la production FAOSTAT imparfaite et décalée par rapport à la campagne, l'échantillon petit (9 pays, environ 33 ans), et d'autres facteurs dominent (maladies, vergers, prix aux planteurs, contrebande).
- Extensions possibles, à présenter comme exploratoires si on les fait : indicateurs de saison sèche, production par campagne ou par région, températures extrêmes.

---

### 2026-11-08 — Graphique historique sur 21 ans avec le tunnel de volatilité

**Validation.** L'utilisatrice valide le format : cours réel en ligne continue, tunnel HAR hors échantillon à 20 séances avec son taux de couverture, crise 2024-2026 et événements, probabilité de hausse en sous-graphique.

**Code.**
- `scripts/43_tunnel_historique.py` : HAR réestimé chaque année sur le passé (purge de 20 séances, comme `plis`). Pour chaque séance t, le tunnel du cours à t+20 vaut P_t × exp(±k σ̂ √(20/252)), avec k = 1 ou 2. Il est daté à la séance visée. Sorties : `outputs/metriques/tunnel_har20.parquet` et `tunnel_couverture.csv`.
- `site/marche.qmd` : carte « 21 ans de cours », avec cours en échelle logarithmique, tunnel en pointillés, zone 2024-2026, 6 événements numérotés, et probabilité de hausse du Gradient Boosting à 20 séances en dessous. Une option `etiquettes` a été ajoutée à `afficher`.

**Résultats : couverture du tunnel à ±1 écart-type** (68 % attendus pour une loi normale).

| Période | À ±1 écart-type | À ±2 écarts-types | Largeur moyenne à ±1 |
|---|---:|---:|---:|
| 2010-2023 | 69 % | 96 % | ±8 % |
| 2024-2026 | 58 % | 83 % | ±16 % |

- Avant la crise, le tunnel est **bien calibré**.
- Pendant la crise, il s'élargit, sans suffire : les chocs dépassent ce que l'agitation passée annonçait.

**Correction d'une attente.** L'utilisatrice pensait voir une probabilité de hausse « collée à 0,5 ». En réalité, elle est **très dispersée** : de 0,06 à 0,98, médiane 0,54, et seulement 28 % des valeurs entre 0,4 et 0,6. Pourtant, l'exactitude équilibrée reste à 0,508. Le modèle est donc **trop confiant**, pas prudent. Le texte de la page le dit.

**Vérification.** Rendu sans erreur. Dimensions contrôlées (1 195 × 655 px dans une carte de 1 229 px). Capture finale prise.

**Avis sur la régression des rendements (proposée par l'utilisatrice, non lancée).**
- **Technique :** facile à intégrer. `cible_rendement_h` existe déjà dans le dataset, et `predire` accepte un régresseur avec `ecart_bootstrap` en RMSE. Environ 10 minutes de calcul pour 5 horizons.
- **Méthode :**
  - évaluer sur les **rendements** et non sur le prix reconstruit : la RMSE en dollars est dominée par P_t et fait paraître tous les modèles proches ;
  - prendre comme benchmarks la marche aléatoire (rendement nul) et la moyenne passée ;
  - c'est une analyse décidée après les résultats : exploratoire, avec un amendement au protocole (point 13) et une correction de Bonferroni sur 5 horizons ;
  - la courbe de prix prévu ne serait tracée que si le benchmark est battu.
- **Pronostic :** faible, puisque la classification du sens a échoué.

---

### 2026-11-08 — Régression des rendements cumulés (point 13 du protocole)

**Validation.** L'utilisatrice valide (« Oui, lance-la »). Les règles sont écrites au point 13 de `protocole.md` avant le calcul.

**Code.** `scripts/44_regression_rendements.py` : Gradient Boosting en régression (réglages du point 4) sur R = P(t+h)/P(t) − 1, avec h de 1 à 120 séances. Benchmarks : marche aléatoire (rendement nul) et moyenne passée. RMSE sur les rendements, bootstrap à 99 % par blocs de max(20, h). Lecture de contrôle : sans passage jusqu'à 20 séances, rendement avec les jours de saut mis à zéro à 60 et 120 séances. Sorties : `outputs/metriques/regression_rendements.csv` et `regression_predictions.parquet`. Durée : environ 1 minute.

**Résultats : le modèle fait pire que la marche aléatoire.**

| Horizon | RMSE modèle | RMSE benchmark | IC 99 % de l'écart (positif = modèle meilleur) | Signe correct |
|---:|---:|---:|---|---:|
| 1 | 0,0228 | 0,0224 | −0,0007 à −0,0002 | 48 % |
| 5 | 0,0537 | 0,0508 | −0,0047 à −0,0012 | 51 % |
| 20 | 0,1140 | 0,1037 | −0,0186 à −0,0009 | 52 % |
| 60 | 0,2221 | 0,1983 | −0,0441 à −0,0086 | 47 % |
| 120 | 0,3237 | 0,2922 | −0,0569 à −0,0135 | 42 % |

- En lecture brute, le modèle est significativement **moins bon** que la marche aléatoire aux 5 horizons. Lecture de contrôle : même conclusion, sauf à 20 séances, où l'intervalle touche zéro (−0,0214 à +0,0006).
- Comme le prévoyait la règle, **aucune courbe de prix prévu n'est tracée**.
- Ce résultat confirme la conclusion générale : la meilleure prévision du prix de demain est le prix d'aujourd'hui.

**Site (2026-11-08).** Section « Et en prévoyant directement le rendement ? » ajoutée à `site/resultats.qmd`, avec le graphique d'écarts et intervalles. Je l'avais d'abord insérée au milieu de la conclusion de la robustesse : ordre corrigé, puis page rendue à nouveau.

---

### 2026-11-08 — Préparation de la publication avec Git et GitHub

**Choix de l'utilisatrice.**
- Publication par Git plutôt que par dépôt manuel, pour que les mises à jour puissent partir d'ici.
- Contenu du dépôt : **code et site**. Les données brutes restent sur le PC.

**Installation.** Git for Windows 2.56.0.4 installé avec `winget` (catalogue winget, empreinte de l'installateur vérifiée), après accord explicite de l'utilisatrice sur sa licence GPL v2. Le gestionnaire de connexion à GitHub (Git Credential Manager 2.9.1) est inclus. **Erreur signalée à l'utilisatrice :** ma première commande de vérification contenait `--accept-source-agreements`, ce qui a accepté sans lui demander les conditions du catalogue Microsoft Store de winget. Cette acceptation n'a rien installé. Je n'utilise plus que le catalogue winget.

**Organisation pour GitHub Pages.**
- Le site est rendu dans `docs/` (`output-dir: ../docs` dans `site/_quarto.yml`), avec un fichier `.nojekyll`. Pages publiera la branche `main`, dossier `/docs`.
- `scripts/40_actualiser_marche.py` rend donc aussi le site dans `docs/`.
- `.gitignore` exclut : `data/` (8 Go), MapSPAM (189 Go), les consignes du cours, `.venv`, `.claude`, `site/_site`, `site/_archive`.
- `README.md` présente le projet, l'organisation du dépôt et la façon de reproduire les résultats.

**Dépôt local.** `git init -b main` est fait, sans commit. Le premier ajout comprendrait 165 fichiers pour 16,5 Mo, aucun au-dessus de 2 Mo.

**À faire par l'utilisatrice.** Créer le compte GitHub et un dépôt public vide, puis me donner l'identifiant et le nom du dépôt. Les commits porteront l'adresse « noreply » de GitHub, pour ne pas rendre publique son adresse personnelle. Elle se connectera elle-même au premier envoi, par la fenêtre du navigateur.

---

## Journal d'utilisation de l'IA

*Tenu pour la règle 1 des consignes et la section du rapport sur les outils d'IA.*

| Date | Outil | Prompt | Usage | Vérification |
|------|-------|--------|-------|--------------|
| 2026-11-04 | Claude Code (Claude Opus 5.5) | Prompt 1, texte intégral dans `Consignes du projet/PROMPT/PROMPT.docx` | Inspection des fichiers, proposition de structure, rédaction de ce carnet | Constats issus de la lecture directe des fichiers et des en-têtes de CSV ; carnet à relire par l'utilisatrice |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « tu peux extraire toute les données dans les dossiers de MapSPAM zones de production dans projet cacao ? » | Script d'extraction, corrigé après un premier échec | Comparaison noms et tailles de tous les fichiers avec les ZIP sources ; lecture d'un CSV de production |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « vu ce tu as vu fais moi un résumé des données récoltés » | Résumé des données disponibles, correction du carnet | Résumé fondé sur les contrôles déjà réalisés dans ce carnet |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « okay change le nom du dossier » | Renommage du dossier MapSPAM, mise à jour du script et du carnet | Liste du dossier et décompte des fichiers après renommage |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « okay supprimme 2000 alors, ça prend de place pour rien » | Déplacement du millésime 2000 vers la Corbeille, régénération du manifeste | Contrôle de la capacité de la Corbeille, du contenu du dossier et de l'absence de `spam2000` dans le manifeste |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | Prompt 2 : « CADRAGE TEMPOREL ET INTERDICTION D'INVENTER DES DONNÉES », départ en 2005 et six thématiques | Revue critique des sources, structure actualisée, ordre de collecte | Inventaire refait ; revue issue de connaissances générales, **non testée à ce stade** |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « dossier caco c'est projet cacao j'ai refait l'erreur juste rename le puis reprend les instruction » | Création de la structure, environnement Python, script de collecte de la thématique 1 | Test d'import des paquets, qui a révélé le blocage ; script non exécuté |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « c'est bon non ? » | Collecte de la thématique 1, scripts de contrôle qualité, détection des changements d'échéance | Contrôles statistiques des séries ; hypothèse d'échéance testée sur le rythme annuel, sans preuve directe faute de contrats expirés |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « Tu peux utiliser Barchart ou les données mensuelles de l'ICCO/Banque Mondiale comme "valeurs de contrôle" [...] » | Contrôle croisé proposé par l'utilisatrice | Le contrôle a invalidé une recommandation de l'IA, retirée du plan ; l'idée du contrôle vient de l'utilisatrice |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « Je souhaite que notre modèle et notre dataset principal soient structurés en fréquence JOURNALIÈRE [...] », puis « j'aimerais faire les deux ... » | Discussion de la fréquence et des horizons, grille quotidienne, tests | 10 tests automatisés, comparaison avec la source brute ; les horizons ont été décidés par l'utilisatrice |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « mais pour le cours du lendemain on peut ne prendre en les 7 facteurs et les adapter en fonction de daily ou non [...] et adapter leur pondérations ? », puis question sur l'environnement Positron | Formulation du plan d'analyse, configuration de Positron | Idée d'adapter les facteurs venue de l'utilisatrice, plan validé par elle ; imports de `.venv` testés |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « tu as donc déjà récupérer les chiffres de Production [...] ne se contredise t'ils pas avec ceux de MapsPAM ? » | Collecte FAOSTAT et comparaison avec MapSPAM | Comparaison chiffrée par pays et millésime ; erreur d'encodage repérée et corrigée |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « compare avec ICCO » | Recherche web, collecte des PDF ICCO, extraction et comparaison | Valeurs lues dans les PDF, contrôle du nombre de colonnes ; explication sur l'Indonésie non confirmée |
| 2026-11-04 | Claude Code (Claude Opus 5.5) | « montre moi les différence de data btw FAOSTAT et MapSPAM concernant l'indonésie » | Comparaison de la production, de la surface et du rendement | Valeurs lues dans les fichiers sources ; hypothèses signalées comme non vérifiées |
| 2026-11-04 | Claude Code (Claude Opus 5.5) + texte d'arbitrage fourni par l'utilisatrice | « Arbitrage méthodologique – Traitement de la production indonésienne et gestion météo [...] » | Consignation de l'arbitrage, extraction des cellules MapSPAM | L'arbitrage est une décision de l'utilisatrice ; les précisions sur l'ICCO et le look-ahead viennent de l'IA |
| 2026-11-05 | Claude Code (Claude Opus 5.5) + texte d'arbitrage fourni par l'utilisatrice | « Arbitrage validé concernant le millésime MapSPAM et l'extraction météo [...] Tu peux valider cette étape et poursuivre le pipeline d'extraction météo. » | Sélection et regroupement des points, collecte NASA POWER, indices par pays | Décompte des fichiers, contrôle des manquants, somme des poids ; le choix 2010 est de l'utilisatrice |
| 2026-11-06 | Claude Code (Claude Opus 5.5) | « okay on fait quoi mtn la ? t'as tout niveau météo ? » | Contrôle ERA5, repérage de l'anomalie de pluie, test d'écrêtage | Comparaison chiffrée sur 14 points ; cause non confirmée, documentation POWER illisible (erreur 404) |
| 2026-11-06 | Claude Code (Claude Opus 5.5) | « et on peut pas vérifié si il y'a des article à ce sujet ? » | Recherche web, lecture de deux signalements du bug ×24, test sur la fenêtre de requête | Hypothèse testée par requêtes directes à l'API et écartée ; signalements GitHub non confirmés par la NASA |
| 2026-11-06 | Claude Code (Claude Opus 5.5) | « Tester ERA5 partout » | Test du modèle sur un point, collecte de la pluie ERA5 pure, correction du contrôle précédent | Le test a invalidé un contrôle de l'IA : les données par défaut d'Open-Meteo n'étaient pas de l'ERA5 pur après 2016 |
| 2026-11-06 | Claude Code (Claude Opus 5.5) | « oui oui commence les autres collecte du coup » | Collecte ENSO, pesticides, engrais, incendies, rayonnement et vent ; diagnostic réseau | Tests d'accès par source, décompte des lignes ; aucun contrôle de qualité de fond à ce stade |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « Je retiens ERA5 quotidien et CHIRPS mensuel pour la pluie » | Module d'anomalies, tests, script d'indices de pluie | 4 tests dont un test de look-ahead ; le choix des sources est celui de l'utilisatrice, sur proposition de l'IA |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « la nasa est disponible elle chaque jour ? [...] prévision météo [...] et ensuite la météo réelle en comparaison », puis « Oui, teste GEFS » et « Lance tout » | Plan prévisions et comparaison, test d'accès GEFS, script de collecte sur trois formats | Test sur une date par format ; collecte complète non vérifiée à ce stade ; exigence de prendre en compte les prévisions rappelée par l'utilisatrice |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « du coup ? » | Contrôles, dataset quotidien avec délais, benchmark | 16 tests ; relecture qui a révélé un bug de date sur l'ONI, corrigé ; lecture de l'artefact d'échéance proposée par l'IA, à valider |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « Oui, continue » | Collecte CFTC, Trends, GPR, GDELT, intégration au dataset | Écarts entre rapports CFTC, doublons et zéros contrôlés ; délais en partie supposés, signalés comme tels |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « Finir les données » | Test USDA, prix Banque mondiale, FAOSTAT annuel, base d'événements | Décalage N+2 vérifié sur deux dates ; dates d'événements reprises de résultats de recherche, avec statut de vérification |
| 2026-11-07 | Claude Code (Claude Opus 5.5) | « Figer les règles à l'avance [...] mettons nous d'accors la dessus » | Rédaction du protocole, répartition en familles, pipeline et tests | 28 tests, essai avec cible aléatoire ; protocole à valider par l'utilisatrice |
| 2026-11-07 | Claude Code (Claude Opus 5.5) + consigne fournie par l'utilisatrice | « Consigne d'intégration multi-horizons (1j, 5j, 20j, 60j, 120j) [...] » | Cibles, purge, benchmark, protocole, page Quarto, cible sans sauts | 34 tests dont la purge par horizon ; matrice décidée par l'utilisatrice ; cible sans sauts et correction des tests multiples proposées par l'IA |
| 2026-11-07 | Claude Code (Claude Opus 5.5) + consigne fournie par l'utilisatrice | « Voici la validation finale [...] Finalise d'abord la collecte et le nettoyage de toutes les données [...] » | Familles corrigées, revue du change, température GEFS, événements, inventaire | Inventaire par fichier ; 34 tests ; lecture des cotations autour de chaque saut ; arbitrages validés par l'utilisatrice |
| 2026-11-08 | Fin de la collecte GEFS, contrôle de qualité, correction des ruptures, intégration | Claude Code (Opus 5.5) a diagnostiqué les échecs, écrit les scripts 35 et 36 et proposé la correction. L'utilisatrice a choisi l'option et la règle d'imputation | Doublons GRIB vérifiés octet pour octet ; test de troncature ; raccords mesurés avant et après 2020 ; interpolation entre dates refusée car elle regarde le futur |
| 2026-11-08 | Modèle à facteurs selon le protocole | Claude Code (Opus 5.5) a écrit `scripts/37_modele_facteurs.py`, corrigé un plantage de `HistGradientBoosting` et appliqué la règle « pas de hiérarchie sans benchmark battu » | Vérification automatique des colonnes interdites ; réglages inchangés ; résultat négatif rapporté tel quel ; Random Forest gardée comme contrôle |
| 2026-11-08 | Tests de robustesse | Claude Code (Opus 5.5) a écrit `scripts/38_robustesse.py` (pluie NASA, GEFS, oracle, sans 2024-2026) | La base refaite redonne les mêmes écarts ; oracle signalé comme utilisant le futur ; test 6 déclaré non fait |
| 2026-11-08 | Trois pistes exploratoires de l'utilisatrice | Claude Code (Opus 5.5) a corrigé la prémisse sur la volatilité, écrit les règles avant le calcul (protocole, point 11), puis `scripts/39_pistes_complementaires.py` | Bonferroni par bloc ; caractère mécanique de la cible d'écart signalé ; recouvrement entre régime et années signalé ; stocks non inventés |
| 2026-11-08 | Site Quarto de 6 pages | Claude Code (Opus 5.5) a écrit les pages, la palette et les graphiques Plotly, puis rendu le site | Toutes les valeurs lues dans les sorties ; vérification visuelle dans le navigateur ; marge corrigée ; erreurs de console signalées |
| 2026-11-08 | Tableau de bord « Marché du jour » et actualisation quotidienne | Claude Code (Opus 5.5) a écrit les modules de cours, d'indicateurs et d'actualités, la page dashboard, le script et la tâche planifiée | Tests de non-regard vers le futur ; particularités Yahoo signalées sans être corrigées ; HAR seul pour la volatilité ; titres et liens seulement pour les actualités |
| 2026-11-08 | Module d'impact de la météo sur la production | Claude Code (Opus 5.5) a repéré les rendements FAOSTAT estimés, écrit les règles avant le calcul (point 12), les scripts 41 et 42 et la page `impact.qmd` | Bootstrap sauvage adapté aux 9 pays ; permutation ; placebo ; bande trop optimiste retirée ; résultat nul rapporté tel quel |
| 2026-11-08 | Graphique sur 21 ans et régression des rendements | Claude Code (Opus 5.5) a écrit les scripts 43 et 44, le graphique et l'amendement du point 13 | Tunnel hors échantillon avec sa couverture mesurée ; attente « probabilité collée à 0,5 » corrigée par les données ; évaluation sur les rendements, pas sur le prix ; pas de courbe de prix prévu sans benchmark battu |

