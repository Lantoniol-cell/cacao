# Cacao : quels facteurs pèsent sur le prix ?

Projet individuel du cours de machine learning en finance (emlyon). Il cherche quelle famille de facteurs apporte le plus d'information pour prévoir le contrat à terme de cacao (CC=F), entre 2005 et 2026 : climat, géopolitique, biodiversité, coûts de production, production et offre, marché et finance, investisseurs et biais, demande et substituts.

**Réponse courte :** aucune famille ne bat un modèle sans facteurs, hors échantillon, pour le sens du prix comme pour son ampleur. Seule la volatilité est prévisible, et uniquement par son propre passé (modèle HAR).

## Site

Le site publié se trouve dans `docs/` (GitHub Pages). Ses sources Quarto sont dans `site/`. On y trouve un tableau de bord « Marché du jour », actualisé chaque soir, les données, les résultats, l'impact des familles, les pistes exploratoires, l'effet de la météo sur la production, ainsi que la méthode et les limites.

## Organisation

| Dossier ou fichier | Contenu |
|---|---|
| `protocole.md` | Règles d'analyse fixées avant les résultats, et leurs amendements datés |
| `carnet_de_bord.md` | Journal de chaque étape et journal d'utilisation de l'IA |
| `scripts/` | Collecte (01 à 32), modèles (30, 33, 37 à 39, 42 à 44), tableau de bord (40) |
| `src/cacao/` | Fonctions communes : grille, météo, variables, évaluation, marché, indicateurs |
| `tests/` | Tests, dont ceux qui vérifient qu'aucune donnée future n'est utilisée |
| `outputs/metriques/` | Résultats chiffrés |
| `config/` | Familles de variables et événements vérifiés |

Les données brutes, environ 8 Go, ne sont pas dans le dépôt. Les scripts de collecte permettent de les reconstruire.

## Reproduire

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Ensuite, lancer les scripts dans l'ordre de leur numéro, avec `PYTHONPATH=src`.

Analyse menée avec l'aide de Claude Code (Anthropic) : voir le journal d'utilisation de l'IA dans `carnet_de_bord.md`.
