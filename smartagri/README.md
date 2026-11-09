# 🌱 SmartAgri — Plateforme Agricole Intelligente

> **Projet de soutenance — Formation SIMPLON 2026**

SmartAgri est une application web complète qui aide les agriculteurs d'Afrique de l'Ouest à prédire leurs rendements, gérer leurs parcelles, consulter la météo et interagir avec un assistant IA (AgriBot).

---

## Structure du projet

```
smartagri/
├── backend/                    ← API FastAPI
│   ├── main.py                 ← Point d'entrée
│   ├── database.py             ← Configuration SQLAlchemy
│   ├── models.py               ← Tables (User, Parcelle, Prediction, Conversation)
│   ├── schemas.py              ← Validation Pydantic
│   ├── auth.py                 ← JWT + hashage bcrypt
│   ├── requirements.txt
│   ├── .env.example            ← Variables d'environnement
│   └── routers/
│       ├── auth_router.py      ← POST /register, /login, GET /me
│       ├── parcelles_router.py ← CRUD /parcelles
│       ├── prediction_router.py← POST /prediction, GET /historique
│       ├── meteo_router.py     ← GET /meteo/{ville}
│       └── agribot_router.py   ← POST /agribot/message
│
└── frontend/
    ├── login/                  ← Page de connexion
    │   ├── index.html          ← Connexion / Inscription / Mot de passe oublié
    │   ├── style.css
    │   └── script.js
    └── app/
        ├── pages/
        │   ├── dashboard.html  ← Tableau de bord
        │   ├── parcelles.html  ← CRUD parcelles
        │   ├── prediction.html ← Prédiction IA avec sliders
        │   ├── agribot.html    ← Chat IA
        │   └── meteo.html      ← Météo et conseils
        └── assets/
            ├── css/app.css     ← CSS global partagé
            └── js/api.js       ← Client API + helpers JS
```

---

## Démarrage rapide

### 1. Backend (FastAPI)

```bash
# Aller dans le dossier backend
cd smartagri/backend

# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
copy .env.example .env
# Éditez .env selon vos besoins

# Lancer le serveur
uvicorn main:app --reload --port 8000
```

Le serveur démarre sur **http://localhost:8000**
- Documentation Swagger : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

### 2. Frontend

Ouvrez simplement `frontend/login/index.html` dans votre navigateur.

> ⚠️ Le backend doit être lancé pour que l'application soit fonctionnelle.

---

## Compte de démonstration

| Champ    | Valeur               |
|----------|----------------------|
| Email    | demo@smartagri.com   |
| Mot de passe | Demo1234!        |

Créé automatiquement au premier démarrage du backend.

---

## Technologies utilisées

### Backend
| Technologie | Rôle |
|-------------|------|
| **FastAPI** | Framework API REST |
| **SQLAlchemy** | ORM base de données |
| **SQLite** | BDD développement (→ PostgreSQL prod) |
| **python-jose** | Tokens JWT |
| **passlib[bcrypt]** | Hashage des mots de passe |
| **pydantic** | Validation des données |
| **httpx** | Appels API OpenWeatherMap |
| **openai** | AgriBot GPT (optionnel) |

### Frontend
| Technologie | Rôle |
|-------------|------|
| **HTML5 / CSS3** | Structure et style |
| **JavaScript ES6+** | Interactivité |
| **Google Fonts (Inter)** | Typographie |
| **CSS custom properties** | Thème cohérent |

---

## Endpoints API

### Authentification
```
POST   /api/auth/register   → Créer un compte
POST   /api/auth/login      → Se connecter (JWT)
GET    /api/auth/me         → Mon profil
```

### Parcelles
```
GET    /api/parcelles/          → Liste mes parcelles
POST   /api/parcelles/          → Créer une parcelle
GET    /api/parcelles/{id}      → Détail
PUT    /api/parcelles/{id}      → Modifier
DELETE /api/parcelles/{id}      → Supprimer
```

### Prédiction
```
POST   /api/prediction/         → Prédire le rendement
GET    /api/prediction/historique → Historique
```

### Météo
```
GET    /api/meteo/{ville}               → Météo actuelle
GET    /api/meteo/{ville}/previsions    → Prévisions 6 jours
```

### AgriBot
```
POST   /api/agribot/message     → Envoyer un message
GET    /api/agribot/historique  → Historique conversation
DELETE /api/agribot/historique  → Effacer
```

---

## ⚙️ Variables d'environnement (.env)

```env
DATABASE_URL=sqlite:///./smartagri.db
SECRET_KEY=votre-clé-secrète-très-longue
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPENWEATHER_API_KEY=votre_clé_owm      # https://openweathermap.org/api
OPENAI_API_KEY=votre_clé_openai        # Optionnel pour AgriBot GPT
```

---

## Fonctionnalités

- ✅ **Authentification JWT** — inscription, connexion, token sécurisé
- ✅ **Gestion des parcelles** — CRUD complet avec filtres et recherche
- ✅ **Prédiction IA** — modèle agronomique avec sliders interactifs
- ✅ **Météo** — données temps réel + prévisions 6 jours + conseils
- ✅ **AgriBot** — assistant IA avec mémoire conversationnelle
- ✅ **Dashboard** — statistiques, graphiques, activité récente
- ✅ **Responsive** — adapté mobile et tablette
- ✅ **Mode démo** — fonctionne sans API externe

---

## Auteur

Projet de soutenance — Formation IA / Développement Web, SIMPLON 2026

---

*SmartAgri — L'agriculture intelligente commence ici* 🌱
