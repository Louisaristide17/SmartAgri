# Pipeline Machine Learning SmartAgri

Lancer : `python ml/train_model.py` (≈ 1 min) → écrit `model.joblib`, `metrics.json`, `dataset_clean.csv`, `figures/`.

## Honnêteté sur les données
Il n'existe pas de jeu public de rendements parcelle par parcelle pour la Côte d'Ivoire.
Le jeu (6 000 observations) est donc **simulé** à partir du référentiel agronomique (`referentiel_ci.py`)
avec du bruit (météo, pratiques, mesure) et des défauts de collecte (manquants, doublons, capteur en panne).
Le modèle apprend donc ce référentiel : **à remplacer par des données réelles** (ANADER, CNRA, FAOSTAT, enquêtes).
La chaîne complète (nettoyage → entraînement → évaluation → API) est prête à les accueillir.

## Bloc 1 — Données
- Collecte : 6 060 lignes brutes (181 pluies et 123 températures manquantes, 60 doublons, 40 températures aberrantes).
- Nettoyage : doublons supprimés, valeurs > 40 °C invalidées, imputation par médiane de la zone → 6000 lignes.
- Stockage : CSV (`dataset_clean.csv`) + base SQL (SQLite) pour l'application.
- Analyse : rendement moyen par culture et par zone, corrélations ; figures dans `figures/`.

## Bloc 2 — Modèle
- Problème : **régression** (prédire le rendement en t/ha).
- Variables : culture, sol, zone, pluviométrie, température, engrais. Séparation train 80 % (4800) / test 20 % (1200).
- Cible passée en logarithme (les rendements vont de 0,1 à plus de 15 t/ha : l'erreur relative compte).
- Comparaison puis réglage (GridSearchCV, 3 plis) :

| Modèle | MAE (t/ha) | RMSE | Erreur relative | R² |
|---|---|---|---|---|
| Régression linéaire | 0.78 | 1.89 | 55.0 % | 0.632 |
| Random Forest | 0.23 | 0.49 | 11.5 % | 0.976 |
| Gradient Boosting | 0.37 | 0.81 | 28.4 % | 0.933 |
| Gradient Boosting réglé | 0.20 | 0.45 | 10.0 % | 0.979 |

- Retenu : **Gradient Boosting réglé**, validation croisée 5 plis R² = 0.981 ± 0.001.
- Utilisation sur nouvelles données : `routers/prediction_router.py` charge `model.joblib`
  (la formule agronomique sert de secours si le modèle est indisponible).

## Limite à connaître
Un R² élevé mesure la capacité à retrouver le référentiel simulé, pas à prédire le rendement réel d'un champ.

## Source de données réelle : FAOSTAT
`ml/data/faostat_ci_utilisation_terres.csv` (FAO, domaine *Utilisation des terres*, Côte d'Ivoire, 2020-2025) donne le
contexte réel : ~26 millions d'ha de terres agricoles, ~13 millions en culture dont ~8,5 millions en cultures permanentes
(cacao, café, hévéa…), forêts en recul (4,18 → 3,77 M ha entre 2020 et 2025), seulement 0,5 % des terres en culture irriguées.
`python ml/faostat_contexte.py` régénère `faostat_contexte.json` et `figures/faostat_terres.png`.
**Limite assumée :** ce jeu ne contient pas de rendements par culture ; les rendements d'entraînement restent simulés.
