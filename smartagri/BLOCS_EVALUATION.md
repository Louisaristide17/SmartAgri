# SmartAgri face à la grille d'évaluation « Développeur Data IA »

| Bloc | Où le voir dans le projet |
|---|---|
| 1. Données (/25) | `backend/ml/train_model.py` (collecte simulée, nettoyage, analyse), `ml/dataset_clean.csv`, `ml/figures/`, base SQLite (`models.py`, `seed.py`), référentiel `referentiel_ci.py` |
| 2. Modèle (/25) | `backend/ml/train_model.py` + `ml/metrics.json` + `ml/README.md` : régression, train/test, 3 algorithmes comparés, GridSearchCV, MAE/RMSE/MAPE/R², validation croisée |
| 3. Application (/30) | Web : `frontend/app` (HTML/CSS/JS) · API FastAPI (`backend/routers`) · CRUD parcelles · SQLite · tests `backend/tests` (`python -m pytest -v`) · déployé sur Render · Mobile : PWA `frontend/mobile` (GPS) + APK Flutter |
| 4. Agent IA (/25) | `backend/agent_tools.py` + `routers/agribot_router.py` : rôle défini, 4 outils (parcelles, prédictions, modèle ML, cultures de la zone), mémoire de conversation, garde-fous, tests |
| 5. Intégration IA (/25) | Le modèle ML alimente l'écran Prédiction (web, PWA, Flutter) ; AgriBot appelle ce même modèle ; repli sur la formule si le modèle est absent ; erreurs gérées |

## Limites assumées
- Données simulées (pas de jeu public ivoirien) : pipeline prêt pour de vraies données.
- Agent : choix d'outil par règles ; le mode LLM (OpenAI) n'est actif que si `OPENAI_API_KEY` est définie.
- SQLite est effacée à chaque redéploiement Render gratuit (la démo se recrée au démarrage).
- Pas de version Desktop (non requise : la grille propose Web, Mobile ou Desktop).
