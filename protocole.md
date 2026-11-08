# Protocole d'analyse

**Statut : validé par l'utilisatrice le 2026-11-07. Exécution permise seulement après la fin de la phase 1.** Ce fichier est figé avant tout résultat de modèle à facteurs. Toute modification ultérieure doit être datée et justifiée ici.

**Point validé à la même date :** la production FAOSTAT forme la famille `production_offre`, et la famille demande devient `demande_substituts`. Le total passe à 8 familles, confirmé par l'utilisatrice le 2026-11-07. La présentation devra le signaler, car le sujet initial en comptait 7.

Le benchmark sans facteurs a déjà été calculé avant ce protocole. Ses résultats ont donc pu influencer ces règles.

## 1. Question et cibles

Quelle famille de facteurs apporte le plus d'information sur le cacao, hors échantillon ?

Matrice d'horizons demandée par l'utilisatrice le 2026-11-07 :

| Horizon | Séances | Sens du rendement | Volatilité réalisée |
|---|---:|---|---|
| Très court terme | 1 | Oui | Non : une seule séance ne donne pas de volatilité |
| Très court terme | 5 | Oui | Oui |
| Moyen terme | 20 | Oui | Oui |
| Long terme, agronomique | 60 | Oui | Oui |
| Long terme, agronomique | 120 | Oui | Oui |

Soit 9 comparaisons. Le but est de voir où se situe le signal, du court terme au long terme agronomique.

## 2. Données

- Axe : séances de `CC=F`, dataset `data/processed/dataset_quotidien.parquet`.
- Une variable n'entre qu'une fois disponible, strictement avant la séance.
- Sont exclus des variables : `cible_*`, `passage_dans_*`, `saut_echeance`, `ROBUSTESSE_*`.
- Pas de niveau brut non stationnaire. Prix, taux de change et positions entrent en variations ou en anomalies.
- Pluie : ERA5 quotidien et CHIRPS mensuel. La pluie NASA sert au test de robustesse.

## 3. Variables et familles

Répartition dans `config/familles.yaml`. Pays retenus pour les variables par pays : Côte d'Ivoire, Ghana, Indonésie, et l'indice mondial. Les poids des familles sont appris par le modèle, jamais fixés à la main.

Fenêtres selon l'horizon :
- 1 et 5 séances : 5 et 20 jours.
- 20 séances : 20 et 60 jours.
- 60 et 120 séances : 60 et 120 jours.

## 4. Validation

- Tests par année civile, de 2010 à 2026, entraînement sur tout le passé.
- Purge : strictement égale à l'horizon `h` (1, 5, 20, 60 ou 120 séances) entre l'entraînement et le test.
- Hyperparamètres fixés à l'avance, sans réglage sur les périodes de test.
- `random_state=42`.

| Modèle | Réglages |
|---|---|
| Random Forest | 500 arbres, 20 observations minimum par feuille, `max_features` racine carrée |
| Gradient Boosting (`HistGradientBoosting`) | 300 itérations, taux 0,03, profondeur 3, 50 observations minimum par feuille |

Le meilleur des deux n'est pas choisi sur le test : le Gradient Boosting est le modèle principal, la Random Forest sert de contrôle.

## 5. Benchmarks à battre

Meilleur des modèles sans facteurs, sur 2010-2026 (`outputs/metriques/benchmark.csv`) :

| Horizon | Sens brut | Sens, lecture de contrôle | RMSE volatilité |
|---:|---:|---:|---:|
| 1 | 0,501 | 0,502 sans passage | Sans objet |
| 5 | 0,503 | 0,500 sans passage | 0,201 |
| 20 | 0,542 | 0,514 sans passage | 0,116 |
| 60 | 0,514 | 0,500 sans sauts | 0,093 |
| 120 | 0,500 | 0,513 sans sauts | 0,106 |

**Lecture de contrôle.** Jusqu'à 20 séances, on retire les fenêtres contenant un passage d'échéance. À 60 et 120 séances, 95 à 98 % des fenêtres en contiennent un : il ne reste que 138 lignes à 60 séances et aucune à 120. On utilise donc une cible où les jours de saut sont mis à zéro.

## 6. Critères de réussite

- **Métriques :** RMSE pour la volatilité, exactitude équilibrée pour le sens, AUC en complément.
- **Modèle réussi :** il bat le benchmark sur l'ensemble 2010-2026 **et** en lecture de contrôle, avec un intervalle de confiance de l'écart qui exclut zéro. Le bootstrap utilise des blocs de `max(20, h)` séances.
- **Tests multiples :** 9 comparaisons augmentent le risque de faux signal. L'intervalle est donc porté à 99,4 % (correction de Bonferroni, 5 % divisés par 9).
- **Prudence à long terme :** sur 2010-2026, il n'y a qu'environ 200 fenêtres indépendantes à 20 séances, 70 à 60 séances et 35 à 120 séances. Un résultat à long terme repose sur peu d'observations indépendantes et sera présenté comme tel.
- Les périodes 2010-2023 et 2024-2026 sont toujours présentées séparément.
- Si aucun modèle ne bat le benchmark sur une cible, on conclut qu'il n'y a pas de signal démontré sur cette cible. Aucune hiérarchie de familles n'est alors présentée comme un résultat.

## 7. Mesure de l'impact des familles

- **Mesure principale :** retrait d'une famille à la fois, puis perte de performance hors échantillon.
- **Mesure secondaire :** SHAP absolu moyen, agrégé par famille, sur les périodes de test.
- Une part SHAP moyenne n'est pas un effet causal, et les corrélations entre familles la répartissent. Tout désaccord entre les deux mesures sera publié.
- Les familles n'ont pas la même taille (42 variables pour le climat, 11 pour le marché à 20 séances). La somme SHAP favorise les grandes familles : elle sera aussi publiée par variable. Le retrait d'une famille, mesure principale, est moins exposé à ce biais.
- Poids comparés avant 2024 et à partir de 2024.

## 8. Tests de robustesse prévus

1. Pluie NASA à la place d'ERA5 et CHIRPS.
2. Sans 2024-2026.
3. Random Forest à la place du Gradient Boosting.
4. Exclusion des fenêtres de passage d'échéance.
5. Prévisions GEFS, avec et sans le test de météo parfaite.
6. MapSPAM 2020 corrigé et poids ICCO, si le temps le permet.

Toute analyse non listée ici sera présentée comme exploratoire.

## 9. Limites déjà connues

- Sauts de `CC=F` aux passages d'échéance, repérés après coup.
- Reprévisions GEFS 2005-2019, produites après coup.
- Chiffres FAOSTAT révisés, pas ceux connus à l'époque.
- Biais humide de la NASA en 2020-2023 sur l'humidité, et dérive d'ERA5 face à CHIRPS en Afrique de l'Ouest.
- Délais de publication en partie supposés.

## 10. Calendrier

Date limite de collecte : **2026-11-10 au matin**. Ce qui n'est pas prêt passe en extension.

## 11. Amendement du 2026-11-08 — analyses exploratoires, validé par l'utilisatrice le 2026-11-08

Les stocks certifiés ICE pourront être exportés plus tard depuis Bloomberg par l'utilisatrice. Ils sont une extension et n'entrent pas dans ces analyses.

Ces analyses sont ajoutées **après** les résultats principaux et la robustesse, qui ne montrent aucun signal. Elles sont exploratoires et ne remplacent pas la conclusion principale. Leurs règles sont fixées ici avant tout calcul. Les réglages des modèles et la validation chronologique restent ceux du point 4. Gradient Boosting seulement.

**A. Écart à la tendance, 60 et 120 séances.**
- D_t = log(P_t) − log(moyenne mobile de 120 séances de P_t), où P est le prix de `cacao_close`.
- Cibles : signe et valeur de D_{t+h} − D_t.
- Benchmark : régression linéaire de la cible sur D_t, estimée sur le passé de chaque pli.
- Lecture de contrôle : la cible sans sauts, avec les rendements des jours de passage mis à zéro.
- 4 comparaisons.

**B. Volatilité au-delà du HAR, 5, 20, 60 et 120 séances.**
- Benchmark : régression linéaire de `cible_vol_h` sur les volatilités passées à 5, 20 et 60 séances, estimée sur le passé de chaque pli.
- Modèle : les facteurs prévoient le résidu du HAR, et la prévision finale est HAR plus le résidu prévu.
- Mesures : RMSE (principale) et QLIKE.
- 4 comparaisons.

**C. Régime de volatilité et famille `investisseurs_biais`.**
- Régime haut à la séance t : volatilité réalisée sur 60 séances au-dessus du 80e centile de ses valeurs strictement passées.
- Perte au retrait de la famille, calculée séparément en régime haut et bas, sur les 9 cibles du point 1.
- Découpage 2010-2023 contre 2024-2026, montré à titre descriptif.
- 18 comparaisons.

**Correction pour tests multiples.** Bonferroni à l'intérieur de chaque bloc : intervalle de 98,75 % pour A et B (5 % divisés par 4), de 99,72 % pour C (5 % divisés par 18).

**Interdits (point 11).**
- Aucune série de stocks n'est disponible. Aucun résidu face aux stocks ne sera calculé avec des données inventées.
- Aucun réglage ne change après avoir vu ces résultats.

## 12. Module d'impact de la météo sur la production — règles fixées le 2026-11-08, avant calcul

Module demandé par l'utilisatrice le 2026-11-08. C'est une analyse exploratoire, hors de la question principale sur le prix.

**Constat préalable sur les données.** De 1991 à 2024, le **rendement** FAOSTAT est presque entièrement estimé par la FAO (code E) pour la Côte d'Ivoire (29 années sur 34), le Cameroun (29), le Ghana (17) et le Nigeria (15). En Côte d'Ivoire, il reste vers 500 kg/ha presque chaque année. La **production**, elle, est officielle (code A) dans la plupart des cas. La cible est donc la production, pas le rendement.

**Cible.** Logarithme de la production FAOSTAT, par pays et par an, pour les 9 pays, de 1991 à 2024.

**Météo.** Moyenne des points de chaque pays, pondérée par MapSPAM 2010.
- Pluie : total annuel CHIRPS, centré-réduit dans chaque pays sur 1991-2024, pour l'année N et l'année N−1 (l'année de récolte FAOSTAT ne coïncide pas avec la campagne), plus le carré de chacun, car un déficit comme un excès peuvent nuire.
- Température : moyenne annuelle de T2M_MAX de la NASA, centrée-réduite dans chaque pays, pour N et N−1. Elle n'est disponible que depuis 2005 : modèle séparé sur 2005-2024.

**Modèle.** Moindres carrés avec effets fixes pays, effets fixes année et tendance linéaire propre à chaque pays (expansion des surfaces).

**Inférence.**
- Erreurs regroupées par pays. Avec seulement 9 groupes, chaque coefficient de pluie est testé par **bootstrap sauvage par pays sous l'hypothèse nulle** (poids de Rademacher, les 512 combinaisons énumérées).
- Test global de la pluie par **permutation** : on mélange les années de la météo à l'intérieur de chaque pays, 2 000 tirages, et on compare le gain de R² intra-pays.
- Seuil de 5 %.

**Contrôles prévus.**
1. Placebo : la pluie de l'année N+1 ne doit pas expliquer la production de l'année N.
2. Observations officielles seulement (code A).
3. Sans l'Indonésie.
4. Sans les tendances par pays.

**Lecture.** La météo ne dépend pas de la production, ce qui permet une lecture causale prudente. Mais les données de production sont imparfaites, les poids MapSPAM sont fixes et il n'y a que 9 pays. Un résultat nul ne prouvera pas l'absence d'effet.

## 13. Régression des rendements cumulés — règles fixées le 2026-11-08, avant calcul

Analyse demandée par l'utilisatrice le 2026-11-08. Elle est exploratoire, car décidée après les résultats principaux.

**Cible.** Rendement simple futur R = (P(t+h) − P(t)) / P(t), avec h dans {1, 5, 20, 60, 120} séances et P = `cacao_close`.

**Modèle.** Gradient Boosting en régression, avec les réglages du point 4 et les variables de `construire(d, h)`. Validation annuelle de 2010 à 2026, purge de h séances.

**Benchmarks.**
- Marche aléatoire : rendement prévu nul, donc prix prévu égal à P(t).
- Moyenne passée : moyenne des rendements de l'entraînement de chaque pli.
- Le meilleur des deux sur 2010-2026 sert de référence.

**Mesures.**
- RMSE sur les **rendements** (principale). On ne juge pas sur le prix reconstruit, dont l'erreur est dominée par P(t).
- MAE et part de signes correctement prévus, en complément.

**Réussite.**
- Battre le benchmark sur 2010-2026 **et** en lecture de contrôle, avec un intervalle bootstrap à **99 %** qui exclut zéro (Bonferroni : 5 % divisés par 5 horizons), par blocs de max(20, h) séances.
- Lecture de contrôle : sans fenêtres de passage d'échéance jusqu'à 20 séances. À 60 et 120 séances, rendement recalculé avec les jours de saut mis à zéro.

**Affichage.** La courbe de prix prévu, P(t) × (1 + R̂), n'est tracée sur le site **que si** le benchmark est battu.
